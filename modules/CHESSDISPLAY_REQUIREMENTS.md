---
last_updated: "2026-02-06 12:00"
version: "2.0"
status: draft
author: Discovery Architect
---

# ChessDisplay Module - Documento de Requerimientos (v2.0)

> **Cambio mayor respecto a v1.0**: ChessDisplay ya no recibe una instancia de `Chess`. En su lugar, recibe los datos del tablero como una cadena/lista de 64 caracteres via `setTable()`. El panel informativo se elimina temporalmente. El modulo se convierte en un renderizador puro de tablero.

## Descripcion General

Modulo de visualizacion llamado `ChessDisplay.py` para ESP32 (MicroPython) que renderiza un tablero de ajedrez en una pantalla OLED SSD1306 de 128x64 pixels conectada por I2C. El modulo recibe datos del tablero como una cadena de 64 caracteres y dibuja las piezas en pixel art 8x8.

Este modulo es **exclusivamente de renderizado**. No maneja entrada de usuario, no tiene logica de juego, y no depende de ningun otro modulo del proyecto (Chess, ChessGame, etc.).

## Restricciones Tecnicas

- Compatible con MicroPython para ESP32.
- Optimizar uso de memoria RAM (~100KB disponibles en ESP32).
- camelCase para todos los nombres de metodos y propiedades.
- Ubicacion del archivo: `modules/chessdisplay/ChessDisplay.py`
- Nombre de la clase: `ChessDisplay`
- Pantalla: SSD1306 128x64 pixels, monocromatica, conexion I2C.
- Dependencia: libreria `ssd1306` de MicroPython (SSD1306_I2C).
- **Sin dependencia** a Chess, ChessGame u otros modulos del proyecto.

---

## Cambios respecto a v1.0

### Eliminado
- **Dependencia a Chess**: ya no recibe instancia de Chess en constructor.
- **Panel informativo**: la zona derecha (turno, movimiento, capturas, estado) se elimina temporalmente.
- **getCapturedPieces() como prerequisito**: ya no se requiere.
- **Lectura de estado via metodos de Chess**: `chess.getTurn()`, `chess.isCheck()`, etc. ya no se invocan.

### Nuevo
- **setTable(board)**: metodo para recibir datos del tablero como lista/cadena de 64 caracteres.
- **Renderizado desacoplado**: el display no sabe de donde vienen los datos, solo los dibuja.

### Se mantiene
- Renderizado de tablero de ajedrez en zona de 64x64 pixels.
- Piezas en pixel art 8x8.
- Patron ajedrezado con diferenciacion blancas/negras.
- Orientacion configurable (flip).
- Constructor con pines I2C.

---

## API Publica

### Constructor

```python
ChessDisplay(sda, scl, flipped=False, address=0x3C, i2cId=0)
```

| Parametro | Tipo | Default | Descripcion |
|-----------|------|---------|-------------|
| `sda` | `int` | (requerido) | Numero de pin GPIO para SDA |
| `scl` | `int` | (requerido) | Numero de pin GPIO para SCL |
| `flipped` | `bool` | `False` | Orientacion inicial. `False` = blancas abajo, `True` = negras abajo |
| `address` | `int` | `0x3C` | Direccion I2C del SSD1306 |
| `i2cId` | `int` | `0` | Numero de bus I2C a usar |

**Diferencia con v1.0**: Se elimino el parametro `chess`.

El constructor internamente:
1. Crea la instancia `machine.I2C` con los pines proporcionados.
2. Crea la instancia `ssd1306.SSD1306_I2C(128, 64, i2c, addr=address)`.
3. Inicializa el tablero interno vacio (64 espacios).

### Metodos Publicos

| Metodo | Parametros | Retorno | Descripcion |
|--------|------------|---------|-------------|
| `setTable` | `board` | ninguno | Recibe los datos del tablero como lista o cadena de 64 caracteres. Almacena internamente para el proximo render |
| `render` | ninguno | ninguno | Dibuja el tablero en la pantalla usando los datos del ultimo `setTable()`. Si no se ha llamado `setTable()`, dibuja tablero vacio |
| `flip` | ninguno | ninguno | Invierte la orientacion del tablero (toggle). **No llama a render automaticamente** |

### Propiedades

| Propiedad | Tipo | Lectura | Escritura | Descripcion |
|-----------|------|---------|-----------|-------------|
| `flipped` | `bool` | Si | Si | Orientacion actual del tablero |

---

## Metodo setTable(board)

Recibe la representacion del tablero y la almacena internamente.

- `board`: lista de 64 caracteres o string de 64 caracteres.
  - Indice 0 = a1, indice 63 = h8.
  - Piezas blancas: `P, N, B, R, Q, K` (mayusculas).
  - Piezas negras: `p, n, b, r, q, k` (minusculas).
  - Casilla vacia: `' '` (espacio).

Este formato es compatible con `Chess.getBoard()` (via `ChessGame.getBoard()`).

**No llama a render automaticamente.** El usuario debe llamar `render()` despues para ver los cambios.

---

## Distribucion de Pantalla (Layout v2.0)

