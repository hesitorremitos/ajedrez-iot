---
last_updated: "2026-02-06 16:10"
version: "1.1"
status: draft
author: Discovery Architect
---

# ChessGame Module - Documento de Requerimientos

## Problem Statement

Se requiere un modulo orquestador de partidas de ajedrez llamado `ChessGame` que coordine el motor de reglas (`Chess`), dos relojes (`ChessClock`), historial de movimientos, piezas capturadas y deteccion de fin de partida.

`ChessGame` es la **unica interfaz publica** para el usuario. Internamente crea y gestiona las instancias de `Chess` y `ChessClock`. El usuario nunca interactua directamente con estos modulos.

## Goals

- Orquestar una partida completa de ajedrez: movimientos, relojes, historial, undo.
- Soportar Fischer increment (tiempo base + incremento por movimiento).
- Detectar fin de partida: checkmate, stalemate, tablas (regla 50 movimientos + material insuficiente), timeout.
- Ser la unica interfaz publica (wrappea Chess y ChessClock via delegacion directa).
- Exponer estado del tablero como cadena de 64 caracteres para consumidores externos (ej: ChessDisplay).

## Non-Goals

- Resign / ofrecer tablas.
- Pause/resume de partida (los relojes siempre corren durante el juego).
- Modos de tiempo complejos (Bronstein delay, controles multiples por fase).
- Persistencia en flash.
- Render / display / UI.
- Partidas sin reloj (siempre se requiere tiempo base).

## Restricciones Tecnicas

- Compatible con MicroPython para ESP32.
- Optimizar RAM/CPU.
- camelCase en metodos/propiedades.
- Archivo: `modules/chessgame/ChessGame.py`
- Clase: `ChessGame`
- Dependencias internas: `modules.chess.Chess`, `modules.chessclock.ChessClock`

---

## Arquitectura Interna

```
ChessGame (orquestador)
    |
    +-- Chess (motor de reglas) ........... valida y ejecuta movimientos
    |
    +-- ChessClock x2 (whiteClock, blackClock) ... contadores regresivos
    |
    +-- Estado de partida ................. historial, capturas, undo, gameOver
```

ChessGame crea internamente:
- 1 instancia de `Chess`
- 2 instancias de `ChessClock` (una por jugador)

ChessGame registra handlers en los callbacks de Chess (`onMove`, `onCheck`, `onCheckmate`, `onStalemate`) para reaccionar a eventos del motor.

---

## API Publica

### Constructor

```python
ChessGame(debug=False)
```

- `debug`: bool (opcional). Habilita logs de diagnostico.

Al construir:
1. Crea instancia de `Chess`.
2. Crea 2 instancias de `ChessClock`.
3. Inicializa estado: historial vacio, capturas vacias, `_gameOver = False`.
4. Registra handlers internos en callbacks de Chess.

### Control de Partida

#### start(timeBase, increment=0)

Configura relojes e inicia la partida.

- `timeBase`: int (ms). Tiempo base por jugador. **Obligatorio**.
- `increment`: int (ms). Fischer increment por movimiento. Default 0 (sin incremento).

Comportamiento:
1. Configura ambos relojes con `timeBase`.
2. Guarda `increment` internamente.
3. Limpia historial, capturas, `_gameOver = False`.
4. Inicia el reloj del color activo de la posicion (`chess.getTurn()`), no necesariamente blancas.
5. **No resetea el tablero**. Si se llamo `setFen()` antes de `start()`, la posicion custom se mantiene. Si no, usa la posicion actual (default: posicion inicial del constructor).

Nota: para posiciones custom, llamar `setFen()` ANTES de `start()`.

#### reset()

Reinicia todo al estado inicial para permitir una nueva partida.

Comportamiento:
1. Tablero a posicion inicial (reset de Chess).
2. Historial vacio.
3. Capturas vacias.
4. Ambos relojes detenidos.
5. `_gameOver = False`.

Despues de `reset()`, se debe llamar `start()` para iniciar una nueva partida.

#### play(move)

Ejecuta un movimiento en la partida.

- `move`: str. Formato: `'e2-e4'`, `'O-O'`, `'O-O-O'`, `'e7-e8=Q'`.

Retorna: `bool`. True si el movimiento se ejecuto, False si invalido o partida terminada.

