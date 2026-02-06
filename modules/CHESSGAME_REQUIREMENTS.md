---
last_updated: "2026-02-06 00:45"
version: "1.4"
status: draft
author: Discovery Architect
---

# ChessGame Module - Requerimientos (Refinado)

## Problem Statement

Se requiere un modulo coordinador `ChessGame` que compone:

- `Chess` (motor de reglas y estado)
- 2 instancias de `ChessClock` (una por color: blancas y negras)

para ofrecer una API unica de partida con reloj.

`ChessGame` es parte del core (sin hardware):

- No maneja botones/GPIO.
- No renderiza display.
- No crea AccessPoint.
- No implementa transporte.

## Goals

- Mantener `Chess` y ambos `ChessClock` sincronizados.
- Coordinar el cambio de reloj solo cuando `Chess.play(moveStr)` acepta una jugada.
- Proveer `undo()/redo()` consistentes entre tablero y reloj.
- Proveer callbacks/eventos para que un controlador de aplicacion conecte UI/Display y otros modulos.

## Non-Goals

- Control de tiempo avanzado (increment/delay) por ahora.
- Persistencia de partidas.
- Sincronizacion de estado por red.
- Manejo de input y renderizado.

## Restricciones Tecnicas

- Compatible con MicroPython para ESP32.
- Optimizar RAM/CPU (sin threads).
- camelCase en API.
- Archivo: `modules/chessgame/ChessGame.py`
- Clase: `ChessGame`

Unidad de tiempo:

- Se asume que todo tiempo en la API esta en **milisegundos** (int), sin sufijos.

## Dependencias

- `modules/chess/Chess.py`
- `modules/chessclock/ChessClock.py`

## Contrato de Uso (Importante)

- Para mantener timeout y callbacks confiables (dado que `ChessClock` es lazy), los consumidores deben obtener el tiempo a traves de `ChessGame` (no directamente desde los clocks).
- Un loop externo (UI/Display) debe llamar periodicamente `game.update()` (recomendado cada 250ms).

## API Publica

### Constructor

```python
ChessGame(chess=None, whiteClock=None, blackClock=None, debug=False)
```

- `chess`: instancia `Chess` opcional. Si None, crea una.
- `whiteClock`: instancia `ChessClock` opcional. Si None, crea una.
- `blackClock`: instancia `ChessClock` opcional. Si None, crea una.
- `debug`: bool (opcional) para logs.

### Acceso a componentes

- `getChess()` retorna la instancia `Chess`.
- `getWhiteClock()` retorna el reloj de blancas (para diagnostico/inspeccion; UI no deberia consultarlo para tiempo).
- `getBlackClock()` retorna el reloj de negras (idem).

### Colores

- `color` es `'w'` o `'b'`.

### Nueva partida

#### start(baseW, baseB=None)

Inicia una nueva partida con reloj:

1) `chess.reset()`
2) `whiteClock.reset(baseW)`
3) `blackClock.reset(baseB o baseW)`
4) Determinar turno inicial: `chess.getTurn()` (deberia ser `'w'` despues de reset).
5) Arrancar el reloj del turno inicial (resume del color activo).
6) Inicializar stacks internos para undo/redo y snapshots del reloj.

Nota:

- `ChessGame` deriva el color activo del motor (`chess.getTurn()`) durante la partida.

### Tiempo

#### getTime(color)

Proxy a `whiteClock.getTime()` / `blackClock.getTime()` segun `color`.

#### getActiveColor()

Retorna `chess.getTurn()`.

### Update (polling)

#### update()

Metodo pensado para ser llamado por el loop de UI/Display (recomendado cada 250ms).

Comportamiento:

- Sincroniza solo el clock del color activo (derivado de `chess.getTurn()`) llamando su `getTime()`.
- Si se detecta timeout (por callback del clock o por `getTime()==0`), se aplica politica de timeout (ver seccion Timeout).

### Pausa

#### pause()

- Pausa ambos clocks.
- Retorna True.

#### resume()

- Reanuda solo el clock del color activo (`chess.getTurn()`).
- Si la partida esta en timeout, `resume()` es no-op (para una nueva partida se usa `start()`).
- Retorna True.

### Movimiento

#### confirmMove(moveStr)

Confirma una jugada y coordina reloj.

Flujo:

1) Determinar `moverColor = chess.getTurn()`.
2) Determinar si la partida estaba corriendo (`wasRunning`): true si el clock de `moverColor` estaba corriendo.
3) Ejecutar `ok = chess.play(moveStr)`.
4) Si `ok`:
   - Limpiar stacks de redo.
   - Si `wasRunning`:
     - Pausar el clock del jugador que movio (esto sincroniza y captura el tiempo gastado antes del switch).
   - Cambiar el reloj de turno:
     - Si `wasRunning` y no hay timeout: reanudar el clock del rival (color activo actual ahora es `chess.getTurn()`).
     - Si la partida estaba pausada (`wasRunning=False`), mantener ambos clocks pausados.
   - Guardar snapshot del reloj para undo/redo (ver modelo de datos).
   - Disparar `onMoveAccepted(moveStr)`.
5) Si `not ok`:
   - No cambiar reloj.
   - Disparar `onMoveRejected(moveStr)`.

Retorna `bool` (resultado de `chess.play`).

Politica:

- `confirmMove()` NO bloquea movimientos por timeout; el controlador puede decidir ignorarlos.

### Undo/Redo

#### undo()

Deshace el ultimo movimiento aceptado y restaura estado del reloj asociado.

Requisitos:

