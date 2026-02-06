# Modulo ChessGame para ESP32 (MicroPython)

Coordinador que compone `Chess` (motor de reglas) y dos `ChessClock` (uno por color) para ofrecer una API unica de partida con reloj. Es parte del core: no maneja hardware, display ni red.

## Caracteristicas

- Coordina chess + 2 relojes en una sola API
- Cambio de reloj automatico al aceptar jugadas
- Undo/redo consistentes entre tablero y reloj
- Callbacks para eventos de partida
- Polling lazy via `update()` para deteccion de timeout
- Optimizado para ESP32 (sin threads)

## Instalacion

```python
from modules.chessgame import ChessGame
```

## Dependencias

- `modules/chess/Chess.py`
- `modules/chessclock/ChessClock.py`

## API Publica

### Constructor

```python
game = ChessGame(chess=None, whiteClock=None, blackClock=None, debug=False)
```

| Parametro | Tipo | Descripcion |
|-----------|------|-------------|
| `chess` | `Chess` | Instancia opcional. Si None, crea una |
| `whiteClock` | `ChessClock` | Instancia opcional. Si None, crea una |
| `blackClock` | `ChessClock` | Instancia opcional. Si None, crea una |
| `debug` | `bool` | Modo debug. Default: `False` |

### Acceso a Componentes

#### `getChess() -> Chess`

Retorna la instancia Chess interna.

#### `getWhiteClock() -> ChessClock`

Retorna el reloj de blancas (para diagnostico; UI deberia usar `getTime()`).

#### `getBlackClock() -> ChessClock`

Retorna el reloj de negras (idem).

### Nueva Partida

#### `start(baseW, baseB=None) -> True`

Inicia una nueva partida con reloj.

```python
game.start(300000)          # 5 min para ambos
game.start(300000, 180000)  # 5 min blancas, 3 min negras
```

| Parametro | Tipo | Descripcion |
|-----------|------|-------------|
| `baseW` | `int` | Tiempo base para blancas (ms) |
| `baseB` | `int` | Tiempo base para negras (ms). Si None, usa `baseW` |

Comportamiento:
1. Resetea chess a posicion inicial
2. Resetea ambos clocks con `baseW` / `baseB`
3. Arranca el clock del turno inicial (blancas)
4. Limpia stacks de undo/redo

### Tiempo

#### `getTime(color) -> int`

Retorna el tiempo restante del color indicado (ms).

```python
print(game.getTime('w'))  # 284321
print(game.getTime('b'))  # 300000
```

#### `getActiveColor() -> str`

Retorna el color del turno actual (`'w'` o `'b'`).

```python
print(game.getActiveColor())  # 'w'
```

### Update (Polling)

#### `update() -> True`

Sincroniza el clock del color activo (lazy sync). Un loop externo debe llamar este metodo periodicamente (recomendado cada 250ms) para detectar timeout.

```python
# Loop de UI/Display
while True:
    game.update()
    # ... renderizar ...
    time.sleep_ms(250)
```

### Pausa

#### `pause() -> True`

Pausa ambos clocks.

```python
game.pause()
```

#### `resume() -> True`

Reanuda solo el clock del color activo. Si hay timeout, es no-op.

```python
game.resume()
```

### Movimiento

#### `confirmMove(moveStr) -> bool`

Confirma una jugada y coordina reloj.

```python
ok = game.confirmMove('e2-e4')
if ok:
    print('Movimiento aceptado')
else:
    print('Movimiento ilegal')
```

Flujo interno:
1. Determina el color que mueve (`chess.getTurn()`)
2. Ejecuta `chess.play(moveStr)`
3. Si es legal: pausa el clock del que movio, reanuda el del rival (si estaba corriendo), guarda snapshot
4. Si es ilegal: no cambia clocks ni stacks

No bloquea movimientos por timeout; el controlador externo decide.

### Undo/Redo

#### `undo() -> bool`

Deshace el ultimo movimiento y restaura estado del reloj.

```python
game.confirmMove('e2-e4')
game.confirmMove('e7-e5')

game.undo()  # Deshace e7-e5, restaura tiempos
game.undo()  # Deshace e2-e4, restaura tiempos
game.undo()  # False (no hay mas movimientos)
```

#### `redo() -> bool`

Rehace el ultimo movimiento deshecho y restaura el reloj.

