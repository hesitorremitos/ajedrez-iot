# Modulo Chess para ESP32 (MicroPython)

Modulo de ajedrez que valida movimientos y gestiona el estado de una partida. Optimizado para entornos con recursos limitados como ESP32.

## Caracteristicas

- Validacion completa de movimientos para todas las piezas
- Movimientos especiales: enroque, promocion de peon, captura al paso (en passant)
- Deteccion de jaque, jaque mate y ahogado
- Deteccion de tablas por material insuficiente y regla de 50 movimientos
- Soporte para notacion FEN y PGN
- Sistema de callbacks para eventos del juego
- Funcion de deshacer movimientos (undo)
- Historial de partida

## Instalacion

Para MicroPython en ESP32, copia el paquete a `lib/chess`:

```python
from chess import Chess
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

#### `play(move: str) -> bool`
Ejecuta un movimiento en notacion algebraica.

```python
chess = Chess()
chess.play('e2-e4')   # Retorna: True
chess.play('e7-e5')   # Retorna: True
chess.play('g1-f3')   # Retorna: True
chess.play('invalid') # Retorna: False
```

**Formato de movimientos:**
- Movimiento normal: `e2-e4`
- Captura: `e4-d5`
- Promocion: `e7-e8=Q` (Q, R, B, N)
- Enroque corto: `O-O`
- Enroque largo: `O-O-O`
- En passant: `e5-d6`

#### `getLegalMoves(square: str) -> list[str]`
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

#### `getPiece(square: str) -> str`
Retorna la pieza en la casilla especificada.

```python
chess = Chess()
print(chess.getPiece('e1'))  # 'K' (Rey blanco)
print(chess.getPiece('e8'))  # 'k' (Rey negro)
print(chess.getPiece('e4'))  # ' ' (Casilla vacia)
print(chess.getPiece('a2'))  # 'P' (Peon blanco)
print(chess.getPiece('a7'))  # 'p' (Peon negro)
```

**Notacion de piezas:**
- Mayusculas: piezas blancas (P, N, B, R, Q, K)
- Minusculas: piezas negras (p, n, b, r, q, k)
- Espacio: casilla vacia

#### `undo() -> bool`
Deshace el ultimo movimiento realizado.

```python
chess = Chess()
chess.play('e2-e4')
print(chess.getPiece('e4'))  # 'P'

chess.undo()
print(chess.getPiece('e4'))  # ' '
print(chess.getPiece('e2'))  # 'P'
```

#### `reset()`
Reinicia la partida a la posicion inicial.

```python
chess = Chess()
chess.play('e2-e4')
chess.play('e7-e5')
chess.reset()
print(chess.getTurn())  # 'w'
print(chess.getHistory())  # []
```

### Metodos de Estado

#### `getTurn() -> str`
Retorna el jugador en turno.

```python
chess = Chess()
print(chess.getTurn())  # 'w'
chess.play('e2-e4')
print(chess.getTurn())  # 'b'
```

#### `isCheck() -> bool`
Indica si el jugador en turno esta en jaque.

```python
chess = Chess()
chess.setFen('4k3/8/5N2/8/8/8/8/4K3 b - - 0 1')
print(chess.isCheck())  # True (caballo en f6 da jaque al rey negro)
```

#### `isCheckmate() -> bool`
Indica si hay jaque mate.

```python
# Mate del pastor
chess = Chess()
chess.play('e2-e4')
chess.play('e7-e5')
chess.play('f1-c4')
chess.play('b8-c6')
chess.play('d1-h5')
chess.play('g8-f6')
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

> QUITAR METODO
#### `isDraw() -> bool`
Indica si hay tablas (regla 50 movimientos o material insuficiente).

```python
# Material insuficiente (K vs K)
chess = Chess()
chess.setFen('4k3/8/8/8/8/8/8/4K3 w - - 0 1')
print(chess.isDraw())  # True

# Material insuficiente (K vs K+B)
chess.setFen('4k3/8/8/8/8/8/8/4KB2 w - - 0 1')
print(chess.isDraw())  # True

# Regla de 50 movimientos
chess.setFen('4k3/8/8/8/8/8/8/4KR2 w - - 99 50')
chess.play('f1-f2')
print(chess.isDraw())  # True
```

#### `isGameOver() -> bool`
Indica si la partida ha terminado.

```python
chess = Chess()
print(chess.isGameOver())  # False

# Despues de mate
chess.setFen('k7/RR6/8/8/8/8/8/4K3 b - - 0 1')
print(chess.isGameOver())  # True (jaque mate)
```

### Metodos FEN/PGN

#### `setFen(fen: str)`
Carga una posicion desde notacion FEN.

```python
chess = Chess()
chess.setFen('r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4')
print(chess.getPiece('c4'))  # 'B'
print(chess.getTurn())       # 'w'
```

#### `getFen() -> str`
Exporta la posicion actual a notacion FEN.

```python
chess = Chess()
print(chess.getFen())
# 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

chess.play('e2-e4')
print(chess.getFen())
# 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1'
```

