"""
Example: MQTT coordinator with WiFi.sta, Chess, ChessClock and event queue.

Publishes board state to MQTT and handles remote commands (nueva_partida,
finalizar_partida). SSE is not used here; see main.py for SSE demo.

Configure BROKER_HOST, WIFI_SSID and WIFI_PASSWORD before deploy.
"""

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from modules.chess import Chess
from modules.chessclock import ChessClock
from modules.mqttClient import MqttClient, buildStatePayload
from modules.network import WiFi

DEVICE_ID = "tablero-01"
BROKER_HOST = "192.168.1.10"
BROKER_PORT = 1883
WIFI_SSID = "MiRed"
WIFI_PASSWORD = "clave123"

STATE_TOPIC = "adapt/{}/state".format(DEVICE_ID)
EVENTS_TOPIC = "adapt/{}/events".format(DEVICE_ID)
CMD_TOPIC = "adapt/{}/cmd".format(DEVICE_ID)

EVENTS = asyncio.Queue(32)

wifi = WiFi(debug=True)
mqtt = MqttClient(debug=True)
chess = Chess()
whiteClock = ChessClock()
blackClock = ChessClock()

GAME = {
    "active": False,
    "lastMove": "",
    "pgn": "",
    "nombresBlancas": "",
    "nombresNegras": "",
    "sensores": 0,
}


def _gameStateExtra():
    return {
        "move": GAME["lastMove"],
        "pgn": GAME["pgn"],
        "sensores": GAME["sensores"],
        "nombresBlancas": GAME["nombresBlancas"],
        "nombresNegras": GAME["nombresNegras"],
    }


async def publishState(retain=True, alsoEvent=False):
    if not mqtt.isConnected():
        return
    payload = buildStatePayload(chess, whiteClock, blackClock, _gameStateExtra())
    await mqtt.publish(STATE_TOPIC, payload, retain=retain)
    if alsoEvent:
        await mqtt.publish(EVENTS_TOPIC, payload)


def onChessMove(moveStr, captured, isPromotion, isCastling, isEnPassant):
    GAME["lastMove"] = moveStr
    asyncio.create_task(publishState(retain=True, alsoEvent=True))


async def onMqttConnect():
    await mqtt.subscribe(CMD_TOPIC)


def onMqttMessage(topic, payload):
    asyncio.create_task(EVENTS.put(("mqtt_cmd", payload)))


def onStaConnect(ip):
    asyncio.create_task(
        mqtt.connect(host=BROKER_HOST, port=BROKER_PORT, clientId=DEVICE_ID)
    )


def onStaDisconnect():
    asyncio.create_task(mqtt.disconnect())


mqtt.onConnect = onMqttConnect
mqtt.onMessage = onMqttMessage
wifi.sta.onConnect = onStaConnect
wifi.sta.onDisconnect = onStaDisconnect
chess.onMove = onChessMove


async def handleMqttCmd(payload):
    if not isinstance(payload, dict):
        return
    tipo = payload.get("tipo")
    if tipo == "nueva_partida":
        chess.reset()
        whiteClock.reset(600000)
        blackClock.reset(600000)
        whiteClock.start()
        GAME["active"] = True
        GAME["lastMove"] = ""
        GAME["pgn"] = ""
        GAME["nombresBlancas"] = payload.get("nombresBlancas", "")
        GAME["nombresNegras"] = payload.get("nombresNegras", "")
        await publishState(retain=True, alsoEvent=True)
    elif tipo == "finalizar_partida":
        whiteClock.pause()
        blackClock.pause()
        GAME["active"] = False
        await publishState(retain=True, alsoEvent=True)


async def coordinator():
    while True:
        evt, data = await EVENTS.get()
        if evt == "mqtt_cmd":
            await handleMqttCmd(data)


async def main():
    asyncio.create_task(coordinator())
    await wifi.sta.start(ssid=WIFI_SSID, password=WIFI_PASSWORD)
    while True:
        await asyncio.sleep(3600)


try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
