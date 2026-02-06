# ChessGame

Modulo orquestador de partidas de ajedrez para ESP32 (MicroPython). Coordina el motor de reglas (`Chess`), dos relojes (`ChessClock`), historial de movimientos, piezas capturadas y deteccion de fin de partida.

**ChessGame es la unica interfaz publica para el usuario.** Internamente crea y gestiona las instancias de `Chess` y `ChessClock`. El usuario nunca interactua directamente con estos modulos.

## Caracteristicas

- Orquestacion completa de partida: movimientos, relojes, historial, undo
- Soporte Fischer increment (tiempo base + incremento por movimiento)
- Deteccion de fin de partida: checkmate, stalemate, tablas (regla 50 movimientos + material insuficiente), timeout
- Delegacion directa a Chess para consultas de reglas
- Exportacion a FEN y PGN
- Callbacks para eventos de partida y posicion

## Arquitectura

```
ChessGame (orquestador)
    |
    +-- Chess (motor de reglas) ........... valida y ejecuta movimientos
    |
    +-- ChessClock x2 .................... contadores regresivos (blancas/negras)
    |
    +-- Estado de partida ................. historial, capturas, undo, gameOver
```

## API Publica

### Constructor

```python
ChessGame(debug=False)
```

| Parametro | Tipo | Descripcion |
|-----------|------|-------------|
| `debug` | `bool` | Activa modo debug para mensajes de diagnostico. Default: `False` |

Al construir: crea instancia de Chess en posicion inicial, 2 relojes detenidos, historial vacio, `gameOver=False`.

### Control de Partida

#### `start(timeBase, increment=0)`

Configura relojes e inicia la partida.

| Parametro | Tipo | Descripcion |
|-----------|------|-------------|
| `timeBase` | `int` | Tiempo base por jugador en ms. **Obligatorio** |
| `increment` | `int` | Fischer increment por movimiento en ms. Default: `0` |

Comportamiento:
1. Configura ambos relojes con `timeBase`.
2. Limpia historial, capturas, `gameOver`.
3. Inicia el reloj del turno activo de la posicion (`getTurn()`), respetando FEN custom.
4. **No resetea el tablero**. Si se llamo `setFen()` antes, la posicion custom se mantiene.

```python
game = ChessGame()
game.start(300000, 3000)  # 5 min + 3 seg increment
```

#### `reset()`

Reinicia todo al estado inicial. Despues de `reset()`, se debe llamar `start()` para iniciar una nueva partida.

- Tablero a posicion inicial
- Historial vacio, capturas vacias
- Ambos relojes detenidos
- `gameOver = False`

```python
game.reset()
game.start(180000, 2000)  # Nueva partida: 3 min + 2 seg
```

#### `play(move) -> bool`

Ejecuta un movimiento en la partida. Retorna `True` si se ejecuto, `False` si invalido o partida terminada.

| Parametro | Tipo | Descripcion |
|-----------|------|-------------|
| `move` | `str` | Movimiento en formato `'e2-e4'`, `'O-O'`, `'O-O-O'`, `'e7-e8=Q'` |

Flujo interno (movimiento valido):
1. Pausa reloj del jugador que movio.
2. Si `increment > 0`: aplica Fischer increment al jugador que movio.
3. Reanuda reloj del oponente.
4. Actualiza historial y capturas (via callback `onMove` de Chess).
5. Evalua fin de partida (checkmate, stalemate, draw).

```python
game.play('e2-e4')   # True
game.play('e7-e5')   # True
game.play('invalid') # False
```

#### `undo() -> bool`

Deshace el ultimo movimiento. Restaura tablero (via FEN), tiempos de ambos relojes, historial y capturas. Retorna `True` si se deshizo, `False` si no hay movimientos.

```python
game.play('e2-e4')
game.play('e7-e5')
game.undo()            # True, deshace e7-e5
game.getTurn()         # 'b'
game.undo()            # True, deshace e2-e4
game.getTurn()         # 'w'
game.undo()            # False, no hay mas movimientos
```

Si la partida termino (gameOver), `undo()` restaura el estado anterior y permite continuar.

### Consultas Delegadas a Chess

Estos metodos delegan directamente al motor de reglas. ChessGame los expone para que el usuario no necesite acceder a Chess directamente.

| Metodo | Parametros | Retorno | Descripcion |
|--------|------------|---------|-------------|
| `getLegalMoves(square)` | `square: str` | `list` | Movimientos legales de la pieza en la casilla |
| `getPiece(square)` | `square: str` | `str` | Pieza en la casilla (o espacio si vacia) |
| `getBoard()` | ninguno | `list` | Tablero como lista de 64 caracteres |
| `isCheck()` | ninguno | `bool` | Si el jugador en turno esta en jaque |
| `isCheckmate()` | ninguno | `bool` | Si hay jaque mate |
| `isStalemate()` | ninguno | `bool` | Si hay ahogado |
| `getTurn()` | ninguno | `str` | Turno actual: `'w'` o `'b'` |