```
|<--- 64px --->|<--- 64px --->|
+==============+==============+ -+-
|              |              |  |
|   Tablero    |  (sin uso)   | 64px
|   de ajedrez |              |  |
|              |              |  |
+==============+==============+ -+-
```

### Zona Izquierda: Tablero (64x64 pixels)

Sin cambios respecto a v1.0:

- Cuadricula de 8x8 casillas, cada una de 8x8 pixels.
- Patron ajedrezado: casillas claras (pixels apagados) y oscuras (pixels encendidos).
- Piezas representadas con pixel art 8x8.
- Las piezas en casillas claras se dibujan con pixels encendidos (silueta oscura sobre fondo claro).
- Las piezas en casillas oscuras se dibujan invertidas con XOR (silueta clara sobre fondo oscuro).
- Orientacion configurable: blancas abajo (default) o negras abajo (flipped).

### Zona Derecha (64x64 pixels)

**Temporalmente sin uso.** Se deja vacia (pixels apagados). En futuras versiones podra usarse para informacion de partida.

---

## Comportamiento Detallado

### render()

1. Limpia el buffer del framebuffer (`fill(0)`).
2. Dibuja el tablero de ajedrez en la zona izquierda (64x64):
   a. Itera sobre las 64 casillas.
   b. Determina si la casilla es clara u oscura (patron ajedrezado).
   c. Si hay pieza (segun datos de `setTable()`), dibuja el bitmap correspondiente con la inversion adecuada.
   d. Si esta vacia, dibuja casilla clara u oscura segun corresponda.
   e. Respeta la orientacion (`flipped`).
3. Llama a `display.show()` para enviar el buffer a la pantalla.

**Diferencia con v1.0**: No lee estado de Chess. Usa datos almacenados internamente por `setTable()`.

### flip()

Sin cambios respecto a v1.0:
1. Invierte el valor interno de `_flipped` (toggle: True <-> False).
2. NO llama a render() automaticamente.

### Orientacion del tablero

Sin cambios respecto a v1.0:
- `flipped = False` (default): fila 1 (blancas) abajo, fila 8 (negras) arriba. Columna 'a' a la izquierda.
- `flipped = True`: fila 8 (negras) abajo, fila 1 (blancas) arriba. Columna 'h' a la izquierda.

---

## Piezas en Pixel Art 8x8

Sin cambios respecto a v1.0.

Cada pieza se almacena como un bitmap de 8 bytes (1 byte por fila, 8 bits por columna). Total: 6 piezas x 8 bytes = **48 bytes**.

Las 6 piezas: Rey (K/k), Dama (Q/q), Torre (R/r), Alfil (B/b), Caballo (N/n), Peon (P/p).

### Diferenciacion blancas/negras

Las piezas blancas y negras usan el mismo bitmap. La diferenciacion se logra por contexto visual (tecnica a criterio del implementador, siempre que sean distinguibles en ambos tipos de casilla).

---

## Manejo de Errores

Sin cambios respecto a v1.0:
- Sin excepciones custom.
- Si la inicializacion I2C o SSD1306 falla, se deja propagar la excepcion de MicroPython.
- `setTable()` con datos invalidos (longitud != 64): comportamiento indefinido.

---

## Estructura de Archivos

```text
modules/
  CHESSDISPLAY_REQUIREMENTS.md    # Este documento
  chessdisplay/
    __init__.py                   # Exporta ChessDisplay
    ChessDisplay.py               # Clase principal

tests/
  modules/
    chessdisplay/
      test_chess_display.py       # Tests con mocks de SSD1306 (sin mock de Chess)
```

---

## Funcionalidad Excluida (fuera de alcance)

Se mantiene la lista de v1.0 mas:
- **Panel informativo** (turno, movimiento, capturas, estado): eliminado temporalmente.
- Manejo de entrada de usuario (botones, rotary encoder, touch).
- Auto-actualizacion via callbacks.
- Highlight de ultimo movimiento.
- Pantallas especiales de evento.
- Animaciones o transiciones.
- Modo debug / logging.
- Ajuste de contraste / brillo.
- Metodo clear() o showMessage().
- Soporte para pantallas SSD1306 de 128x32.
- Conexion SPI (solo I2C).
- Multiples pantallas.

---

## Consideraciones de Implementacion

El agente desarrollador debe:

1. Disenar los 6 bitmaps de piezas (8x8 pixels) como constantes compactas.
2. Implementar el renderizado del patron ajedrezado usando operaciones de framebuffer.
3. Decidir la tecnica de diferenciacion visual entre piezas blancas y negras.
4. Usar operaciones XOR o similares para invertir piezas en casillas oscuras.
5. Optimizar el uso de `framebuf` para minimizar allocaciones en cada render.
6. Asegurar que el import de `machine` y `ssd1306` tenga fallback para entornos de testing:
   ```python
   try:
       from machine import Pin, I2C
       from ssd1306 import SSD1306_I2C
   except ImportError:
       Pin = None
       I2C = None
       SSD1306_I2C = None
   ```
