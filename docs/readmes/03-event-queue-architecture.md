# Arquitectura por Eventos (Simple, sin clases complejas)

Este documento describe una version funcional y facil de leer para:

- boton de turno (IRQ)
- reloj
- validacion
- historial
- SSE
- render de display

## 1) Por que cola de eventos

Si cada modulo toca estado por su lado, aparecen race conditions.

Con una cola:

- todo entra como evento
- un solo coordinador modifica estado
- orden determinista

## 2) Diagrama mental

`IRQ boton` -> `flag` -> `event queue` -> `coordinator`

Y el coordinador ejecuta:

1. actualizar reloj
2. cambiar turno
3. validar reglas
4. guardar historial
5. render display
6. publicar SSE

## 3) Estado global sencillo

```python
STATE = {
    "version": 0,
    "turn": "white",
    "white_ms": 300000,
    "black_ms": 300000,
    "increment_ms": 2000,
    "last_tick_ms": 0,
    "running": "white",
    "history": [],
}
```

## 4) Eventos tipicos

- `turn_pressed`
- `tick`
- `move_http`
- `sync_request`

## 5) Ejemplo funcional (basico-intermedio)

```python
import time
import uasyncio as asyncio

EVENTS = asyncio.Queue(32)
TURN_FLAG = asyncio.ThreadSafeFlag()

def now_ms():
    return time.ticks_ms()

def consume_elapsed(state):
    if state["running"] is None:
        return
    now = now_ms()
    elapsed = time.ticks_diff(now, state["last_tick_ms"])
    state["last_tick_ms"] = now
    if state["running"] == "white":
        state["white_ms"] = max(0, state["white_ms"] - elapsed)
    else:
        state["black_ms"] = max(0, state["black_ms"] - elapsed)

async def irq_bridge():
    last_press = 0
    while True:
        await TURN_FLAG.wait()
        t = now_ms()
        if time.ticks_diff(t, last_press) < 150:
            continue
        last_press = t
        await EVENTS.put(("turn_pressed", t))

async def coordinator(state, publish_sse, render_display):
    state["last_tick_ms"] = now_ms()
    while True:
        evt, data = await EVENTS.get()

        if evt == "tick":
            consume_elapsed(state)
            continue

        if evt == "turn_pressed":
            consume_elapsed(state)

            # incremento al que termina su turno
            if state["turn"] == "white":
                state["white_ms"] += state["increment_ms"]
            else:
                state["black_ms"] += state["increment_ms"]

            # cambiar turno
            state["turn"] = "black" if state["turn"] == "white" else "white"
            state["running"] = state["turn"]
            state["last_tick_ms"] = now_ms()

            # version + fanout
            state["version"] += 1
            snap = {
                "version": state["version"],
                "turn": state["turn"],
                "white_ms": state["white_ms"],
                "black_ms": state["black_ms"],
            }
            state["history"].append(snap)
            render_display(snap)
            await publish_sse(snap)
```

## 6) Donde entran validacion e historial

- Validacion de movimiento: dentro del coordinador al procesar `move_http`.
- Historial: append en coordinador (idealmente capado a N eventos).

## 7) Integracion con servidor (tinyweb/nanoweb/microdot)

La ruta HTTP no modifica estado directamente.
Solo publica evento:

```python
await EVENTS.put(("move_http", payload))
```

El coordinador hace el resto.

## 8) Buenas practicas

- Una sola fuente de verdad (`STATE`).
- Un solo escritor (`coordinator`).
- IRQ minima.
- Mensajes SSE pequenos (usa `version`).
- Evitar operaciones largas dentro del coordinador; si algo tarda, delegar.

## 9) Cuando subir de nivel

Si el proyecto crece mucho, puedes separar en colas por modulo (actor model).
Mientras tanto, para ESP32 y legibilidad, cola unica + funciones es excelente.