- Si no hay movimientos para deshacer, retorna False.
- Debe pausar ambos clocks durante la operacion.
- Llama `ok = chess.undo()`.
- Si `ok`:
  - Mueve el ultimo `moveStr` aceptado al stack de redo.
  - Restaura el snapshot previo del reloj (ver modelo de datos).
  - Dispara `onUndo(moveStr)`.
- Retorna `ok`.

#### redo()

Rehace el ultimo movimiento deshecho (si existe) y restaura el reloj al estado exacto correspondiente.

Requisitos:

- Si no hay nada en redo, retorna False.
- Debe pausar ambos clocks durante la operacion.
- Toma el ultimo `moveStr` del stack redo y ejecuta `ok = chess.play(moveStr)`.
- Si `ok`:
  - Restaura el snapshot de reloj asociado a ese redo.
  - Dispara `onRedo(moveStr)`.
- Retorna `ok`.

Nota:

- Si despues de `undo()` se confirma un movimiento nuevo, el stack redo debe vaciarse.

## Callbacks (eventos)

Callbacks opcionales por propiedades (patron consistente con `Chess`):

- `onMoveAccepted(moveStr)`
- `onMoveRejected(moveStr)`
- `onUndo(moveStr)`
- `onRedo(moveStr)`
- `onTimeout(color)`
- `onStateChanged()` (opcional)

Semantica de `onStateChanged()`:

- Si esta presente, se dispara ante cualquier cambio observable: `start`, `confirmMove` (accepted/rejected), `undo`, `redo`, `pause`, `resume` y `timeout`.

Nota:

- `ChessGame` NO reemplaza callbacks de `Chess` (check/mate/draw).

## Modelo de Datos Interno (minimo)

- `_moveStack`: stack de movimientos aceptados (strings) en orden.
- `_redoMoves`: stack de movimientos deshechos.
- `_clockStateStack`: stack de snapshots del reloj.
- `_redoClockStateStack`: stack de snapshots del reloj asociados a redo.

Snapshot de reloj (estructura minima):

- `whiteTime` (ms)
- `blackTime` (ms)
- `activeColor` (`'w'`/`'b'`, consistente con `chess.getTurn()` en ese estado)
- `running` (bool) indicando si la partida estaba corriendo en ese snapshot

Politica de snapshots:

- Mantener un snapshot inicial al hacer `start()`.
- En una jugada aceptada:
  - Se sincroniza el gasto del jugador que movio antes del switch (pausando su reloj si estaba corriendo).
  - Luego se realiza el switch (resume del rival si correspondia).
  - Se empuja un snapshot del estado resultante (despues del switch), para permitir undo/redo exacto.

## Manejo de Timeout

Integracion con `ChessClock`:

- Cada `ChessClock` tiene `onTimeout()` sin args y auto-pause.
- `ChessGame` debe asignar handlers distintos a cada reloj para mapear a color.

Politica al ocurrir timeout:

- Pausar ambos clocks.
- Disparar `onTimeout(color)` una sola vez por evento.
- La politica de bloquear `confirmMove()` queda en el controlador app (fuera de alcance).

## Estructura de Archivos

```text
modules/
  chessgame/
    __init__.py
    ChessGame.py
tests/
  modules/
    chessgame/
      test_chess_game.py
```

## Testing (CPython)

- `ChessGame` puede testearse en CPython usando clocks falsos.

Requerimiento: Fake minimal

- El fake debe soportar al menos: `reset`, `start`, `pause`, `resume`, `getTime`, `setTime`, `addTime`, `isRunning`, `isTimeout` y la propiedad `onTimeout`.

## Ejemplo de Uso Esperado

```python
from modules.chessgame import ChessGame

game = ChessGame()
game.start(baseW=300000)

# Loop de UI/Display (ej: cada 250ms)
game.update()

ok = game.confirmMove('e2-e4')
if ok:
    print('ok')
else:
    print('illegal')

game.undo()
```

## Criterios de Aceptacion

- AC-01: `start()` resetea chess, resetea ambos clocks con `baseW/baseB` y reanuda el clock del turno inicial.
- AC-02: `confirmMove()` legal pausa el clock del que movio y reanuda el del rival solo si la partida estaba corriendo.
- AC-03: `confirmMove()` ilegal NO cambia clocks ni stacks.
- AC-04: `pause()` pausa ambos; `resume()` reanuda solo el del `chess.getTurn()` si no hay timeout.
- AC-05: `undo()` revierte el ultimo movimiento y restaura exactamente tiempos + running + activeColor del snapshot previo.
- AC-06: `redo()` rehace el movimiento y restaura exactamente el snapshot asociado.
- AC-07: `update()` sincroniza el clock activo y permite detectar timeout en modo lazy.
- AC-08: `onTimeout(color)` se propaga y `ChessGame` pausa ambos clocks al ocurrir timeout.

## Decisions Log

- 2026-02-06: Constructor acepta `whiteClock` y `blackClock` (inyeccion directa). Alternativas: factory/crear siempre interno. Razon: flexibilidad y tests con fakes.
- 2026-02-06: Unidad de tiempo en API es ms sin sufijos. Razon: consistencia con ChessClock.
- 2026-02-06: `getActiveColor()` se deriva de `chess.getTurn()`. Razon: una sola fuente de verdad.
- 2026-02-06: Se agrega `update()` para polling (UI/Display), sincronizando solo el clock activo.
- 2026-02-06: Timeout no bloquea movimientos; el controlador decide.
- 2026-02-06: Se elimina `activeColor` en `start()` para evitar inconsistencias con `chess.getTurn()`. Alternativa: permitir override alineando el motor. Razon: simplicidad.