Flujo interno (cuando es valido):
1. Si `_gameOver` es True: retorna False.
2. Guarda `currentColor` = turno actual (antes de que Chess cambie turno).
3. Guarda estado para undo (posicion FEN + tiempos de ambos relojes + historial + capturas).
4. Delega a `chess.play(move)`.
5. Si invalido: descarta estado guardado, retorna False.
6. Si valido:
   a. Pausa reloj del jugador que movio (`currentColor`).
   b. Si `increment > 0`: `addTime(increment)` al reloj del jugador que movio.
   c. Resume reloj del oponente.
   d. Registra movimiento en historial (Chess dispara `onMove`, ChessGame lo escucha para actualizar historial y capturas).
   e. Evalua fin de partida:
      - `checkmate` / `stalemate` usando el estado de posicion ya evaluado por `Chess` tras `play()` (sin recalcular en `ChessGame`).
      - `isDraw()` → `_gameOver = True`, dispara `onDraw()`, `onGameOver('draw', None)`.
   f. Retorna True.

Nota sobre timeout: el timeout se detecta cuando `ChessClock` dispara `onTimeout`. ChessGame escucha este callback para marcar `_gameOver = True` y disparar `onGameOver('timeout', winnerColor)`.

#### undo()

Deshace el ultimo movimiento. Restaura estado del tablero Y tiempos de relojes.

Retorna: `bool`. True si se deshizo, False si no hay movimientos.

Flujo interno:
1. Si pila de estados vacia: retorna False.
2. Pop estado anterior.
3. Restaura posicion de Chess via `setFen(savedFen)`.
4. Restaura tiempos: `whiteClock.setTime(savedWhiteTime)`, `blackClock.setTime(savedBlackTime)`.
5. Restaura historial y capturas.
6. `_gameOver = False` (si se deshizo un movimiento que termino la partida).
7. Reanuda reloj del turno actual.
8. Retorna True.

### Consultas Delegadas a Chess

Estos metodos delegan directamente al motor de reglas. ChessGame los expone para que el usuario no necesite acceder a Chess directamente.

| Metodo | Parametros | Retorno | Delegacion |
|--------|------------|---------|------------|
| `getLegalMoves` | `square: str` | `list[str]` | `chess.getLegalMoves(square)` |
| `getPiece` | `square: str` | `str` | `chess.getPiece(square)` |
| `getBoard` | ninguno | `list` | `chess.getBoard()` |
| `isCheck` | ninguno | `bool` | `chess.isCheck()` |
| `isCheckmate` | ninguno | `bool` | `chess.isCheckmate()` |
| `isStalemate` | ninguno | `bool` | `chess.isStalemate()` |
| `getTurn` | ninguno | `str` | `chess.getTurn()` |

### Consultas de Partida

#### isDraw()

Verifica si la partida es tablas.

Evalua:
- **Regla de 50 movimientos**: `halfmoveClock >= 100` (100 medios-movimientos = 50 completos). El contador `halfmoveClock` se mantiene internamente en Chess como parte del estado FEN.
- **Material insuficiente**: delega a `chess.isInsufficientMaterial()`.

Implementacion recomendada: acceder al contador via API publica (`chess.getHalfmoveClock()`), evitando tocar atributos privados.

Retorna: `bool`.

#### isGameOver()

Verifica si la partida termino por cualquier razon.

Retorna: `bool`. True si checkmate, stalemate, draw o timeout.

Nota: tambien se puede consultar `_gameOver` directamente, que se actualiza en `play()` y en el handler de timeout.

#### getHistory()

Devuelve el historial de movimientos.

Retorna: `list[tuple]`. Formato: `[('e2-e4', 'e7-e5'), ('g1-f3', 'b8-c6')]`.
Si las negras no han movido en el ultimo turno: `('d2-d4', '')`.

#### getCapturedPieces()

Obtiene las piezas capturadas durante la partida.

Retorna: `dict`. Formato: `{"w": str, "b": str}`.
- `"w"`: piezas negras capturadas por blancas (minusculas), ordenadas por valor descendente.
- `"b"`: piezas blancas capturadas por negras (mayusculas), ordenadas por valor descendente.

Orden de valor: dama > torre > alfil > caballo > peon.

#### getFen()

Exporta la posicion actual a notacion FEN completa (6 campos).

Retorna: `str`. FEN standard completo.

Internamente delega a `chess.getFen()`, que mantiene los 6 campos incluyendo `halfmoveClock` y `fullmoveNumber`.

#### setFen(fen)

Carga una posicion desde notacion FEN.

- `fen`: str. FEN standard (4 a 6 campos).

Internamente delega a `chess.setFen(fen)`.

**Uso**: llamar ANTES de `start()` para partidas con posicion custom.

