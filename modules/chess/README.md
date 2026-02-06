# Modulo Chess para ESP32 (MicroPython)

Motor puro de reglas de ajedrez. Valida y ejecuta movimientos, detecta jaque/mate/ahogado y material insuficiente. Optimizado para entornos con recursos limitados como ESP32.

> **v2.1**: Chess mantiene su rol de motor puro y expone utilidades de estado (`getHalfmoveClock`, `getLastPositionState`) para integracion eficiente con un orquestador externo.

## Caracteristicas

- Validacion completa de movimientos para todas las piezas
- Movimientos especiales: enroque, promocion de peon, captura al paso (en passant)
- Deteccion de jaque, jaque mate y ahogado
- Deteccion de material insuficiente
- Soporte para notacion FEN (6 campos standard)
- Estado util para orquestadores: `getHalfmoveClock()`, `getLastPositionState()`
- Callback `onMove` con detalles de cada movimiento ejecutado
- Callbacks de posicion: `onCheck`, `onCheckmate`, `onStalemate`

## Instalacion

Para MicroPython en ESP32, copia el paquete a `lib/chess`:

```python
from modules.chess import Chess
```

## API Publica

### Constructor

```python
chess = Chess(debug=False)
```

| Parametro | Tipo | Descripcion |
|-----------|------|-------------|
| `debug` | `bool` | Activa modo debug para mensajes de diagnostico. Default: `False` |

### Metodos Principales

#### `play(move) -> bool`
Valida y ejecuta un movimiento. Retorna True si exitoso, False si invalido. Dispara callbacks.

```python
chess = Chess()
chess.play('e2-e4')   # True
chess.play('e7-e5')   # True
chess.play('g1-f3')   # True
chess.play('invalid') # False
```

**Formato de movimientos:**
- Movimiento normal: `e2-e4`
- Captura: `e4-d5`
- Promocion: `e7-e8=Q` (Q, R, B, N)
- Enroque corto: `O-O`
- Enroque largo: `O-O-O`
- En passant: `e5-d6`

#### `getLegalMoves(square) -> list`
Retorna lista de movimientos legales para la pieza en la casilla indicada.

```python
chess = Chess()
moves = chess.getLegalMoves('e2')
print(moves)  # ['e2-e3', 'e2-e4']

moves = chess.getLegalMoves('g1')
print(moves)  # ['g1-f3', 'g1-h3']

# Con promocion disponible
chess.setFen('8/P7/8/8/8/8/8/4K2k w - - 0 1')
moves = chess.getLegalMoves('a7')
print(moves)  # ['a7-a8=Q', 'a7-a8=R', 'a7-a8=B', 'a7-a8=N']

# Con enroque disponible
chess.setFen('r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1')
moves = chess.getLegalMoves('e1')
print(moves)  # ['e1-d1', 'e1-f1', 'O-O', 'O-O-O']
```

#### `getPiece(square) -> str`
Retorna la pieza en la casilla especificada.

```python
chess = Chess()
print(chess.getPiece('e1'))  # 'K' (Rey blanco)
print(chess.getPiece('e8'))  # 'k' (Rey negro)
print(chess.getPiece('e4'))  # ' ' (Casilla vacia)
```

**Notacion de piezas:**
- Mayusculas: piezas blancas (P, N, B, R, Q, K)
- Minusculas: piezas negras (p, n, b, r, q, k)
- Espacio: casilla vacia

#### `getBoard() -> str`
Retorna la representacion del tablero como cadena de 64 caracteres.

```python
chess = Chess()
board = chess.getBoard()
print(board[0])   # 'R' (a1)
print(board[4])   # 'K' (e1)
print(board[56])  # 'r' (a8)
print(board[60])  # 'k' (e8)
```

Indice 0 = a1, indice 63 = h8. Formato consistente para integracion con display.

#### `reset()`
Reinicia el tablero a la posicion inicial.

```python
chess = Chess()
chess.play('e2-e4')
chess.play('e7-e5')
chess.reset()
print(chess.getTurn())  # 'w'
print(chess.getFen())   # posicion inicial
```

### Metodos de Estado

#### `getTurn() -> str`
Retorna el jugador en turno: `'w'` o `'b'`.

```python
chess = Chess()
print(chess.getTurn())  # 'w'
chess.play('e2-e4')
print(chess.getTurn())  # 'b'
```

#### `getHalfmoveClock() -> int`
Retorna el contador de medio-movimientos (campo 5 de FEN).

```python
chess = Chess()
print(chess.getHalfmoveClock())  # 0
chess.play('g1-f3')
print(chess.getHalfmoveClock())  # 1
```

#### `getLastPositionState() -> str`
Retorna el ultimo estado de posicion evaluado tras `play()`.

Valores posibles: `'normal'`, `'check'`, `'checkmate'`, `'stalemate'`.

#### `isCheck() -> bool`
Indica si el jugador en turno esta en jaque.

```python
chess = Chess()
chess.setFen('4k3/8/5N2/8/8/8/8/4K3 b - - 0 1')
print(chess.isCheck())  # True
```

#### `isCheckmate() -> bool`
Indica si hay jaque mate.

```python
chess = Chess()
chess.play('e2-e4'); chess.play('e7-e5')
chess.play('f1-c4'); chess.play('b8-c6')
chess.play('d1-h5'); chess.play('g8-f6')
chess.play('h5-f7')
print(chess.isCheckmate())  # True
```

