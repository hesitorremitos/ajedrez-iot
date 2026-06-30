"""
MQTT client transport for ESP32 (MicroPython).

Wraps umqtt.robust with async poll loop and JSON helpers.
Does not interpret chess commands; the coordinator handles payloads.
"""

try:
    import ujson as json
except ImportError:
    import json

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

try:
    from umqtt.robust import MQTTClient as _RobustClient
except ImportError:
    _RobustClient = None


class MqttClient:
    """Async-friendly MQTT transport with publish/subscribe and callbacks."""

    def __init__(self, debug=False):
        self._debug = debug
        self._client = None
        self._connected = False
        self._pollTask = None
        self._host = None
        self._port = 1883
        self._clientId = b"esp32"
        self._user = None
        self._password = None
        self._keepalive = 60
        self._onMessage = None
        self._onConnect = None
        self._onDisconnect = None

    @property
    def onMessage(self):
        return self._onMessage

    @onMessage.setter
    def onMessage(self, callback):
        self._onMessage = callback

    @property
    def onConnect(self):
        return self._onConnect

    @onConnect.setter
    def onConnect(self, callback):
        self._onConnect = callback

    @property
    def onDisconnect(self):
        return self._onDisconnect

    @onDisconnect.setter
    def onDisconnect(self, callback):
        self._onDisconnect = callback

    def _log(self, message):
        if self._debug:
            print("[MqttClient Debug] {}".format(message))

    async def _sleepMs(self, ms):
        if hasattr(asyncio, "sleep_ms"):
            await asyncio.sleep_ms(ms)
        else:
            await asyncio.sleep(ms / 1000)

    async def _runCallback(self, callback):
        if not callback:
            return
        try:
            result = callback()
            if result is not None and hasattr(result, "__await__"):
                await result
        except Exception as exc:
            self._log("callback failed: {}".format(exc))

    def _handleRawMessage(self, topic, msg):
        if isinstance(topic, bytes):
            topic = topic.decode()
        if isinstance(msg, bytes):
            text = msg.decode()
        else:
            text = msg
        try:
            payload = json.loads(text)
        except (ValueError, TypeError):
            payload = text
        if self._onMessage:
            try:
                self._onMessage(topic, payload)
            except Exception as exc:
                self._log("onMessage failed: {}".format(exc))

    async def _pollLoop(self):
        while True:
            if self._connected and self._client is not None:
                try:
                    self._client.check_msg()
                except OSError as exc:
                    self._log("poll OSError: {}".format(exc))
                    await self._markDisconnected()
            await self._sleepMs(100)

    async def _markDisconnected(self):
        if not self._connected:
            return
        self._connected = False
        await self._runCallback(self._onDisconnect)

    async def connect(
        self,
        host,
        port=1883,
        clientId=None,
        user=None,
        password=None,
        keepalive=60,
    ):
        """
        Connect to MQTT broker and start message poll task.

        Returns:
            bool: True if successful, False on error
        """
        if _RobustClient is None:
            self._log("umqtt.robust not available")
            return False

        try:
            self._host = host
            self._port = port
            self._user = user
            self._password = password
            self._keepalive = keepalive

            if clientId is None:
                self._clientId = b"esp32"
            elif isinstance(clientId, str):
                self._clientId = clientId.encode()
            else:
                self._clientId = clientId

            self._client = _RobustClient(
                self._clientId,
                host,
                port,
                user,
                password,
                keepalive,
            )
            self._client.set_callback(self._handleRawMessage)
            self._client.connect()
            self._connected = True

            if self._pollTask is None:
                self._pollTask = asyncio.create_task(self._pollLoop())

            await self._runCallback(self._onConnect)
            self._log("connected to {}:{}".format(host, port))
            return True

        except Exception as exc:
            self._log("connect failed: {}".format(exc))
            self._client = None
            self._connected = False
            return False

    async def disconnect(self):
        """
        Disconnect from broker and stop polling.

        Returns:
            bool: True if successful or already disconnected, False on error
        """
        try:
            wasConnected = self._connected
            self._connected = False

            if self._pollTask is not None:
                self._pollTask.cancel()
                try:
                    await self._pollTask
                except asyncio.CancelledError:
                    pass
                self._pollTask = None

            if self._client is not None:
                try:
                    self._client.disconnect()
                except OSError:
                    pass
                self._client = None

            if wasConnected:
                await self._runCallback(self._onDisconnect)

            self._log("disconnected")
            return True

        except Exception as exc:
            self._log("disconnect failed: {}".format(exc))
            return False

    def isConnected(self):
        """
        Check if client is connected to broker.

        Returns:
            bool
        """
        return self._connected and self._client is not None

    def _encodePayload(self, payload):
        if isinstance(payload, dict):
            return json.dumps(payload).encode()
        if isinstance(payload, str):
            return payload.encode()
        return payload

    def _encodeTopic(self, topic):
        if isinstance(topic, str):
            return topic.encode()
        return topic

    async def publish(self, topic, payload, qos=0, retain=False):
        """
        Publish message to topic.

        Args:
            topic: str or bytes
            payload: dict (serialized with ujson), str, or bytes
            qos: 0 or 1
            retain: bool

        Returns:
            bool: True if successful, False on error or not connected
        """
        if not self.isConnected():
            return False

        try:
            topicBytes = self._encodeTopic(topic)
            msgBytes = self._encodePayload(payload)
            self._client.publish(topicBytes, msgBytes, retain, qos)
            return True
        except OSError as exc:
            self._log("publish failed: {}".format(exc))
            await self._markDisconnected()
            return False
        except Exception as exc:
            self._log("publish failed: {}".format(exc))
            return False

    async def subscribe(self, topic, qos=0):
        """
        Subscribe to topic.

        Returns:
            bool: True if successful, False on error or not connected
        """
        if not self.isConnected():
            return False

        try:
            topicBytes = self._encodeTopic(topic)
            self._client.subscribe(topicBytes, qos)
            self._log("subscribed to {}".format(topic))
            return True
        except OSError as exc:
            self._log("subscribe failed: {}".format(exc))
            await self._markDisconnected()
            return False
        except Exception as exc:
            self._log("subscribe failed: {}".format(exc))
            return False
