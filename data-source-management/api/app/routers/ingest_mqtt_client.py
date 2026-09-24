import asyncio
import logging
from types import SimpleNamespace

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from sqlmodel import Session

from auth import OIDCError
from dependencies import authenticate_token, engine
from repositories.ingest_mqtt import IngestMqttRepository
from services.mqtt_inspect import MqttSubscriber

logger = logging.getLogger("app.mqtt_client")

router = APIRouter(prefix="/ingest/mqtt", tags=["ingest/mqtt"])

AUTH_TIMEOUT_SECONDS = 10
QUEUE_MAX = 1000
# Soft cap on concurrent live sessions to avoid runaway broker connections.
MAX_SESSIONS = 100
_active_sessions = 0


def _authorize(token: str, ingest_id: int) -> SimpleNamespace:
    """Blocking auth + authorization; returns the fields the subscriber needs.

    Runs in a worker thread (see ``live``) so it never blocks the event loop.
    Raises OIDCError / HTTPException on auth or lookup failure. The SQLModel
    ``Session`` is opened, used and closed entirely within this single thread.
    """
    with Session(engine) as session:
        user = authenticate_token(token, session)
        entity = IngestMqttRepository(session).find_one(
            ingest_id, access_scope=user.access_scope
        )
        return SimpleNamespace(
            username=entity.username, password=entity.password, topic=entity.topic
        )


@router.websocket("/{id}/live")
async def live(websocket: WebSocket, id: int):
    """Live MQTT inspection: stream messages for one ingest and publish test messages.

    Protocol (JSON):
      client -> server: {"action": "auth", "token": "<access token>"}   (must be first)
                        {"action": "publish", "topic_suffix", "payload"}
      server -> client: {"type": "connected", "topic"}
                        {"type": "message", "topic", "payload", "received_at"}
                        {"type": "published", "topic"}
                        {"type": "dropped", "count"}
                        {"type": "error", "detail"}
    """
    global _active_sessions
    await websocket.accept()

    # 1) first frame must authenticate
    try:
        first = await asyncio.wait_for(
            websocket.receive_json(), timeout=AUTH_TIMEOUT_SECONDS
        )
    except (asyncio.TimeoutError, WebSocketDisconnect, ValueError):
        await websocket.close(code=1008)
        return
    if (
        not isinstance(first, dict)
        or first.get("action") != "auth"
        or not first.get("token")
    ):
        await websocket.send_json(
            {"type": "error", "detail": "Authentication required."}
        )
        await websocket.close(code=1008)
        return

    # 2) authenticate + authorize off the event loop (DB + OIDC are blocking)
    try:
        ent = await asyncio.to_thread(_authorize, first["token"], id)
    except OIDCError:
        await websocket.close(code=1008)
        return
    except HTTPException as exc:
        if exc.status_code == 404:
            await websocket.send_json({"type": "error", "detail": "Ingest not found."})
        await websocket.close(code=1008)
        return
    except Exception:
        logger.exception("MQTT live: authorization error")
        await websocket.close(code=1011)
        return

    if _active_sessions >= MAX_SESSIONS:
        await websocket.send_json(
            {"type": "error", "detail": "Too many active MQTT sessions, try later."}
        )
        await websocket.close(code=1013)
        return

    # 3) start the dedicated subscriber and pump messages
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue(maxsize=QUEUE_MAX)
    sub = MqttSubscriber(
        username=ent.username,
        password=ent.password,
        topic=ent.topic,
        loop=loop,
        queue=queue,
    )
    try:
        await asyncio.to_thread(sub.start)
    except Exception:
        logger.exception("MQTT live: failed to connect subscriber")
        await websocket.send_json(
            {"type": "error", "detail": "Failed to connect to the MQTT broker."}
        )
        await websocket.close(code=1011)
        return

    _active_sessions += 1
    await websocket.send_json({"type": "connected", "topic": f"{ent.topic}/#"})

    async def forward():
        last_dropped = 0
        while True:
            item = await queue.get()
            if sub.dropped != last_dropped:
                last_dropped = sub.dropped
                await websocket.send_json({"type": "dropped", "count": sub.dropped})
            await websocket.send_json(item)

    async def receive():
        while True:
            data = await websocket.receive_json()
            if isinstance(data, dict) and data.get("action") == "publish":
                try:
                    topic = sub.publish(
                        data.get("topic_suffix", ""),
                        str(data.get("payload", "")),
                    )
                    await websocket.send_json({"type": "published", "topic": topic})
                except Exception:
                    await websocket.send_json(
                        {"type": "error", "detail": "Publish failed."}
                    )

    fwd = asyncio.create_task(forward())
    rcv = asyncio.create_task(receive())
    try:
        await asyncio.wait({fwd, rcv}, return_when=asyncio.FIRST_COMPLETED)
    finally:
        fwd.cancel()
        rcv.cancel()
        sub.stop()
        _active_sessions -= 1
        logger.debug("MQTT live session closed for ingest_id=%s", id)