#### `getPgn(headers: dict = None) -> str`
Exporta la partida completa a formato PGN.

```python
chess = Chess()
chess.play('e2-e4')
chess.play('e7-e5')
chess.play('g1-f3')
chess.play('b8-c6')

pgn = chess.getPgn({'Event': 'Partida de ejemplo', 'White': 'Jugador1', 'Black': 'Jugador2'})
print(pgn)
# [Event "Partida de ejemplo"]
# [Site "?"]
# [Date "????.??.??"]
# [Round "?"]
# [White "Jugador1"]
# [Black "Jugador2"]
# [Result "*"]
#
# 1. e2-e4 e7-e5 2. g1-f3 b8-c6 *
```

#### `getHistory() -> list[tuple]`
Retorna historial de movimientos en tuplas por turno.

```python
chess = Chess()
chess.play('e2-e4')
chess.play('e7-e5')
chess.play('g1-f3')
chess.play('b8-c6')

print(chess.getHistory())
# [('e2-e4', 'e7-e5'), ('g1-f3', 'b8-c6')]

# Turno incompleto
chess.play('f1-c4')
print(chess.getHistory())
# [('e2-e4', 'e7-e5'), ('g1-f3', 'b8-c6'), ('f1-c4', '')]
```

### Callbacks

Los callbacks se ejecutan automaticamente despues de cada llamada a `play()` cuando corresponda.

```python
chess = Chess()

def mi_callback_jaque():
    print("Jaque!")

def mi_callback_mate():
    print("Jaque mate!")

def mi_callback_ahogado():
    print("Ahogado!")

def mi_callback_tablas():
    print("Tablas!")

def mi_callback_fin():
    print("Partida terminada!")

chess.onCheck = mi_callback_jaque
chess.onCheckmate = mi_callback_mate
chess.onStalemate = mi_callback_ahogado
chess.onDraw = mi_callback_tablas
chess.onGameOver = mi_callback_fin
```

| Callback | Cuando se ejecuta |
|----------|-------------------|
| `onCheck` | Cuando el jugador en turno queda en jaque |
| `onCheckmate` | Cuando hay jaque mate |
| `onStalemate` | Cuando hay ahogado |
| `onDraw` | Cuando hay tablas |
| `onGameOver` | Cuando la partida termina (cualquier razon) |

### Representacion del Tablero

```python
chess = Chess()
print(chess)
```

Salida:
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

## Ejemplos Completos

### Partida Basica

```python
from Chess import Chess

chess = Chess()

# Apertura italiana
movimientos = ['e2-e4', 'e7-e5', 'g1-f3', 'b8-c6', 'f1-c4', 'f8-c5']

for mov in movimientos:
    if chess.play(mov):
        print(f"Movimiento {mov} ejecutado")
    else:
        print(f"Movimiento {mov} invalido")

print(chess)
print(f"FEN: {chess.getFen()}")
```

### Mate del Pastor

```python
from Chess import Chess

chess = Chess()

# Mate del pastor (Scholar's mate)
movimientos = ['e2-e4', 'e7-e5', 'f1-c4', 'b8-c6', 'd1-h5', 'g8-f6', 'h5-f7']

for mov in movimientos:
    chess.play(mov)

print(f"Jaque mate: {chess.isCheckmate()}")  # True
print(f"PGN: {chess.getPgn()}")
```

### Usando Callbacks

```python
from Chess import Chess

chess = Chess()

def alerta_jaque():
    print("ATENCION: Rey en jaque!")

def partida_terminada():
    if chess.isCheckmate():
        ganador = "Negras" if chess.getTurn() == 'w' else "Blancas"
        print(f"Jaque mate! Ganan las {ganador}")
    elif chess.isStalemate():
        print("Ahogado - Tablas")
    elif chess.isDraw():
        print("Tablas por material insuficiente o regla de 50 movimientos")

chess.onCheck = alerta_jaque
chess.onGameOver = partida_terminada

# Jugar partida...
```

### Deshacer Movimientos

```python
from Chess import Chess

chess = Chess()

chess.play('e2-e4')
chess.play('e7-e5')
chess.play('d2-d4')

print("Posicion actual:")
print(chess)

# Deshacer ultimo movimiento
chess.undo()
print("Despues de undo:")
print(chess)

# Deshacer todos los movimientos
while chess.undo():
    pass

print("Posicion inicial restaurada:")
print(chess.getFen())
```

## Pruebas

Las pruebas se ejecutan con pytest desde la raiz del proyecto:

```bash
pytest tests/modules/chess
```

Las pruebas cubren:
- Movimientos basicos de todas las piezas
- Movimientos especiales (enroque, promocion, en passant)
- Deteccion de jaque y jaque mate
- Deteccion de tablas y ahogado
- Funcionalidad FEN, PGN, historial y undo

## Notas Tecnicas

- Representacion interna del tablero: lista de 64 caracteres (indice 0 = a1, indice 63 = h8)
- Optimizado para uso de memoria en ESP32
- Compatible con MicroPython

## Version

1.0 - Enero 2025


notacion algebraica estandar