```python
game.getLegalMoves('e2')  # ['e2-e3', 'e2-e4']
game.getPiece('e1')       # 'K'
game.getBoard()           # lista de 64 caracteres
game.getTurn()            # 'w'
```

### Consultas de Partida

#### `isDraw() -> bool`

Verifica si la partida es tablas. Evalua:
- **Regla de 50 movimientos**: `halfmoveClock >= 100` (100 medios-movimientos = 50 completos).
- **Material insuficiente**: K vs K, K vs K+B, K vs K+N, K+B vs K+B (mismo color de casilla).

#### `isGameOver() -> bool`

Verifica si la partida termino por cualquier razon (checkmate, stalemate, draw, timeout).

#### `getHistory() -> list`

Devuelve el historial de movimientos como lista de tuplas.

```python
game.play('e2-e4')
game.play('e7-e5')
game.play('g1-f3')
game.getHistory()
# [('e2-e4', 'e7-e5'), ('g1-f3', '')]
```

Si las negras no han movido en el ultimo turno, el segundo elemento es `''`.

#### `getCapturedPieces() -> dict`

Obtiene las piezas capturadas durante la partida.

```python
game.getCapturedPieces()
# {"w": "p", "b": ""}
```

- `"w"`: piezas negras capturadas por blancas (minusculas), ordenadas por valor descendente.
- `"b"`: piezas blancas capturadas por negras (mayusculas), ordenadas por valor descendente.

Orden de valor: Q/q > R/r > B/b > N/n > P/p.

#### `getFen() -> str`

Exporta la posicion actual a notacion FEN completa (6 campos).

```python
game.getFen()
# 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
```

#### `setFen(fen)`

Carga una posicion desde notacion FEN. **Llamar ANTES de `start()`** para partidas con posicion custom.

```python
game = ChessGame()
game.setFen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1")
game.start(600000)
game.play('O-O')  # Enroque corto blancas
```

#### `getPgn(headers=None) -> str`

Exporta la partida a formato PGN con cabeceras y movimientos.

| Parametro | Tipo | Descripcion |
|-----------|------|-------------|
| `headers` | `dict` | Cabeceras PGN opcionales. Default: `None` |

Determina resultado automaticamente:
- Checkmate: `1-0` o `0-1`
- Stalemate / Draw: `1/2-1/2`
- Timeout: `1-0` o `0-1`
- En curso: `*`

```python
game.getPgn({"Event": "Torneo", "White": "Alice", "Black": "Bob"})
```

### Consultas de Relojes

| Metodo | Parametros | Retorno | Descripcion |
|--------|------------|---------|-------------|
| `getTime(color)` | `'w'` o `'b'` | `int` | Tiempo restante en ms |
| `getText(color)` | `'w'` o `'b'` | `str` | Tiempo en formato `'MM:SS'` |
| `getSeconds(color)` | `'w'` o `'b'` | `int` | Tiempo restante en segundos (floor) |

```python
game.getTime('w')     # 300000 (ms)
game.getText('w')     # '5:00'
game.getSeconds('w')  # 300
```

## Callbacks

### Callbacks propios de ChessGame

#### `onTimeout`

Se dispara cuando un reloj llega a 0.

```python
game.onTimeout = lambda color: print("Timeout:", color)
# color: 'w' o 'b' (quien se quedo sin tiempo)
```

#### `onDraw`

Se dispara cuando la partida termina en tablas (regla 50 movimientos o material insuficiente).

```python
game.onDraw = lambda: print("Tablas!")
```

#### `onGameOver`

Se dispara cuando la partida termina por cualquier razon.

```python
game.onGameOver = lambda reason, winner: print(reason, winner)
# reason: 'checkmate', 'stalemate', 'draw', 'timeout'
# winner: 'w', 'b', o None (en caso de tablas/stalemate)
```

### Orden de disparo de callbacks

En una situacion de fin de partida:
1. Primero el callback especifico: `onDraw()` o `onTimeout(color)`.
2. Luego siempre `onGameOver(reason, winner)`.

### Callbacks delegados de Chess

ChessGame expone los callbacks de posicion de Chess como propiedades delegadas:

| Propiedad | Descripcion |
|-----------|-------------|
| `onCheck` | Cuando el jugador en turno queda en jaque |
| `onCheckmate` | Cuando hay jaque mate |
| `onStalemate` | Cuando hay ahogado |

