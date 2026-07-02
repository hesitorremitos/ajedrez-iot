"""
Firmware tablero IoT (ESP32).
REPL: startGame(), play("e2-e4"), sync(), endGame(), status().
"""

import _thread

import uasyncio as asyncio
import ujson as json
from umqtt.robust import MQTTClient

from modules.chess import Chess
from modules.chessclock import ChessClock
from modules.chessdisplay import ChessDisplay
from modules.network import WiFi

# Configuracion

MQTT_TOPIC = "ajedrez"
WIFI_SSID = "root"
WIFI_PASSWORD = "@11235813"
BROKER_HOST = "mqtt.inginformatica.dev"
BROKER_PORT = 1883
BROKER_USER = None
BROKER_PASSWORD = None
DEFAULT_MINUTES = 10

DISPLAY_ENABLED = True
DISPLAY_SDA = 21
DISPLAY_SCL = 22
DISPLAY_ADDR = 0x3C

# Variables globales

wifi = WiFi(debug=False)
chess = Chess()
whiteClock = ChessClock()
blackClock = ChessClock()

nombresBlancas = ""
nombresNegras = ""
gameActive = False

display = None
if DISPLAY_ENABLED:
    try:
        display = ChessDisplay(DISPLAY_SDA, DISPLAY_SCL, address=DISPLAY_ADDR)
    except Exception as err:
        print("Display no disponible:", err)
        display = None


def _getTurnCount():
    parts = chess.getFen().split()
    if len(parts) > 5:
        return int(parts[5])
    return 1


def _sidePanelActiveColor():
    turn = chess.getTurn()
    if turn in ("w", "b"):
        return turn
    return "w"


def refreshDisplay(fullBoard=True):
    if display is None:
        return
    if fullBoard:
        display.renderBoard(chess.getBoard())
    display.renderSidePanel(
        whiteClock.getText(),
        blackClock.getText(),
        _sidePanelActiveColor(),
        _getTurnCount(),
    )


def switchClock():
    if chess.getTurn() == "w":
        blackClock.pause()
        whiteClock.resume()
    else:
        whiteClock.pause()
        blackClock.resume()


def startGame(minutes=DEFAULT_MINUTES, blancas="", negras=""):
    global nombresBlancas, nombresNegras, gameActive
    ms = int(minutes) * 60000
    chess.reset()
    whiteClock.reset(ms)
    blackClock.reset(ms)
    whiteClock.start()
    nombresBlancas = blancas
    nombresNegras = negras
    gameActive = True
    data = {
        "fen": chess.getFen(),
        "turno": chess.getTurn(),
        "tiempoW": whiteClock.getText(),
        "tiempoB": blackClock.getText(),
        "active": gameActive,
        "nombresBlancas": nombresBlancas,
        "nombresNegras": nombresNegras,
    }
    mqtt.publish(MQTT_TOPIC, json.dumps(data), retain=True)
    refreshDisplay()
    return True


def play(move):
    if not gameActive:
        return False
    if not chess.play(move):
        return False
    switchClock()
    data = {
        "fen": chess.getFen(),
        "turno": chess.getTurn(),
        "tiempoW": whiteClock.getText(),
        "tiempoB": blackClock.getText(),
        "active": gameActive,
        "move": move,
        "nombresBlancas": nombresBlancas,
        "nombresNegras": nombresNegras,
    }
    mqtt.publish(MQTT_TOPIC, json.dumps(data), retain=True)
    refreshDisplay()
    return True


def endGame():
    global gameActive
    if not gameActive:
        return False
    whiteClock.pause()
    blackClock.pause()
    gameActive = False
    data = {
        "fen": chess.getFen(),
        "turno": chess.getTurn(),
        "tiempoW": whiteClock.getText(),
        "tiempoB": blackClock.getText(),
        "active": gameActive,
        "nombresBlancas": nombresBlancas,
        "nombresNegras": nombresNegras,
    }
    mqtt.publish(MQTT_TOPIC, json.dumps(data), retain=True)
    refreshDisplay()
    return True


def sync():
    if not gameActive:
        return False
    data = {
        "fen": chess.getFen(),
        "turno": chess.getTurn(),
        "tiempoW": whiteClock.getText(),
        "tiempoB": blackClock.getText(),
        "active": gameActive,
        "nombresBlancas": nombresBlancas,
        "nombresNegras": nombresNegras,
    }
    mqtt.publish(MQTT_TOPIC, json.dumps(data), retain=True)
    refreshDisplay()
    return True


def status():
    print("active:", gameActive)
    print("fen:", chess.getFen())
    print("turno:", chess.getTurn())
    print("tiempoW:", whiteClock.getText())
    print("tiempoB:", blackClock.getText())


async def _displayPump():
    while True:
        if gameActive and display is not None:
            refreshDisplay(fullBoard=False)
        await asyncio.sleep_ms(1000)


async def _mainLoop():
    await wifi.sta.start(ssid=WIFI_SSID, password=WIFI_PASSWORD)
    if display is not None:
        asyncio.create_task(_displayPump())
    while True:
        await asyncio.sleep_ms(1000)


def _startBackground():
    asyncio.run(_mainLoop())


_thread.start_new_thread(_startBackground, ())

mqtt = MQTTClient(
    b"esp32",
    BROKER_HOST,
    BROKER_PORT,
    BROKER_USER,
    BROKER_PASSWORD,
    ssl=False
)
mqtt.connect()

_idleMs = DEFAULT_MINUTES * 60000
whiteClock.reset(_idleMs)
blackClock.reset(_idleMs)
refreshDisplay()