#### getPgn(headers=None)

Exporta la partida a formato PGN.

- `headers`: dict opcional con cabeceras PGN.

Retorna: `str`. PGN completo con cabeceras y movimientos.

Determina resultado automaticamente segun estado de partida:
- Checkmate: `1-0` o `0-1` segun ganador.
- Stalemate / Draw: `1/2-1/2`.
- Timeout: `1-0` o `0-1` segun ganador.
- En curso: `*`.

### Consultas de Relojes

| Metodo | Parametros | Retorno | Descripcion |
|--------|------------|---------|-------------|
| `getTime` | `color: str` | `int` | Tiempo restante en ms. `color`: `'w'` o `'b'` |
| `getText` | `color: str` | `str` | Tiempo restante en formato `'MM:SS'` |
| `getSeconds` | `color: str` | `int` | Tiempo restante en segundos (floor) |

---

## Callbacks

### onTimeout

Se dispara cuando un reloj llega a 0.

```python
def onTimeout(color):
    # color: 'w' o 'b' (quien se quedo sin tiempo)
    pass
```

ChessGame internamente registra handlers en `ChessClock.onTimeout` de ambos relojes. Cuando uno dispara, ChessGame:
1. Marca `_gameOver = True`.
2. Dispara `onTimeout(color)`.
3. Dispara `onGameOver('timeout', winnerColor)` (el oponente gana).

### onDraw

Se dispara cuando la partida termina en tablas.

```python
def onDraw():
    pass
```

### onGameOver

Se dispara cuando la partida termina por cualquier razon.

```python
def onGameOver(reason, winner):
    # reason: 'checkmate', 'stalemate', 'draw', 'timeout'
    # winner: 'w', 'b', o None (en caso de tablas/stalemate)
    pass
```

### Orden de disparo de callbacks

En una situacion de fin de partida, el orden es:
1. Primero el callback especifico: `onDraw()` o `onTimeout(color)`.
2. Luego siempre `onGameOver(reason, winner)`.

Nota: `onCheck`, `onCheckmate`, `onStalemate` son callbacks de Chess (motor de reglas). ChessGame puede exponerlos via propiedades si el usuario desea escucharlos directamente, pero no los redefine.

### Exposicion de callbacks de Chess

ChessGame expone los callbacks de posicion de Chess como propiedades delegadas:

| Propiedad | Delega a |
|-----------|----------|
| `onCheck` | `chess.onCheck` |
| `onCheckmate` | `chess.onCheckmate` |
| `onStalemate` | `chess.onStalemate` |

Esto permite al usuario registrar handlers para eventos de posicion sin acceder a Chess directamente.

---

## Modelo de Estado Interno

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `_chess` | `Chess` | Instancia del motor de reglas |
| `_whiteClock` | `ChessClock` | Reloj de blancas |
| `_blackClock` | `ChessClock` | Reloj de negras |
| `_increment` | `int` | Fischer increment en ms (0 = sin incremento) |
| `_history` | `list` | Historial: `[[movBlancas, movNegras], ...]` |
| `_currentTurnMove` | `str` or `None` | Movimiento de blancas pendiente de negras |
| `_moveStack` | `list` | Pila de estados para undo |
| `_capturedPieces` | `dict` | `{"w": [], "b": []}` |
| `_gameOver` | `bool` | True si la partida termino |

### Estado guardado para undo

Cada entrada en `_moveStack` contiene:
- `fen`: string FEN completo de la posicion anterior.
- `whiteTime`: int, tiempo del reloj blanco en ms.
- `blackTime`: int, tiempo del reloj negro en ms.
- `history`: copia del historial.
- `currentTurnMove`: movimiento pendiente.
- `capturedPieces`: copia de capturas.
- `gameOver`: bool.

Se usa FEN para snapshot/restore de Chess porque es el mecanismo mas limpio: `chess.getFen()` para guardar, `chess.setFen()` para restaurar. Esto evita acoplar ChessGame a los internos de Chess.

---

## Integracion con Chess (Motor de Reglas)

### Callbacks que ChessGame escucha de Chess

#### onMove(moveStr, captured, isPromotion, isCastling, isEnPassant)

Chess dispara este callback despues de cada `play()` exitoso. ChessGame lo usa para:
- Actualizar `_capturedPieces` con la pieza capturada (si `captured` no es None).
- Actualizar `_history` con el movimiento.

