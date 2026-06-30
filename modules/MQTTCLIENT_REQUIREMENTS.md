---
last_updated: "2026-06-30"
version: "1.0"
status: draft
author: Discovery Architect
---

# MqttClient Module - Documento de Requerimientos

> Capa de transporte MQTT bidireccional para ESP32. Publica estado del tablero y recibe comandos de partida. No valida reglas de ajedrez ni gestiona WiFi.

## Descripcion General

Modulo `MqttClient` para ESP32 (MicroPython) que conecta a un broker MQTT, publica payloads JSON y se suscribe a topics de comando. Depende de `wifi.sta` para conectividad de red; la reconexion WiFi la gestiona el modulo `network`.

Casos de uso:
- Publicar snapshot de partida (FEN, turno, relojes) en topic retain.
- Publicar eventos puntuales (movimiento, fin de partida).
- Recibir comandos admin (`nueva_partida`, `finalizar_partida`) y entregarlos al coordinador via callback.

## Restricciones Tecnicas

- Compatible con MicroPython para ESP32.
- Optimizar RAM: dict plano + `ujson`, sin serializadores custom.
- camelCase en metodos y propiedades publicas.
- Archivo: `modules/mqttClient/MqttClient.py`
- Clase: `MqttClient`
- Libreria de transporte: `umqtt.robust` vendoreada en `lib/umqtt/`
- Patron de errores: metodos retornan `True`/`False`, sin excepciones custom.

---

## Arquitectura

```
wifi.sta.onConnect  -->  mqttClient.connect()
wifi.sta.onDisconnect --> mqttClient.disconnect()
coordinador         -->  mqttClient.publish(topic, dict)
broker              -->  mqttClient.onMessage --> EVENTS.put(("mqtt_cmd", payload))
```

### Principio de independencia

- `MqttClient` no llama `chess.play()` ni interpreta `tipo` de comandos.
- El coordinador construye payloads con `buildStatePayload()` en `payload.py`.
- WiFi y MQTT son capas separadas; reconexion MQTT ocurre en `onConnect` de WiFi.

---

## Topics MQTT

| Topic | Direccion | QoS | Retain | Uso |
|-------|-----------|-----|--------|-----|
| `adapt/{deviceId}/state` | ESP32 -> broker | 0 | true | Snapshot actual |
| `adapt/{deviceId}/events` | ESP32 -> broker | 0 | false | Eventos puntuales |
| `adapt/{deviceId}/cmd` | broker -> ESP32 | 0 | false | Comandos admin |

`deviceId` es configuracion del coordinador (ej. `"tablero-01"`).

---

## Contrato JSON

### Salida (ESP32 -> broker)

Campos minimos:

```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
  "turno": "b",
  "tiempoW": "09:45",
  "tiempoB": "10:00"
}
```

Campos opcionales (solo si el coordinador los tiene):

| Campo | Fuente |
|-------|--------|
| `move` | ultimo movimiento |
| `pgn` | string acumulado en coordinador |
| `sensores` | contador hardware |
| `nombresBlancas` / `nombresNegras` | estado de partida |

### Entrada (broker -> ESP32)

```json
{ "tipo": "nueva_partida" }
```

```json
{ "tipo": "finalizar_partida" }
```

El coordinador traduce `tipo` a acciones sobre Chess, ChessClock y estado de partida.

---

## API Publica

### Constructor

```python
MqttClient(debug=False)
```

### Metodos

| Metodo | Retorno | Descripcion |
|--------|---------|-------------|
| `connect(host, port=1883, clientId=None, user=None, password=None, keepalive=60)` | `bool` | Conecta al broker e inicia poll de mensajes |
| `disconnect()` | `bool` | Desconecta y detiene poll |
| `isConnected()` | `bool` | Estado de conexion |
| `publish(topic, payload, qos=0, retain=False)` | `bool` | Publica dict (ujson), str o bytes |
| `subscribe(topic, qos=0)` | `bool` | Suscribe a topic |

`payload` en `publish`: si es `dict`, se serializa con `ujson.dumps`.

### Callbacks

| Callback | Cuando |
|----------|--------|
| `onConnect` | Tras conexion exitosa (re-suscribir cmd aqui) |
| `onDisconnect` | Tras desconexion |
| `onMessage` | Mensaje recibido: `callback(topic, payload)` — payload es dict si JSON valido, sino str |

---

## Helper: buildStatePayload

Funcion en `modules/mqttClient/payload.py`:

```python
buildStatePayload(chess, whiteClock, blackClock, gameState=None) -> dict
```

Construye dict plano con claves presentes. `gameState` es dict opcional con `move`, `pgn`, `sensores`, `nombresBlancas`, `nombresNegras`.

---

## User Stories

### US-1: Conectar tras WiFi

- **Given** `wifi.sta` conectado
- **When** se llama `connect(host, clientId="tablero-01")`
- **Then** retorna `True` y dispara `onConnect`

### US-2: Publicar FEN

- **Given** cliente conectado
- **When** `publish("adapt/tablero-01/state", {"fen": "...", "turno": "w"}, retain=True)`
- **Then** retorna `True`

### US-3: Recibir finalizar partida

- **Given** suscrito a `adapt/tablero-01/cmd`
- **When** llega `{"tipo": "finalizar_partida"}`
- **Then** `onMessage` recibe dict con `tipo`

---

## Decisiones

| Decision | Razon |
|----------|-------|
| `umqtt.robust` vs `mqtt_as` | No solapa WiFi con `network`; suficiente para POC y produccion inicial |
| JSON plano vs web completo | Prioridad ESP32; web/backend adapta campos faltantes |
| `tipo` en comandos | Alineado con `web/js/esp32.js` |
| Poll async 100ms | No bloquea coordinador; compatible con uasyncio |

---

## Funcionalidad Excluida

- TLS/SSL (fase posterior).
- QoS 1 garantizado.
- Persistencia de configuracion broker en flash.
- Interpretacion de comandos dentro del modulo.
- PGN dentro del modulo Chess.

---

## Version

- Version del documento: 1.0
- Fecha: Junio 2026
