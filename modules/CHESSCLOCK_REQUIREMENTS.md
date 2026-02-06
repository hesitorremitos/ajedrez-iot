---
last_updated: "2026-02-06 00:00"
version: "1.3"
status: draft
author: Discovery Architect
---

# ChessClock Module - Requerimientos (Refinado)

## Metadata

- Runtime: MicroPython (ESP32)
- Testing: no requerido para este modulo (se prioriza runtime en MicroPython)

## Problem Statement

Se requiere un modulo **simple** que provea un **contador regresivo** para ajedrez.

- `ChessClock` representa **un solo contador** (una instancia por jugador).
- Un coordinador externo crea 2 instancias y decide cual corre.
- Este modulo NO decide turnos, NO valida jugadas, NO hace incrementos/delay automaticamente.

## Goals

- Contador regresivo lazy, sin threads ni timers obligatorios.
- API pequena para: iniciar, pausar, reanudar, consultar y ajustar tiempo.
- Callbacks minimos para timeout.

## Non-Goals

- Fischer increment / Bronstein delay / controles multiples.
- Persistencia en flash.
- Integracion con botones/GPIO, display o red.
- Orquestacion de turnos o reglas del juego (eso pertenece a otra capa).

## Restricciones Tecnicas

- Compatible con MicroPython para ESP32.
- Optimizar RAM/CPU.
- camelCase en metodos/propiedades.
- Archivo: `modules/chessclock/ChessClock.py`
- Clase: `ChessClock`
- Unidad estandar del modulo: **milisegundos** (int). Por simplicidad, en la API no se usa sufijo `Ms`.

## Modelo de Estado

- `initial`: tiempo base configurado para el reloj (ms).
- `time`: tiempo restante actual (ms).
- `running`: bool.
- `timeoutNotified`: latch interno para disparar `onTimeout()` solo una vez por timeout.

Reglas:

- `time` siempre se clamplea a `>= 0`.
- Si `time` llega a `0` mientras corre, el reloj hace **auto-pause** y se considera timeout.

## API Publica

### Constructor

```python
ChessClock(debug=False)
```

- `debug`: bool (opcional). Si True, permite logs de diagnostico.

### Control

#### start(initial=None)

Inicia el reloj (lo deja corriendo).

- `initial`: int (ms) opcional.

Comportamiento:

- Si `initial` es provisto: guarda `initial`, setea `time=initial`, limpia `timeoutNotified` y arranca.
- Si `initial` NO es provisto:
  - Si nunca se configuro un `initial`, usa default `300000` (5 min), setea `time=initial` y arranca.
  - Si ya existe `initial`, setea `time=initial` y arranca.

Nota: para reanudar despues de pausar, se usa `resume()`.

#### pause()

Pausa el reloj.

- Si estaba corriendo, debe sincronizar el descuento hasta "ahora" antes de detener.
- Si ya estaba pausado, es no-op.
- Retorna True (incluyendo no-op).

#### resume()

Reanuda el reloj desde el `time` actual.

- Si `time` es 0, no debe volver a correr (no-op).
- Si ya estaba corriendo, es no-op.
- Retorna True (incluyendo no-op).

### Configuracion / Reset

#### reset(initial=None)

Deja el reloj en estado pausado y con `time=initial`.

- `initial`: int (ms) opcional.

Comportamiento:

- Si `initial` es provisto: guarda `initial`.
- Si no hay `initial` guardado aun y no se pasa parametro, usa default `300000`.
- Setea `time=initial`, `running=False`.
- Limpia `timeoutNotified`.

### Ajustes de Tiempo

#### setTime(time)

Fija el tiempo restante actual.

- `time`: int (ms). Se clamplea a `>= 0`.

Si el reloj esta corriendo:

- Debe sincronizar primero (lazy), aplicar el cambio y continuar corriendo desde ese instante.

Si el resultado es `0`:

- Debe entrar en timeout: auto-pause y disparar `onTimeout()` una sola vez.

Retorna True.

#### addTime(delta)

Ajuste relativo del tiempo.

- `delta`: int (ms). Puede ser negativo.

Reglas:

- Si el reloj esta corriendo, primero sincroniza, luego aplica, y sigue corriendo.
- Clamp final a `>= 0`.
- Si el resultado es `0`, aplica politica de timeout (igual que `setTime`).

Retorna True.

### Consultas

#### getTime()

Retorna el `time` restante (ms).

- Si `running=True`, debe sincronizar lazy antes de devolver.

#### getSeconds()

Retorna `time` en segundos (int), usando **floor**: `time // 1000`.

