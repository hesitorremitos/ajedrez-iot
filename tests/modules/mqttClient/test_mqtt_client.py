"""Tests for MqttClient module with mocked umqtt.robust."""

import asyncio
import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = ROOT / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))


class MockRobustClient:
    """Mock for umqtt.robust.MQTTClient."""

    lastInstance = None

    def __init__(self, client_id, server, port, user=None, password=None, keepalive=0, ssl=None):
        self.client_id = client_id
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.keepalive = keepalive
        self._callback = None
        self.connectCalled = False
        self.disconnectCalled = False
        self.published = None
        self.subscribed = None
        MockRobustClient.lastInstance = self

    def set_callback(self, callback):
        self._callback = callback

    def connect(self):
        self.connectCalled = True

    def disconnect(self):
        self.disconnectCalled = True

    def publish(self, topic, msg, retain=False, qos=0):
        self.published = (topic, msg, retain, qos)

    def subscribe(self, topic, qos=0):
        self.subscribed = (topic, qos)

    def check_msg(self):
        pass

    def simulateMessage(self, topic, msg):
        if self._callback:
            self._callback(topic, msg)


def _run(coro):
    return asyncio.run(coro)


def _loadMqttClientClass(monkeypatch):
    for name in list(sys.modules):
        if name.startswith("modules.mqttClient"):
            del sys.modules[name]

    monkeypatch.setitem(
        sys.modules,
        "umqtt.robust",
        SimpleNamespace(MQTTClient=MockRobustClient),
    )

    mqtt_module = importlib.import_module("modules.mqttClient.MqttClient")
    monkeypatch.setattr(mqtt_module, "_RobustClient", MockRobustClient)
    return mqtt_module.MqttClient


@pytest.fixture
def MqttClientClass(monkeypatch):
    return _loadMqttClientClass(monkeypatch)


@pytest.fixture
def client(MqttClientClass):
    return MqttClientClass(debug=False)


def test_connect_returns_true_and_starts_poll(client):
    ok = _run(client.connect("192.168.1.10", clientId="tablero-01"))
    assert ok is True
    assert client.isConnected() is True
    assert MockRobustClient.lastInstance.connectCalled is True
    _run(client.disconnect())


def test_connect_invokes_onConnect(client):
    connectEvents = []

    async def onConnect():
        connectEvents.append(True)
        await client.subscribe("adapt/tablero-01/cmd")

    client.onConnect = onConnect
    _run(client.connect("192.168.1.10", clientId="tablero-01"))

    assert connectEvents == [True]
    assert MockRobustClient.lastInstance.subscribed[0] == b"adapt/tablero-01/cmd"
    _run(client.disconnect())


def test_publish_serializes_dict(client):
    _run(client.connect("192.168.1.10"))
    payload = {"fen": "startpos", "turno": "w"}
    ok = _run(client.publish("adapt/tablero-01/state", payload, retain=True))

    assert ok is True
    topic, msg, retain, qos = MockRobustClient.lastInstance.published
    assert topic == b"adapt/tablero-01/state"
    assert json.loads(msg.decode()) == payload
    assert retain is True
    assert qos == 0
    _run(client.disconnect())


def test_publish_returns_false_when_not_connected(client):
    ok = _run(client.publish("adapt/tablero-01/state", {"fen": "x"}))
    assert ok is False


def test_onMessage_receives_parsed_json(client):
    received = []

    def onMessage(topic, payload):
        received.append((topic, payload))

    client.onMessage = onMessage
    _run(client.connect("192.168.1.10"))

    MockRobustClient.lastInstance.simulateMessage(
        b"adapt/tablero-01/cmd",
        b'{"tipo": "finalizar_partida"}',
    )

    assert received == [("adapt/tablero-01/cmd", {"tipo": "finalizar_partida"})]
    _run(client.disconnect())


def test_disconnect_returns_true(client):
    _run(client.connect("192.168.1.10"))
    ok = _run(client.disconnect())
    assert ok is True
    assert client.isConnected() is False
    assert MockRobustClient.lastInstance.disconnectCalled is True


def test_connect_returns_false_when_robust_missing(monkeypatch):
    for name in list(sys.modules):
        if name.startswith("modules.mqttClient"):
            del sys.modules[name]

    monkeypatch.setitem(
        sys.modules,
        "umqtt.robust",
        SimpleNamespace(MQTTClient=MockRobustClient),
    )

    mqtt_module = importlib.import_module("modules.mqttClient.MqttClient")
    monkeypatch.setattr(mqtt_module, "_RobustClient", None)
    client = mqtt_module.MqttClient()
    ok = _run(client.connect("192.168.1.10"))
    assert ok is False