Parametros:
- `moveStr`: str. Movimiento ejecutado (ej: `'e2-e4'`, `'O-O'`).
- `captured`: str o None. Pieza capturada (ej: `'p'`, `'N'`). None si no hubo captura.
- `isPromotion`: bool. True si fue promocion de peon.
- `isCastling`: bool. True si fue enroque.
- `isEnPassant`: bool. True si fue captura al paso.

### Metodos de Chess que ChessGame invoca

- `chess.play(move)` — ejecutar movimiento.
- `chess.getLegalMoves(square)` — consultar movimientos legales.
- `chess.getPiece(square)` — consultar pieza.
- `chess.getBoard()` — obtener tablero como lista de 64 caracteres.
- `chess.getTurn()` — consultar turno.
- `chess.isCheck()` — consultar jaque.
- `chess.isCheckmate()` — consultar jaque mate.
- `chess.isStalemate()` — consultar ahogado.
- `chess.isInsufficientMaterial()` — consultar material insuficiente.
- `chess.getFen()` — obtener FEN completo.
- `chess.setFen(fen)` — cargar posicion.
- `chess.reset()` — resetear tablero.

---

## Integracion con ChessClock

ChessGame crea 2 instancias de ChessClock (whiteClock, blackClock) y las orquesta:

### En start(timeBase, increment)
- `whiteClock.reset(timeBase)` y `blackClock.reset(timeBase)`.
- Se reanuda el reloj del turno activo en la posicion (`chess.getTurn()`).
- Registra handlers de `onTimeout` en ambos relojes.

### En play() (movimiento exitoso)
1. Pausa reloj del jugador que movio: `clock.pause()`.
2. Si `increment > 0`: `clock.addTime(increment)` al reloj del jugador que movio.
3. Resume reloj del oponente: `opponentClock.resume()`.

### En undo()
- Restaura tiempos: `whiteClock.setTime(savedWhiteTime)`, `blackClock.setTime(savedBlackTime)`.
- Reanuda reloj del turno actual.

### Deteccion de timeout
- ChessClock dispara `onTimeout` cuando llega a 0 (lazy: se detecta en `getTime()`/`pause()`/etc.).
- ChessGame escucha este callback, marca `_gameOver = True` y dispara sus propios callbacks.
- **Importante**: dado que ChessClock es lazy, ChessGame (o un controlador de UI externo) debe hacer polling periodico via `getTime()` para detectar timeout sin interaccion del usuario.

---

## Estructura de Archivos

```text
modules/
  CHESSGAME_REQUIREMENTS.md     # Este documento
  chessgame/
    __init__.py                  # Exporta ChessGame
    ChessGame.py                 # Clase principal

tests/
  modules/
    chessgame/
      test_chessgame.py          # Tests de ChessGame
```

---

## Edge Cases

- `play()` con `_gameOver = True` retorna False sin efecto.
- `undo()` con pila vacia retorna False.
- `undo()` despues de game over: restaura estado y permite continuar (gameOver = False).
- `start()` llamado multiples veces: reinicia relojes y estado de partida (no resetea tablero).
- `start()` sin `setFen()` previo: usa posicion actual (inicial del constructor, o la cargada previamente).
- `getTime('w')` / `getTime('b')` con colores invalidos: comportamiento indefinido (no se valida).
- Timeout durante `play()`: si el reloj del oponente hace timeout antes de que juegue, se detecta en el siguiente `getTime()` o `play()`.
- Fischer increment: se aplica SOLO al jugador que acaba de mover, y solo si `increment > 0`.

---

## Ejemplo de Uso

### Partida basica (5 minutos + 3 segundos increment)

```python
from modules.chessgame import ChessGame

game = ChessGame()

# Registrar callbacks
game.onGameOver = lambda reason, winner: print(f"Game over: {reason}, winner: {winner}")
game.onTimeout = lambda color: print(f"Timeout: {color}")

# Iniciar partida: 5 min + 3 seg increment
game.start(300000, 3000)

# Jugar
game.play('e2-e4')    # True, reloj blanco pausa + 3s, reloj negro resume
game.play('e7-e5')    # True, reloj negro pausa + 3s, reloj blanco resume

# Consultar estado
game.getTurn()         # 'w'
game.getLegalMoves('g1')  # ['g1-f3', 'g1-h3']
game.getBoard()        # lista de 64 caracteres
game.getText('w')      # '5:01' (aprox)
game.getText('b')      # '5:02' (aprox)

# Historial
game.getHistory()      # [('e2-e4', 'e7-e5')]

# Deshacer (restaura tablero y tiempos)
game.undo()
game.getTurn()         # 'b' (vuelve al turno de negras)
```

