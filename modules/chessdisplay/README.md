# ChessDisplay

Modulo de visualizacion de ajedrez para pantalla OLED SSD1306 128x64 pixels conectada por I2C. Renderiza un tablero de ajedrez con piezas en pixel art 8x8. Optimizado para ESP32 con MicroPython.

> **v2.0**: ChessDisplay ya no depende de Chess. Recibe los datos del tablero via `setTable()` como lista/cadena de 64 caracteres. El panel informativo se elimina temporalmente.

**Este modulo es exclusivamente de renderizado.** No maneja entrada de usuario, no tiene logica de juego, y no depende de ningun otro modulo del proyecto.

## Requisitos

- ESP32 con MicroPython
- Pantalla OLED SSD1306 128x64, conexion I2C
- Libreria `ssd1306` de MicroPython

## Distribucion de Pantalla

```
|<--- 64px --->|<--- 64px --->|
+==============+==============+
|              |              |
|   Tablero    |  (sin uso)   |
|   de ajedrez |              |
|              |              |
+==============+==============+
```

- **Zona izquierda (64x64)**: Tablero de ajedrez con casillas de 8x8 pixels y piezas en pixel art
- **Zona derecha (64x64)**: Sin uso temporalmente (pixels apagados)

## API

### Constructor

```python
ChessDisplay(sda, scl, flipped=False, address=0x3C, i2cId=0)
```

| Parametro | Tipo | Default | Descripcion |
|-----------|------|---------|-------------|
| `sda` | `int` | (requerido) | Pin GPIO para SDA |
| `scl` | `int` | (requerido) | Pin GPIO para SCL |
| `flipped` | `bool` | `False` | `False` = blancas abajo, `True` = negras abajo |
| `address` | `int` | `0x3C` | Direccion I2C del SSD1306 |
| `i2cId` | `int` | `0` | Bus I2C a usar |

### Metodos

| Metodo | Descripcion |
|--------|-------------|
| `setTable(board)` | Recibe datos del tablero como lista o cadena de 64 caracteres. Almacena internamente para el proximo render. **No llama a render automaticamente** |
| `render()` | Dibuja el tablero en la pantalla usando los datos del ultimo `setTable()`. Si no se ha llamado `setTable()`, dibuja tablero vacio |
| `flip()` | Invierte la orientacion del tablero (toggle). **No llama a render automaticamente** |

### Propiedades

| Propiedad | Tipo | Lectura | Escritura | Descripcion |
|-----------|------|---------|-----------|-------------|
| `flipped` | `bool` | Si | Si | Orientacion actual del tablero |

## Uso Basico

```python
from modules.chessdisplay import ChessDisplay
from modules.chessgame import ChessGame

# Crear display (sin dependencia a Chess)
display = ChessDisplay(sda=21, scl=22)

# Crear partida
game = ChessGame()
game.start(300000)

# Renderizar posicion inicial
display.setTable(game.getBoard())
display.render()

# Jugar y actualizar
game.play('e2-e4')
display.setTable(game.getBoard())
display.render()

# Girar tablero
display.flip()
display.render()
```

## setTable(board)

Recibe la representacion del tablero y la almacena internamente.

- `board`: lista de 64 caracteres o string de 64 caracteres.
  - Indice 0 = a1, indice 63 = h8.
  - Piezas blancas: `P, N, B, R, Q, K` (mayusculas).
  - Piezas negras: `p, n, b, r, q, k` (minusculas).
  - Casilla vacia: `' '` (espacio).

Este formato es compatible con `ChessGame.getBoard()` (que delega a `Chess.getBoard()`).

```python
# Usando datos de ChessGame
display.setTable(game.getBoard())

# Usando tablero custom directamente
customBoard = list(
    "RNBQKBNR"
    + "PPPPPPPP"
    + "        "
    + "        "
    + "        "
    + "        "
    + "pppppppp"
    + "rnbqkbnr"
)
display.setTable(customBoard)
display.render()
```

## Orientacion del Tablero

```python
# Blancas abajo (default)
display = ChessDisplay(sda=21, scl=22)
display.setTable(game.getBoard())
display.render()

# Girar tablero (negras abajo)
display.flip()
display.render()

# Verificar orientacion
print(display.flipped)  # True

# Asignar directamente
display.flipped = False
display.render()
```

## Diferenciacion Visual de Piezas

En pantalla monocromatica, las piezas blancas y negras se distinguen mediante:

- **Piezas blancas**: Silueta rellena (bitmap completo)
- **Piezas negras**: Silueta de contorno (solo borde del bitmap)

En casillas oscuras, los colores se invierten automaticamente mediante la tecnica de dibujo inverso, manteniendo la distincion entre ambos colores de piezas.

## Parametros Avanzados

```python
# Display con direccion I2C diferente y bus I2C 1
display = ChessDisplay(
    sda=21,
    scl=22,
    flipped=True,
    address=0x3D,
    i2cId=1
)
display.setTable(game.getBoard())
display.render()
```

## Estructura de Archivos

```
modules/
  chessdisplay/
    __init__.py          # Exporta ChessDisplay
    ChessDisplay.py      # Clase principal

tests/
  modules/
    chessdisplay/
      test_chess_display.py  # Tests con mocks de hardware
```

## Pruebas

```bash
uv run pytest tests/modules/chessdisplay
```

Las pruebas cubren:
- Creacion de instancia con mocks de hardware
- `setTable()` almacena datos sin llamar a render
- `render()` dibuja tablero con piezas
- `render()` sin `setTable()` dibuja tablero vacio
- Orientacion (flip) y propiedad `flipped`
- Patron ajedrezado correcto
- Diferenciacion visual entre piezas blancas y negras

## Notas Tecnicas

- Representacion interna del tablero: 64 caracteres (indice 0 = a1, indice 63 = h8)
- Cada pieza se almacena como bitmap de 8 bytes (48 bytes total para 6 piezas)
- Sin dependencia a Chess, ChessGame u otros modulos del proyecto
- Optimizado para uso de memoria en ESP32
- Compatible con MicroPython

## Version

2.0 - Febrero 2026
