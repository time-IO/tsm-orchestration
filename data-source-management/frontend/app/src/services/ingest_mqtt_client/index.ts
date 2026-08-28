import type { MqttLiveHandlers } from 'src/services/ingest_mqtt_client/types';

type ServerFrame = {
  type?: string;
  topic?: string;
  payload?: string;
  received_at?: string;
  detail?: string;
  count?: number;
};

function buildWsUrl(id: number): string {
  const base = (process.env.API_BASE_URL || '').replace(/\/$/, '');
  // http(s):// -> ws(s)://
  const wsBase = base.replace(/^http/, 'ws');
  return `${wsBase}/ingest/mqtt/${id}/live`;
}

/**
 * Live WebSocket connection to an MQTT ingest's broker subscription.
 *
 * The browser cannot set an Authorization header on a WebSocket, so the access
 * token is sent as the first message (`{action: 'auth', token}`) instead.
 */
export class MqttLiveConnection {
  private ws: WebSocket | null = null;

  constructor(
    private readonly id: number,
    private readonly token: string,
    private readonly handlers: MqttLiveHandlers,
  ) {}

  connect(): void {
    const ws = new WebSocket(buildWsUrl(this.id));
    this.ws = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ action: 'auth', token: this.token }));
      this.handlers.onOpen?.();
    };

    ws.onmessage = (event: MessageEvent) => {
      let frame: ServerFrame;
      try {
        frame = JSON.parse(event.data as string) as ServerFrame;
      } catch {
        return;
      }
      switch (frame.type) {
        case 'connected':
          this.handlers.onConnected?.(frame.topic ?? '');
          break;
        case 'message':
          this.handlers.onMessage?.({
            topic: frame.topic ?? '',
            payload: frame.payload ?? '',
            received_at: frame.received_at ?? '',
          });
          break;
        case 'published':
          this.handlers.onPublished?.(frame.topic ?? '');
          break;
        case 'dropped':
          this.handlers.onDropped?.(frame.count ?? 0);
          break;
        case 'error':
          this.handlers.onError?.(frame.detail ?? 'Unknown error');
          break;
      }
    };

    ws.onerror = () => this.handlers.onError?.('WebSocket connection error');
    ws.onclose = () => this.handlers.onClose?.();
  }

  publish(topicSuffix: string, payload: string): void {
    this.ws?.send(JSON.stringify({ action: 'publish', topic_suffix: topicSuffix, payload }));
  }

  close(): void {
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.close();
      this.ws = null;
    }
  }
}
