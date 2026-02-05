# ChessDisplay

Modulo de visualizacion de ajedrez para pantalla OLED SSD1306 128x64 pixels conectada por I2C. Renderiza el estado de una partida de ajedrez con piezas en pixel art 8x8 y un panel informativo lateral.

**Este modulo es exclusivamente de renderizado.** No maneja entrada de usuario (botones, encoder, etc.) ni logica de juego.

## Requisitos

- ESP32 con MicroPython
- Pantalla OLED SSD1306 128x64, conexion I2C
- Libreria `ssd1306` de MicroPython
- Modulo `Chess` del proyecto

## Distribucion de Pantalla

```
|<--- 64px --->|<--- 64px --->|
+==============+==============+
|              |  Turn: W     |
|   Tablero    |  Mov:   1    |
|   8x8        |  e2-e4       |
|   pixel art  |              |
|              |  CHECK!      |
|              |  Capt:       |
|              |  qrpp        |
|              |  BN          |
+==============+==============+
```

- **Zona izquierda (64x64)**: Tablero de ajedrez con casillas de 8x8 pixels y piezas en pixel art
- **Zona derecha (64x64)**: Panel informativo con turno, movimiento, estado y capturas

## API

### Constructor

```python
ChessDisplay(chess, sda, scl, flipped=False, address=0x3C, i2cId=0)
```

| Parametro | Tipo | Default | Descripcion |
|-----------|------|---------|-------------|
| `chess` | `Chess` | (requerido) | Instancia del modulo Chess |
| `sda` | `int` | (requerido) | Pin GPIO para SDA |
| `scl` | `int` | (requerido) | Pin GPIO para SCL |
| `flipped` | `bool` | `False` | `False` = blancas abajo, `True` = negras abajo |
| `address` | `int` | `0x3C` | Direccion I2C del SSD1306 |
| `i2cId` | `int` | `0` | Bus I2C a usar |

### Metodos

| Metodo | Descripcion |
|--------|-------------|
| `render()` | Dibuja el estado completo (tablero + panel) y envia a pantalla |
| `flip()` | Invierte la orientacion del tablero (toggle). No actualiza la pantalla |

### Propiedades

| Propiedad | Tipo | Lectura | Escritura | Descripcion |
|-----------|------|---------|-----------|-------------|
| `flipped` | `bool` | Si | Si | Orientacion actual del tablero |

## Uso Basico

```python
from modules.chess import Chess
from modules.chessdisplay import ChessDisplay

# Crear partida y display
chess = Chess()
display = ChessDisplay(chess, sda=21, scl=22)

# Renderizar posicion inicial
display.render()

# Jugar y actualizar
chess.play("e2-e4")
display.render()

chess.play("e7-e5")
display.render()
```

## Orientacion del Tablero

```python
# Blancas abajo (default)
display = ChessDisplay(chess, sda=21, scl=22)
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

## Parametros Avanzados

```python
# Display con direccion I2C diferente y bus I2C 1
display = ChessDisplay(
    chess,
    sda=21,
    scl=22,
    flipped=True,
    address=0x3D,
    i2cId=1
)
display.render()
```

## Panel Informativo

El panel derecho muestra (8 caracteres por linea, 8 lineas):

| Linea | Contenido | Ejemplo |
|-------|-----------|---------|
| 0 | Turno actual | `Turn: W` o `Turn: B` |
| 1 | Numero de movimiento | `Mov:   1` |
| 2 | Ultimo movimiento | `e2-e4` o `O-O` |
| 3 | (separador) | |
| 4 | Estado de partida | `CHECK!`, `MATE!`, `DRAW`, `STALE` |
| 5 | Etiqueta capturas | `Capt:` |
| 6 | Capturadas por blancas | `qrpp` (piezas negras capturadas) |
| 7 | Capturadas por negras | `BN` (piezas blancas capturadas) |

Las piezas capturadas se muestran ordenadas por valor (dama > torre > alfil > caballo > peon). Si exceden 8 caracteres, se truncan mostrando las de mayor valor.

## Diferenciacion Visual de Piezas

En pantalla monocromatica, las piezas blancas y negras se distinguen mediante:

- **Piezas blancas**: Silueta rellena (bitmap completo)
- **Piezas negras**: Silueta de contorno (solo borde del bitmap)

En casillas oscuras, los colores se invierten automaticamente mediante la tecnica de dibujo inverso, manteniendo la distincion entre ambos colores de piezas.

## Salida Esperada

### Posicion Inicial

```
Tablero izquierdo: Patron ajedrezado con piezas negras arriba y blancas abajo
Panel derecho:     Turn: W | Mov:   1 | (sin ultimo movimiento ni capturas)
```

### Despues de 1.e4

```
Tablero: Peon blanco ahora en e4 en lugar de e2
Panel:   Turn: B | Mov:   1 | e2-e4
```

### Jaque Mate del Pastor

```
Tablero: Posicion de mate con dama blanca en f7
Panel:   Turn: B | Mov:   4 | h5-f7 | MATE! | Capt: | p
```

### Tablero Girado (flipped=True)

```
Tablero: Piezas negras abajo, blancas arriba, columna 'h' a la izquierda
Panel:   (mismo contenido informativo)
```

## Dependencia: getCapturedPieces()

Este modulo requiere el metodo `getCapturedPieces()` en el modulo `Chess`, que fue agregado como prerequisito:

```python
chess = Chess()
chess.play("e2-e4")
chess.play("d7-d5")
chess.play("e4-d5")  # Blancas capturan peon negro

captured = chess.getCapturedPieces()
# {"w": "p", "b": ""}
# "w" = piezas capturadas por blancas (piezas negras, minusculas)
# "b" = piezas capturadas por negras (piezas blancas, mayusculas)
```

## Estructura de Archivos

```
modules/
  chessdisplay/
    __init__.py          # Exporta ChessDisplay
    ChessDisplay.py      # Clase principal
    README.md            # Este documento

tests/
  modules/
    chessdisplay/
      test_chess_display.py  # Tests con mocks de hardware
```
