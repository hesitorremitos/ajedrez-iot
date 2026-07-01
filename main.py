"""
Firmware tablero IoT (ESP32).
REPL: startGame(), play("e2-e4"), sync(), endGame(), status().
"""

import uasyncio as asyncio
import ujson as json
from umqtt.robust import MQTTClient

from modules.chess import Chess
from modules.chessclock import ChessClock
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

# Variables globales

wifi = WiFi(debug=False)
chess = Chess()
whiteClock = ChessClock()
blackClock = ChessClock()

nombresBlancas = ""
nombresNegras = ""
gameActive = False

# Conexion (al arrancar)

asyncio.run(wifi.sta.start(ssid=WIFI_SSID, password=WIFI_PASSWORD))

mqtt = MQTTClient(
    b"esp32",
    BROKER_HOST,
    BROKER_PORT,
    BROKER_USER,
    BROKER_PASSWORD,
    ssl=False
)
mqtt.connect()


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
    return True


def status():
    print("active:", gameActive)
    print("fen:", chess.getFen())
    print("turno:", chess.getTurn())
    print("tiempoW:", whiteClock.getText())
    print("tiempoB:", blackClock.getText())