### Partida con posicion custom

```python
game = ChessGame()
game.setFen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1")
game.start(600000)  # 10 min sin increment

game.play('O-O')       # Enroque corto blancas
```

### Reiniciar para nueva partida

```python
game.reset()                    # Todo a estado inicial
game.start(180000, 2000)        # Nueva partida: 3 min + 2 seg
```

---

## Criterios de Aceptacion

### AC-01: Crear instancia
- **Given** ninguna configuracion previa
- **When** se crea `ChessGame()`
- **Then** la instancia se crea con Chess en posicion inicial, 2 relojes detenidos, historial vacio, gameOver=False

### AC-02: start() inicia partida
- **Given** una instancia de ChessGame
- **When** se llama `start(300000, 3000)`
- **Then** ambos relojes se configuran con 300000ms, increment=3000, corre el reloj del turno activo (`getTurn()`), el otro queda pausado, gameOver=False

### AC-03: play() ejecuta movimiento valido
- **Given** partida iniciada con start()
- **When** se llama `play('e2-e4')`
- **Then** retorna True, tablero actualizado, reloj blanco pausado + increment, reloj negro corriendo, historial actualizado

### AC-04: play() rechaza movimiento invalido
- **Given** partida iniciada
- **When** se llama `play('e2-e5')` (movimiento ilegal)
- **Then** retorna False, estado no cambia

### AC-05: play() rechaza si gameOver
- **Given** partida terminada (gameOver=True)
- **When** se llama `play('e2-e4')`
- **Then** retorna False

### AC-06: Fischer increment
- **Given** partida con increment=3000
- **When** blancas juegan un movimiento valido
- **Then** reloj blanco recibe addTime(3000) antes de pausar, luego reloj negro resume

### AC-07: undo() restaura tablero y tiempos
- **Given** partida con 2 movimientos jugados
- **When** se llama `undo()`
- **Then** tablero vuelve al estado anterior, tiempos de ambos relojes restaurados, historial actualizado

### AC-08: undo() sin movimientos
- **Given** partida sin movimientos
- **When** se llama `undo()`
- **Then** retorna False

### AC-09: reset() reinicia todo
- **Given** partida con movimientos jugados y relojes corriendo
- **When** se llama `reset()`
- **Then** tablero posicion inicial, historial vacio, capturas vacias, relojes detenidos, gameOver=False

### AC-10: isDraw() detecta regla 50 movimientos
- **Given** posicion con halfmoveClock=99 y un movimiento sin captura ni peon
- **When** se ejecuta el movimiento y se consulta `isDraw()`
- **Then** retorna True

### AC-11: isDraw() detecta material insuficiente
- **Given** posicion K vs K
- **When** se consulta `isDraw()`
- **Then** retorna True

### AC-12: isGameOver() detecta checkmate
- **Given** posicion de jaque mate
- **When** se consulta `isGameOver()`
- **Then** retorna True

### AC-13: onGameOver callback se dispara con razon y ganador
- **Given** callback registrado en onGameOver
- **When** ocurre jaque mate por blancas
- **Then** callback recibe ('checkmate', 'w')

### AC-14: onTimeout callback se dispara
- **Given** callback registrado en onTimeout y reloj de negras llega a 0
- **When** se detecta timeout (via getTime o play)
- **Then** callback recibe 'b', gameOver=True, onGameOver recibe ('timeout', 'w')

### AC-15: setFen() antes de start() permite posicion custom
- **Given** instancia nueva
- **When** se llama `setFen(customFen)` y luego `start(300000)`
- **Then** la partida inicia con la posicion custom, no la inicial

### AC-16: Delegacion de getLegalMoves
- **Given** partida iniciada
- **When** se llama `game.getLegalMoves('e2')`
- **Then** retorna los mismos resultados que chess.getLegalMoves('e2')

### AC-17: getHistory() formato correcto
- **Given** partida con e2-e4, e7-e5, g1-f3 jugados
- **When** se consulta `getHistory()`
- **Then** retorna [('e2-e4', 'e7-e5'), ('g1-f3', '')]

### AC-18: getCapturedPieces() trackea capturas
- **Given** blancas capturan peon negro
- **When** se consulta `getCapturedPieces()`
- **Then** retorna {"w": "p", "b": ""}

### AC-19: getTime(color) retorna tiempo correcto
- **Given** partida con relojes corriendo
- **When** se llama `getTime('w')` y `getTime('b')`
- **Then** retorna tiempo restante en ms para cada jugador