```python
game.undo()   # Deshace ultimo movimiento
game.redo()   # Lo rehace con los mismos tiempos
game.redo()   # False (no hay mas en redo)
```

Si despues de `undo()` se confirma un movimiento nuevo, el stack redo se vacia.

### Callbacks

```python
game = ChessGame()

game.onMoveAccepted = lambda moveStr: print("Aceptado:", moveStr)
game.onMoveRejected = lambda moveStr: print("Rechazado:", moveStr)
game.onUndo = lambda moveStr: print("Undo:", moveStr)
game.onRedo = lambda moveStr: print("Redo:", moveStr)
game.onTimeout = lambda color: print("Timeout:", color)
game.onStateChanged = lambda: print("Estado cambio")
```

| Callback | Firma | Cuando se ejecuta |
|----------|-------|-------------------|
| `onMoveAccepted` | `(moveStr)` | Jugada legal aceptada |
| `onMoveRejected` | `(moveStr)` | Jugada ilegal rechazada |
| `onUndo` | `(moveStr)` | Movimiento deshecho |
| `onRedo` | `(moveStr)` | Movimiento rehecho |
| `onTimeout` | `(color)` | Reloj llega a 0 (`'w'` o `'b'`) |
| `onStateChanged` | `()` | Cualquier cambio observable |

`ChessGame` NO reemplaza callbacks de `Chess` (check/mate/draw). Pueden usarse en paralelo:

```python
game.getChess().onCheckmate = lambda: print("Checkmate!")
```

---

## Ejemplos

### Partida basica

```python
from modules.chessgame import ChessGame

game = ChessGame()
game.start(300000)  # 5 min

game.confirmMove('e2-e4')  # True, cambia reloj a negras
game.confirmMove('e7-e5')  # True, cambia reloj a blancas

print(game.getTime('w'))         # Tiempo restante blancas
print(game.getTime('b'))         # Tiempo restante negras
print(game.getActiveColor())     # 'w'
```

### Polling con update

```python
from modules.chessgame import ChessGame
import time

game = ChessGame()
game.onTimeout = lambda color: print("Pierde por tiempo:", color)
game.start(60000)  # 1 minuto

while True:
    game.update()  # Sincroniza clock activo, detecta timeout
    # ... leer input, renderizar ...
    time.sleep_ms(250)
```

### Undo/Redo

```python
from modules.chessgame import ChessGame

game = ChessGame()
game.start(300000)

game.confirmMove('e2-e4')
game.confirmMove('e7-e5')
game.confirmMove('g1-f3')

# Deshacer ultimos 2 movimientos
game.undo()  # Deshace g1-f3
game.undo()  # Deshace e7-e5

# Rehacer uno
game.redo()  # Rehace e7-e5

# Un nuevo movimiento limpia el redo
game.confirmMove('d2-d4')
game.redo()  # False (redo vacio)
```

### Pausa/Resume

```python
from modules.chessgame import ChessGame

game = ChessGame()
game.start(300000)

game.confirmMove('e2-e4')

# Pausar partida
game.pause()  # Ambos clocks pausados

# Reanudar
game.resume()  # Solo reanuda el clock del turno activo (negras)
```

### Con inyeccion de dependencias

```python
from modules.chess import Chess
from modules.chessclock import ChessClock
from modules.chessgame import ChessGame

chess = Chess()
wClock = ChessClock(debug=True)
bClock = ChessClock(debug=True)

game = ChessGame(chess=chess, whiteClock=wClock, blackClock=bClock, debug=True)
game.start(300000)
```

---

## Contrato de Uso

- **Polling obligatorio**: un loop externo debe llamar `game.update()` periodicamente (cada 250ms) para detectar timeout. Sin polling, el timeout solo se detecta al interactuar.
- **Tiempo via ChessGame**: UI debe obtener tiempos con `game.getTime(color)`, no directamente desde los clocks.
- **Timeout no bloquea**: `confirmMove()` no rechaza movimientos por timeout. El controlador externo decide la politica.

## Notas

- Unidad estandar: milisegundos (int)
- Colores: `'w'` (blancas), `'b'` (negras)
- Compatible con MicroPython para ESP32
- Sin threads, sin timers (lazy sync)
- Callbacks de `Chess` (check/mate/draw) siguen funcionando independientemente
