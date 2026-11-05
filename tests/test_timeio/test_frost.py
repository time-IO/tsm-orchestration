#!/usr/bin/env python3
import os
from unittest import mock

import pytest
import requests
from cryptography.fernet import Fernet
from timeio import frost
from timeio.crypto import encrypt

SCHEMA = "myproject"
PASSWORD = "s3cret"
TOKEN = "tok3n"
DB_URL = "postgresql://u:pw@db.example.org:5432/postgres?sslmode=require"


@pytest.fixture(scope="module", autouse=True)
def create_secret():
    """Create a new Fernet key, see test_crypto.py for the reasoning."""
    os.environ["FERNET_ENCRYPTION_SECRET"] = Fernet.generate_key().decode()


def push(api_url="http://frost:8081/"):
    frost.push_context(
        api_url,
        TOKEN,
        schema=SCHEMA,
        user="sta_ro_myproject",
        password=encrypt(PASSWORD, os.environ["FERNET_ENCRYPTION_SECRET"]),
        db_url=DB_URL,
    )


def test_push_context_request():
    with mock.patch("timeio.frost.requests.put") as put:
        push()

    put.assert_called_once()
    args, kwargs = put.call_args
    assert args == (f"http://frost:8081/contexts/{SCHEMA}",)
    assert kwargs["data"] == {
        "user": "sta_ro_myproject",
        "password": PASSWORD,
        "url": "postgresql://db.example.org:5432/postgres",
    }
    assert kwargs["headers"]["Authorization"] == f"Bearer {TOKEN}"
    assert kwargs["timeout"]


def test_push_context_raises_on_http_error():
    with mock.patch("timeio.frost.requests.put") as put:
        put.return_value.raise_for_status.side_effect = requests.HTTPError("401")
        with pytest.raises(requests.HTTPError):
            push()


class TestSetupFrostHandler:
    @pytest.fixture
    def handler(self, monkeypatch):
        import setup_frost

        env = {
            "TOPIC": "t",
            "MQTT_BROKER": "b:1883",
            "MQTT_USER": "u",
            "MQTT_PASSWORD": "p",
            "MQTT_CLIENT_ID": "c",
            "MQTT_QOS": "1",
            "MQTT_CLEAN_SESSION": "false",
            "DSMDB_DSN": "dsn",
            "FROST_CONTEXT_API_URL": "http://frost:8081",
            "FROST_INTERNAL_CONTEXT_API_URL": "http://frost-internal:8081",
            "FROST_CONTEXT_API_TOKEN": TOKEN,
        }
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        with mock.patch("timeio.mqtt.AbstractHandler.__init__", return_value=None):
            h = setup_frost.CreateFrostInstanceHandler()
        thing = mock.Mock()
        thing.database.schema = SCHEMA
        thing.database.ro_username = "RO_myproject"
        thing.database.ro_password = encrypt(
            PASSWORD, os.environ["FERNET_ENCRYPTION_SECRET"]
        )
        thing.database.ro_url = DB_URL
        monkeypatch.setattr(setup_frost.Thing, "from_uuid", lambda *a, **k: thing)
        return h

    def act(self, handler):
        handler.act({"thing": "uuid"}, mock.Mock())

    def test_pushes_both_variants(self, handler):
        with mock.patch("timeio.frost.requests.put") as put:
            self.act(handler)

        urls = [c.args[0] for c in put.call_args_list]
        assert urls == [
            f"http://frost:8081/contexts/{SCHEMA}",
            f"http://frost-internal:8081/contexts/{SCHEMA}",
        ]
        users = [c.kwargs["data"]["user"] for c in put.call_args_list]
        assert users == ["sta_ro_myproject", "sti_ro_myproject"]

    @pytest.mark.parametrize("failing", [0, 1])
    def test_attempts_both_and_raises_if_one_fails(self, handler, failing):
        calls = []

        def put(url, **kwargs):
            calls.append(url)
            if len(calls) - 1 == failing:
                raise requests.ConnectionError("down")
            return mock.Mock()

        with mock.patch("timeio.frost.requests.put", side_effect=put):
            with pytest.raises(RuntimeError, match="FROST context push failed"):
                self.act(handler)
        assert len(calls) == 2