#### getText()

Retorna string `MM:SS` usando **floor**.

- Minutos pueden exceder 59 (ej: 90 min => `90:00`).

#### isRunning()

Retorna bool.

#### isTimeout()

Retorna bool.

- True si `getTime()` (sincronizado) retorna 0.

## Callback

### onTimeout

Callback opcional cuando el reloj llega a 0.

Firma:

```python
def onTimeout():
    pass
```

Reglas:

- Se dispara **una sola vez** por cada evento de timeout.
- En timeout el reloj hace **auto-pause** (`running=False`).
- `reset()` limpia el latch para permitir un nuevo timeout en otra partida.

## Implementacion: Time Source (Lazy)

El reloj debe descontar usando ticks monotonic de MicroPython:

```python
import time

time.ticks_ms()
time.ticks_diff(now, last)
```

Nota: en CPython el modulo `time` no incluye `ticks_ms/ticks_diff`. En esta version NO se requiere ejecutar tests de `ChessClock` en CPython.

El descuento es **lazy**: se aplica en `getTime()`, `pause()`, `setTime()`, `addTime()` y en cualquier punto donde se requiera estado consistente.

Implicacion importante (lazy + callback):

- `onTimeout()` solo se dispara cuando el reloj se sincroniza (por llamadas como `getTime()`/`pause()`/`setTime()`/`addTime()`).
- Un coordinador (ej: controlador de UI) debe hacer polling/refresh periodico si necesita detectar timeout sin interaccion del usuario.

Requisito de documentacion:

- El codigo debe documentar en docstrings este comportamiento lazy y la implicacion sobre `onTimeout()`.

## Edge Cases

- `pause()` / `resume()` / `start()` repetidos no deben romper estado (no-op retorna True).
- `resume()` con `time==0` no debe reactivar.
- `setTime()` / `addTime()` con resultado 0 disparan timeout (una sola vez).

## Estructura de Archivos

```text
modules/
  chessclock/
    __init__.py
    ChessClock.py

# Opcional (si se decide testear en el futuro):
# tests/
#   modules/
#     chessclock/
#       test_chess_clock.py
```

## Ejemplos

Reloj unico:

```python
from modules.chessclock import ChessClock

clock = ChessClock()
clock.start(300000)  # 5 minutos, arranca

# ... pasa tiempo ...
print(clock.getText())

clock.pause()
clock.resume()
```

Dos instancias (tipico en ajedrez, orquestado por otro modulo):

```python
whiteClock = ChessClock()
blackClock = ChessClock()

whiteClock.reset(300000)
blackClock.reset(300000)

whiteClock.resume()  # o whiteClock.start() si se desea arrancar desde initial
```

## Criterios de Aceptacion

- AC-01: `start(initial)` guarda `initial`, setea `time=initial` y deja `running=True`.
- AC-02: `start()` sin initial usa `initial` guardado; si no existe, default 5 min.
- AC-03: `getTime()` disminuye con el tiempo (lazy) cuando `running=True`.
- AC-04: `pause()` detiene el descuento; llamadas posteriores a `getTime()` no siguen disminuyendo.
- AC-05: `resume()` reanuda desde el `time` actual sin resetear.
- AC-06: Al llegar a 0, dispara `onTimeout()` una sola vez y deja `running=False`.
- AC-07: `setTime()` y `addTime(delta)` aplican clamp a `>= 0` y preservan lazy-sync.
- AC-08: `getText()` retorna `MM:SS` con floor.

## Decisions Log

- 2026-02-06: `ChessClock` es un contador por instancia (2 instancias en un coordinador externo). Alternativas: un objeto dual. Razon: simplicidad y menor estado.
- 2026-02-06: Unidad del modulo es ms, sin sufijos `Ms` en nombres. Razon: consistencia y API mas limpia.
- 2026-02-06: Se elimina `configure()`; la configuracion se hace via `start(initial)` / `reset(initial)`.
- 2026-02-06: Default `initial=300000` cuando no hay configuracion.
- 2026-02-06: Timeout: auto-pause + `onTimeout()` una sola vez.

## Observaciones y decisiones diferidas

- Se acuerda refinar luego los requerimientos del coordinador externo para alinear su flujo de inicializacion con la nueva API (`reset(initial)` / `resume()` / `start(initial)`).
- No se requiere suite de tests en CPython para `ChessClock` en esta version. Si a futuro se quiere testear una capa de coordinacion en CPython incluyendo clocks, considerar wrappers internos de ticks (ej: usando `time.monotonic()` en CPython).