7. **Actualizar constructor** para eliminar parametro `chess`.
8. **Implementar setTable()** para almacenar datos del tablero.
9. **Adaptar render()** para leer de datos internos en vez de instancia de Chess.
10. **Eliminar toda referencia a Chess** del modulo.

---

## Ejemplo de Uso (v2.0)

```python
from modules.chessdisplay import ChessDisplay
from modules.chessgame import ChessGame

# Crear display
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

# Usar sin ChessGame (tablero custom directo)
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

---

## Criterios de Aceptacion (v2.0)

### AC-01: Crear instancia sin Chess
- **Given** pines SDA=21, SCL=22
- **When** se crea `ChessDisplay(sda=21, scl=22)`
- **Then** la instancia se crea sin errores, con flipped=False, tablero vacio interno

### AC-02: setTable() almacena datos
- **Given** una instancia de ChessDisplay
- **When** se llama `setTable(board)` con 64 caracteres
- **Then** los datos se almacenan internamente para el proximo render

### AC-03: render() dibuja tablero con piezas
- **Given** ChessDisplay con setTable() llamado con posicion inicial
- **When** se llama `render()`
- **Then** el framebuffer contiene el tablero con todas las piezas en posicion inicial

### AC-04: render() sin setTable() dibuja tablero vacio
- **Given** ChessDisplay recien creado (sin setTable)
- **When** se llama `render()`
- **Then** dibuja tablero vacio (solo patron ajedrezado)

### AC-05: setTable() no llama a render
- **Given** una instancia de ChessDisplay
- **When** se llama `setTable(board)`
- **Then** display.show() NO es invocado

### AC-06: flip() invierte orientacion (sin cambios)
- **Given** ChessDisplay con flipped=False
- **When** se llama `flip()`
- **Then** flipped pasa a True

### AC-07: flip() no llama a render (sin cambios)
- **Given** una instancia de ChessDisplay
- **When** se llama `flip()`
- **Then** display.show() NO es invocado

### AC-08: Orientacion flipped=False muestra blancas abajo (sin cambios)
- **Given** ChessDisplay con flipped=False y posicion inicial via setTable
- **When** se llama `render()`
- **Then** la fila 1 (piezas blancas) se dibuja en la parte inferior del tablero

### AC-09: Orientacion flipped=True muestra negras abajo (sin cambios)
- **Given** ChessDisplay con flipped=True y posicion inicial via setTable
- **When** se llama `render()`
- **Then** la fila 8 (piezas negras) se dibuja en la parte inferior del tablero

### AC-10: Piezas blancas y negras son distinguibles (sin cambios)
- **Given** una casilla con pieza blanca y otra con pieza negra del mismo tipo
- **When** se llama `render()`
- **Then** los bitmaps generados son diferentes

### AC-11: Patron ajedrezado correcto (sin cambios)
- **Given** tablero vacio via setTable
- **When** se renderiza
- **Then** a1 es casilla oscura, b1 clara, a2 clara, b2 oscura

### AC-12: Propiedad flipped legible y escribible (sin cambios)
- **Given** una instancia de ChessDisplay
- **When** se lee y asigna `display.flipped`
- **Then** los valores se leen y asignan correctamente

---

## Decisions Log

| Fecha | Decision | Alternativas | Razon |
|-------|----------|--------------|-------|
| 2026-02-05 | v1.0: Display recibe instancia de Chess | Display independiente; recibe datos crudos | Simplicidad de uso (una sola linea render()) |
| 2026-02-06 | v2.0: Display recibe datos via setTable() | Recibir ChessGame; mantener Chess | Desacoplamiento total. Display no necesita conocer la fuente de datos |
| 2026-02-06 | Eliminar panel informativo temporalmente | Mantener panel; panel con datos pasados por metodo | Simplificar scope v2.0. Panel se puede re-agregar en v3.0 con datos explicitamente pasados |
| 2026-02-06 | Constructor sin parametro chess | Parametro game opcional | Limpieza de dependencias |
| 2026-02-05 | Pixel art 8x8 para piezas | (sin cambios) | (sin cambios) |
| 2026-02-05 | Layout 64+64 (tablero + zona derecha) | (sin cambios) | (sin cambios) |
| 2026-02-05 | Orientacion configurable (flip) | (sin cambios) | (sin cambios) |
| 2026-02-05 | SSD1306 creado internamente | (sin cambios) | (sin cambios) |
| 2026-02-05 | Pines I2C obligatorios sin defaults | (sin cambios) | (sin cambios) |
| 2026-02-05 | API minima: render() + flip() + setTable() | Agregar clear(), showMessage() | YAGNI |

---

## Observaciones y decisiones diferidas

- **Panel informativo**: Eliminado en v2.0 por simplicidad. En una futura v3.0, podria re-agregarse con metodos explicitos tipo `setInfo(turn, moveNumber, lastMove, state, captures)` para mantener el desacoplamiento.
- **Zona derecha de pantalla**: 64x64 pixels sin uso. Podria aprovecharse en futuras versiones.
- **Compatibilidad con tests existentes**: Los tests de `test_chess_display.py` necesitaran actualizacion para reflejar la nueva API (sin Chess, con setTable).