```python
game.onCheck = lambda: print("Jaque!")
game.onCheckmate = lambda: print("Jaque mate!")
game.onStalemate = lambda: print("Ahogado!")
```

## Uso Basico

### Partida con Fischer increment

```python
from modules.chessgame import ChessGame

game = ChessGame()

# Registrar callbacks
game.onGameOver = lambda reason, winner: print(f"Game over: {reason}, winner: {winner}")
game.onTimeout = lambda color: print(f"Timeout: {color}")

# Iniciar partida: 5 min + 3 seg increment
game.start(300000, 3000)

# Jugar
game.play('e2-e4')    # reloj blanco pausa + 3s, reloj negro resume
game.play('e7-e5')    # reloj negro pausa + 3s, reloj blanco resume

# Consultar estado
game.getTurn()                # 'w'
game.getLegalMoves('g1')      # ['g1-f3', 'g1-h3']
game.getBoard()               # lista de 64 caracteres
game.getHistory()             # [('e2-e4', 'e7-e5')]
game.getCapturedPieces()      # {"w": "", "b": ""}
game.getText('w')             # '5:01' (aprox)
```

### Partida con posicion custom

```python
game = ChessGame()
game.setFen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1")
game.start(600000)  # 10 min sin increment

game.play('O-O')    # Enroque corto blancas
```

### Undo

```python
game = ChessGame()
game.start(300000)

game.play('e2-e4')
game.play('e7-e5')

# Deshacer (restaura tablero y tiempos)
game.undo()
game.getTurn()         # 'b' (vuelve al turno de negras)
```

### Reiniciar para nueva partida

```python
game.reset()                    # Todo a estado inicial
game.start(180000, 2000)        # Nueva partida: 3 min + 2 seg
```

### Integracion con ChessDisplay

```python
from modules.chessgame import ChessGame
from modules.chessdisplay import ChessDisplay

game = ChessGame()
display = ChessDisplay(sda=21, scl=22)

game.start(300000)

# Render posicion inicial
display.setTable(game.getBoard())
display.render()

# Jugar y actualizar display
game.play('e2-e4')
display.setTable(game.getBoard())
display.render()
```

## Deteccion de Timeout

ChessClock usa evaluacion lazy: el timeout se detecta al consultar `getTime()`, `pause()`, o similares. Para detectar timeout sin interaccion del usuario, un controlador de UI externo debe hacer polling periodico:

```python
# En un loop de UI
remaining = game.getTime('w')  # Esto puede disparar onTimeout
remaining = game.getTime('b')
```

## Estructura de Archivos

```
modules/
  CHESSGAME_REQUIREMENTS.md     # Documento de requerimientos
  chessgame/
    __init__.py                  # Exporta ChessGame
    ChessGame.py                 # Clase principal

tests/
  modules/
    chessgame/
      test_chessgame.py          # Tests de ChessGame
```

## Pruebas

```bash
uv run pytest tests/modules/chessgame
```

Las pruebas cubren:
- Creacion de instancia y estado inicial
- `start()` con/sin Fischer increment
- `play()` con movimientos validos, invalidos y game over
- Fischer increment aplicado correctamente
- Gestion de relojes (pausa/resume)
- `undo()` con restauracion completa (tablero, tiempos, historial, capturas)
- `reset()` reinicia todo
- `isDraw()` (regla 50 movimientos, material insuficiente)
- `isGameOver()` y checkmate
- Timeout via polling de relojes
- `setFen()` antes de `start()` para posicion custom
- Delegacion de metodos a Chess
- Historial y piezas capturadas
- Consultas de relojes (`getTime`, `getText`, `getSeconds`)
- `getPgn()` con resultado automatico y cabeceras
- Callbacks propios (`onTimeout`, `onDraw`, `onGameOver`) y delegados (`onCheck`, `onCheckmate`, `onStalemate`)
- FEN roundtrip (`getFen`/`setFen`)
- Edge cases (multiples start, undo despues de game over, promocion y enroque en historial)

## Notas Tecnicas

- ChessGame no expone directamente las instancias de Chess ni ChessClock
- Undo usa FEN para snapshot/restore (evita acoplar ChessGame a internos de Chess)
- Fischer increment se aplica SOLO al jugador que acaba de mover
- Siempre se requiere reloj (para "sin limite" usar un `timeBase` alto)
- `isDraw()` usa API publica de Chess para evaluar la regla de 50 movimientos
- Optimizado para uso de memoria en ESP32
- Compatible con MicroPython

## Version

1.1 - Febrero 2026