#### `isStalemate() -> bool`
Indica si hay ahogado (stalemate).

```python
chess = Chess()
chess.setFen('k7/8/1Q6/8/8/8/8/4K3 b - - 0 1')
print(chess.isStalemate())  # True
print(chess.isCheck())       # False
```

#### `isInsufficientMaterial() -> bool`
Indica si hay material insuficiente para dar mate.

Evalua: K vs K, K vs K+B, K vs K+N, K+B vs K+B (alfiles del mismo color de casilla).

```python
chess = Chess()
chess.setFen('4k3/8/8/8/8/8/8/4K3 w - - 0 1')
print(chess.isInsufficientMaterial())  # True (K vs K)

chess.setFen('4k3/8/8/8/8/8/8/4KB2 w - - 0 1')
print(chess.isInsufficientMaterial())  # True (K vs K+B)
```

### Metodos FEN

#### `setFen(fen)`
Carga una posicion desde notacion FEN (4 a 6 campos standard).

```python
chess = Chess()
chess.setFen('r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4')
print(chess.getPiece('c4'))  # 'B'
print(chess.getTurn())       # 'w'
```

#### `getFen() -> str`
Exporta la posicion actual a notacion FEN completa (6 campos).

```python
chess = Chess()
print(chess.getFen())
# 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

chess.play('e2-e4')
print(chess.getFen())
# 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1'
```

### Callbacks

Los callbacks se ejecutan automaticamente despues de cada llamada a `play()` exitosa.

#### `onMove`
Se dispara despues de cada movimiento valido con detalles.

```python
def mi_handler(moveStr, captured, isPromotion, isCastling, isEnPassant):
    print("Movimiento:", moveStr)
    if captured:
        print("Captura:", captured)

chess = Chess()
chess.onMove = mi_handler
chess.play('e2-e4')
# Movimiento: e2-e4
```

| Parametro | Tipo | Descripcion |
|-----------|------|-------------|
| `moveStr` | `str` | Movimiento ejecutado (ej: `'e2-e4'`, `'O-O'`) |
| `captured` | `str` o `None` | Pieza capturada o None |
| `isPromotion` | `bool` | True si fue promocion |
| `isCastling` | `bool` | True si fue enroque |
| `isEnPassant` | `bool` | True si fue captura al paso |

#### Callbacks de posicion

```python
chess.onCheck = lambda: print("Jaque!")
chess.onCheckmate = lambda: print("Jaque mate!")
chess.onStalemate = lambda: print("Ahogado!")
```

| Callback | Cuando se ejecuta |
|----------|-------------------|
| `onCheck` | Cuando el jugador en turno queda en jaque |
| `onCheckmate` | Cuando hay jaque mate |
| `onStalemate` | Cuando hay ahogado |

**Orden de disparo**: `onMove` primero, luego el callback de posicion correspondiente.

### Representacion del Tablero

```python
chess = Chess()
print(chess)
```

```
  +---+---+---+---+---+---+---+---+
8 | r | n | b | q | k | b | n | r |
  +---+---+---+---+---+---+---+---+
7 | p | p | p | p | p | p | p | p |
  +---+---+---+---+---+---+---+---+
6 |   |   |   |   |   |   |   |   |
  +---+---+---+---+---+---+---+---+
5 |   |   |   |   |   |   |   |   |
  +---+---+---+---+---+---+---+---+
4 |   |   |   |   |   |   |   |   |
  +---+---+---+---+---+---+---+---+
3 |   |   |   |   |   |   |   |   |
  +---+---+---+---+---+---+---+---+
2 | P | P | P | P | P | P | P | P |
  +---+---+---+---+---+---+---+---+
1 | R | N | B | Q | K | B | N | R |
  +---+---+---+---+---+---+---+---+
    a   b   c   d   e   f   g   h

Turn: White
FEN: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
```

## Ejemplo Completo

```python
from modules.chess import Chess

chess = Chess()

# Registrar callbacks
chess.onMove = lambda move, cap, prom, castle, ep: print("Move:", move)
chess.onCheck = lambda: print("Check!")
chess.onCheckmate = lambda: print("Checkmate!")

# Motor de reglas puro
chess.play('e2-e4')          # True, dispara onMove
chess.getLegalMoves('d7')    # ['d7-d6', 'd7-d5']
chess.getTurn()              # 'b'
chess.isCheck()              # False
chess.getPiece('e4')         # 'P'
chess.getBoard()             # cadena de 64 caracteres
chess.getFen()               # FEN completo con 6 campos

# Material insuficiente
chess.setFen("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
chess.isInsufficientMaterial()  # True (K vs K)
```

> **Nota**: Para historial, undo, piezas capturadas, PGN, deteccion de fin de partida y relojes, usar un orquestador externo.

## Pruebas

```bash
uv run pytest tests/modules/chess
```

Las pruebas cubren:
- Movimientos basicos de todas las piezas
- Movimientos especiales (enroque, promocion, en passant)
- Deteccion de jaque y jaque mate
- Deteccion de ahogado y material insuficiente
- Funcionalidad FEN, getBoard y callbacks (onMove, onCheck, etc.)

## Notas Tecnicas

- Representacion interna: lista mutable de 64 chars; API publica `getBoard()` retorna cadena de 64 caracteres
- `halfmoveClock` y `fullmoveNumber` se mantienen internamente como parte del estado FEN
- Optimizado para uso de memoria en ESP32
- Compatible con MicroPython

## Version

2.1 - Febrero 2026