### AC-20: getPgn() exporta partida completa
- **Given** partida con movimientos jugados
- **When** se llama `getPgn()`
- **Then** retorna string PGN con cabeceras y movimientos

---

## Decisions Log

| Fecha | Decision | Alternativas | Razon |
|-------|----------|--------------|-------|
| 2026-02-06 | Chess se convierte en motor puro de reglas | Chess mantiene logica de partida; ChessGame como wrapper delgado | Separacion de responsabilidades: Chess = reglas, ChessGame = partida |
| 2026-02-06 | play() en Chess retorna solo bool | Dict con detalles; tupla minima | Se usa callback onMove para comunicar detalles, evitando allocaciones en cada movimiento (ESP32) |
| 2026-02-06 | Callbacks en Chess para eventos de tablero | Chess retorna info, ChessGame compara snapshots | Callbacks son zero-allocation si no hay listener; snapshots gastan 64 bytes + CPU |
| 2026-02-06 | ChessGame es unica interfaz publica | Exponer Chess como propiedad; mixto | Encapsulacion completa, el usuario no necesita conocer Chess ni ChessClock |
| 2026-02-06 | Fischer increment al jugador que movio | Increment al oponente; sin increment | Es el estandar Fischer: mueves y ganas tiempo |
| 2026-02-06 | Siempre con reloj | Reloj opcional; partidas sin limite | Simplifica la logica; para "sin limite" se usa un timeBase alto |
| 2026-02-06 | Undo restaura tiempos de relojes | Undo no toca relojes; undo pausa relojes; desactivar undo con reloj | Mantiene consistencia completa del estado de partida |
| 2026-02-06 | reset() + start() para reiniciar | Solo start(); sin reset() | Separacion clara: reset limpia, start configura e inicia |
| 2026-02-06 | _gameOver como bool simple | Estados explicitos (idle/playing/paused/finished); sin estado formal | Suficiente para los requerimientos actuales, minimo overhead |
| 2026-02-06 | onGameOver(reason, winner) | Sin parametros; solo reason | Maximo contexto para el consumidor sin consultas adicionales |
| 2026-02-06 | FEN completo (6 campos) se mantiene en Chess internamente | FEN parcial en Chess, completo en ChessGame; duplicar | Chess ya mantiene halfmoveClock/fullmoveNumber para FEN. ChessGame delega |
| 2026-02-06 | `start()` activa reloj segun turno FEN (`w`/`b`) | Siempre iniciar blancas | Evita desincronizacion reloj-tablero en posiciones custom |
| 2026-02-06 | `ChessGame` evita recalcular mate/ahogado despues de `play()` | Recalcular en ChessGame tras `Chess.play()` | Reduce CPU en ESP32 y mantiene una sola fuente de verdad para estado de posicion |
| 2026-02-06 | `isDraw()` usa `chess.getHalfmoveClock()` | Leer `chess._halfmoveClock` privado | Menor acoplamiento y mejor mantenibilidad |
| 2026-02-06 | isInsufficientMaterial() queda en Chess (publica) | Todo isDraw en ChessGame; todo en Chess | Es evaluacion pura de posicion. isDraw (regla 50) va a ChessGame |
| 2026-02-06 | getBoard() en Chess retorna lista de 64 chars | Parsear FEN; acceso directo a _board | Parsear FEN es coste innecesario en ESP32. Acceso directo es O(1) |
| 2026-02-06 | Estado undo guardado con FEN | Copia directa de _board; Chess expone saveState/restoreState | FEN es mecanismo limpio sin acoplar ChessGame a internos de Chess |

## Observaciones y decisiones diferidas

- **Polling de timeout**: Dado que ChessClock es lazy, el timeout solo se detecta en llamadas a getTime()/pause()/etc. Un controlador de UI externo deberia hacer polling periodico. Si esto resulta insuficiente, considerar agregar un metodo `tick()` en ChessGame que sincronice ambos relojes.
- **Orden exacto de callbacks**: El orden de disparo (onMove de Chess → actualizacion de estado en ChessGame → evaluacion de fin → callbacks de ChessGame) puede ajustarse durante implementacion si se encuentran problemas de timing.
- **Tests en CPython**: ChessClock usa `time.ticks_ms()` que no existe en CPython. Para testear ChessGame en CPython, considerar mock de ChessClock o wrappers de ticks como se menciona en CHESSCLOCK_REQUIREMENTS.
