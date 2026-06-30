# MqttClient Module

Transporte MQTT bidireccional para ESP32. Publica estado del tablero y recibe comandos via callback.

## Uso minimo

```python
import uasyncio as asyncio
from modules.network import WiFi
from modules.mqttClient import MqttClient, buildStatePayload
from modules.chess import Chess
from modules.chessclock import ChessClock

DEVICE_ID = "tablero-01"
BROKER_HOST = "192.168.1.10"
STATE_TOPIC = "adapt/{}/state".format(DEVICE_ID)
EVENTS_TOPIC = "adapt/{}/events".format(DEVICE_ID)
CMD_TOPIC = "adapt/{}/cmd".format(DEVICE_ID)

wifi = WiFi()
mqtt = MqttClient(debug=True)
chess = Chess()
whiteClock = ChessClock()
blackClock = ChessClock()

async def onMqttConnect():
    await mqtt.subscribe(CMD_TOPIC)

def onMqttMessage(topic, payload):
    asyncio.create_task(EVENTS.put(("mqtt_cmd", payload)))

mqtt.onConnect = onMqttConnect
mqtt.onMessage = onMqttMessage

def onStaConnect(ip):
    asyncio.create_task(mqtt.connect(host=BROKER_HOST, clientId=DEVICE_ID))

def onStaDisconnect():
    asyncio.create_task(mqtt.disconnect())

wifi.sta.onConnect = onStaConnect
wifi.sta.onDisconnect = onStaDisconnect
```

Ver `examples/main_mqtt.py` para integracion completa con cola de eventos.

## Contrato JSON

Salida: `fen`, `turno`, `tiempoW`, `tiempoB` (+ opcionales via `buildStatePayload`).

Entrada en `/cmd`: `{"tipo": "nueva_partida"}` o `{"tipo": "finalizar_partida"}`.

## Notas

- Depende de `umqtt.robust` en `lib/umqtt/` (compilar con `uv run build`).
- No interpreta comandos; el coordinador procesa `mqtt_cmd`.
- Re-suscribir en `onConnect` tras reconexion WiFi.
