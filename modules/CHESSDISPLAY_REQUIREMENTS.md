---
last_updated: "2026-02-05 18:00"
version: "1.0"
status: draft
author: Discovery Architect
---

# ChessDisplay Module - Documento de Requerimientos

## Descripcion General

Desarrollar un modulo de visualizacion llamado `ChessDisplay.py` para ESP32 (MicroPython) que renderice el estado de una partida de ajedrez en una pantalla OLED SSD1306 de 128x64 pixels conectada por I2C. El modulo recibe una instancia del modulo `Chess` existente y dibuja el tablero con piezas en pixel art 8x8, ademas de un panel informativo con turno, numero de movimiento, ultimo movimiento jugado y piezas capturadas.

Este modulo es **exclusivamente de renderizado**. No maneja entrada de usuario (botones, encoder, etc.) ni logica de juego.

## Restricciones Tecnicas

- Compatible con MicroPython para ESP32
- Optimizar uso de memoria RAM (~100KB disponibles en ESP32)
- Usar camelCase para todos los nombres de metodos y propiedades
- Ubicacion del archivo: `modules/chessdisplay/ChessDisplay.py`
- Nombre de la clase: `ChessDisplay`
- Pantalla: SSD1306 128x64 pixels, monocromatica, conexion I2C
- Dependencia: libreria `ssd1306` de MicroPython (SSD1306_I2C)
- Dependencia: modulo `Chess` del proyecto (para leer estado de la partida)

---

## Dependencia Cruzada: Modulo Chess

Este modulo requiere que se agregue el siguiente metodo al modulo `Chess` existente:

### getCapturedPieces()

- **Retorno**: formato a determinar por el agente implementador (dict por color, lista, etc.)
- **Proposito**: obtener las piezas que han sido capturadas durante la partida
- **Restriccion**: debe ser eficiente en memoria; el implementador elige el formato optimo
- **Nota**: este metodo NO existe actualmente en Chess.py y debe ser agregado como prerequisito

---

## Distribucion de Pantalla (Layout)

La pantalla de 128x64 pixels se divide en dos zonas:

```
|<--- 64px --->|<--- 64px --->|
+==============+==============+ -+-
|              |              |  |
|   Tablero    |  Panel Info  | 64px
|   de ajedrez |  (texto)     |  |
|              |              |  |
+==============+==============+ -+-
```

### Zona Izquierda: Tablero (64x64 pixels)

- Cuadricula de 8x8 casillas, cada una de 8x8 pixels
- Patron ajedrezado: casillas claras (pixels apagados) y oscuras (pixels encendidos)
- Piezas representadas con pixel art 8x8
- Las piezas en casillas claras se dibujan con pixels encendidos (silueta oscura sobre fondo claro)
- Las piezas en casillas oscuras se dibujan invertidas con XOR (silueta clara sobre fondo oscuro)
- Orientacion configurable: blancas abajo (default) o negras abajo (flipped)

### Zona Derecha: Panel Informativo (64x64 pixels)

Usando la fuente por defecto de MicroPython (framebuf, 8x8 pixels por caracter), se dispone de **8 caracteres por linea** y **8 lineas**.

Contenido del panel (distribucion sugerida, el implementador puede ajustar):

```
Linea 1: Turno actual        Ej: "Turn: W " o "Turn: B "
Linea 2: Numero de movimiento Ej: "Mov:  15"
Linea 3: Ultimo movimiento    Ej: "e2-e4   " o "O-O-O   "
Linea 4: (vacia o separador)
Linea 5: Estado de partida    Ej: "CHECK!" / "MATE!" / "DRAW" / "STALE" / ""
Linea 6: Etiqueta capturadas  Ej: "Capt:   "
Linea 7: Capturadas blancas   Ej: "ppnb    " (piezas negras capturadas por blancas)
Linea 8: Capturadas negras    Ej: "PP      " (piezas blancas capturadas por negras)
```

**Notas sobre el panel:**
- Cuando no hay jaque/mate/tablas, la linea de estado se deja vacia
- Los estados posibles a mostrar: CHECK, MATE, DRAW, STALE (stalemate)
- Las piezas capturadas se muestran como letras (p, n, b, r, q para negras; P, N, B, R, Q para blancas)
- Si no caben todas las capturadas en 8 chars, truncar mostrando las de mayor valor primero
- Cuando no se ha jugado ningun movimiento, la linea de ultimo movimiento queda vacia

---

## Piezas en Pixel Art 8x8

Cada pieza se almacena como un bitmap de 8 bytes (1 byte por fila, 8 bits por columna). Total: 6 piezas x 8 bytes = **48 bytes** de almacenamiento.

Las 6 piezas a representar:
- Rey (K/k)
- Dama (Q/q)
- Torre (R/r)
- Alfil (B/b)
- Caballo (N/n)
- Peon (P/p)

### Diferenciacion blancas/negras

Las piezas blancas y negras usan el **mismo bitmap**. La diferenciacion se logra por contexto:
- En casilla clara: pieza blanca = silueta rellena, pieza negra = silueta con borde (outline)
- En casilla oscura: se aplica inversion correspondiente

El agente implementador decide la mejor tecnica de diferenciacion visual que funcione en monocromo, siempre que las piezas blancas y negras sean distinguibles entre si en ambos tipos de casilla.

### Casillas vacias

- Casilla clara: pixels apagados (fondo limpio)
- Casilla oscura: pixels encendidos (fondo relleno)

---

## API Publica

### Constructor

```python
ChessDisplay(chess, sda, scl, flipped=False, address=0x3C, i2cId=0)
```

| Parametro | Tipo | Default | Descripcion |
|-----------|------|---------|-------------|
| `chess` | `Chess` | (requerido) | Instancia del modulo Chess para leer estado |
| `sda` | `int` | (requerido) | Numero de pin GPIO para SDA |
| `scl` | `int` | (requerido) | Numero de pin GPIO para SCL |
| `flipped` | `bool` | `False` | Orientacion inicial. `False` = blancas abajo, `True` = negras abajo |
| `address` | `int` | `0x3C` | Direccion I2C del SSD1306 |
| `i2cId` | `int` | `0` | Numero de bus I2C a usar |

El constructor internamente:
1. Crea la instancia `machine.I2C` con los pines proporcionados
2. Crea la instancia `ssd1306.SSD1306_I2C(128, 64, i2c, addr=address)`
3. Almacena la referencia a la instancia de Chess

### Metodos Publicos

| Metodo | Parametros | Retorno | Descripcion |
|--------|------------|---------|-------------|
| `render` | ninguno | ninguno | Dibuja el estado actual completo (tablero + panel info) en la pantalla. Lee el estado de la instancia Chess y actualiza el display |
| `flip` | ninguno | ninguno | Invierte la orientacion del tablero (toggle). Si estaba con blancas abajo, pasa a negras abajo y viceversa. NO llama a render automaticamente |

### Propiedades

| Propiedad | Tipo | Lectura | Escritura | Descripcion |
|-----------|------|---------|-----------|-------------|
| `flipped` | `bool` | Si | Si | Orientacion actual del tablero |

---

## Comportamiento Detallado

### render()

1. Limpia el buffer del framebuffer (fill(0))
2. Dibuja el tablero de ajedrez en la zona izquierda (64x64):
   a. Itera sobre las 64 casillas
   b. Determina si la casilla es clara u oscura (patron ajedrezado)
   c. Si hay pieza, dibuja el bitmap correspondiente con la inversion adecuada
   d. Si esta vacia, dibuja casilla clara u oscura segun corresponda
   e. Respeta la orientacion (`flipped`)
3. Dibuja el panel informativo en la zona derecha (64x64):
   a. Turno actual (lee `chess.getTurn()`)
   b. Numero de movimiento (lee del estado de Chess)
   c. Ultimo movimiento jugado (lee del historial de Chess)
   d. Estado de la partida: llama a `chess.isCheck()`, `chess.isCheckmate()`, `chess.isStalemate()`, `chess.isDraw()`
   e. Piezas capturadas (lee `chess.getCapturedPieces()`)
4. Llama a `display.show()` para enviar el buffer a la pantalla

### flip()

1. Invierte el valor interno de `_flipped` (toggle: True <-> False)
2. NO llama a render() automaticamente. El usuario debe llamar render() despues si quiere ver el cambio

### Orientacion del tablero

- `flipped = False` (default): fila 1 (blancas) abajo, fila 8 (negras) arriba. Columna 'a' a la izquierda
- `flipped = True`: fila 8 (negras) abajo, fila 1 (blancas) arriba. Columna 'h' a la izquierda

---

## Manejo de Errores

- Sin excepciones custom: si la inicializacion I2C o SSD1306 falla, se deja propagar la excepcion de MicroPython
- Si `chess` es None o no tiene los metodos esperados, el comportamiento es indefinido (no se valida)
- Patron consistente con AccessPoint: sin validacion de parametros de entrada

---

## Estructura de Archivos

```
modules/
  CHESSDISPLAY_REQUIREMENTS.md    # Este documento
  chessdisplay/
    __init__.py                   # Exporta ChessDisplay
    ChessDisplay.py               # Clase principal

tests/
  modules/
    chessdisplay/
      test_chess_display.py       # Tests con mocks de SSD1306 y Chess
```

---

## Funcionalidad Excluida (fuera de alcance)

- Manejo de entrada de usuario (botones, rotary encoder, touch)
- Auto-actualizacion via callbacks (el render es siempre manual)
- Highlight de ultimo movimiento en el tablero (casillas resaltadas)
- Pantallas especiales de evento (fullscreen para mate, tablas, etc.)
- Animaciones o transiciones
- Modo debug / logging
- Ajuste de contraste / brillo
- Metodo clear() o showMessage()
- Soporte para pantallas SSD1306 de 128x32
- Conexion SPI (solo I2C)
- Multiples pantallas

---

## Consideraciones de Implementacion

El agente desarrollador debe:

1. Disenar los 6 bitmaps de piezas (8x8 pixels) como constantes compactas (bytes o listas de enteros)
2. Implementar el renderizado del patron ajedrezado usando operaciones de framebuffer
3. Decidir la tecnica de diferenciacion visual entre piezas blancas y negras en monocromo
4. Usar operaciones XOR o similares para invertir piezas en casillas oscuras, evitando almacenar bitmaps duplicados
5. Optimizar el uso de `framebuf` para minimizar allocaciones en cada render
6. Implementar `getCapturedPieces()` en el modulo Chess como prerequisito
7. Asegurar que el import de `machine` y `ssd1306` tenga fallback para entornos de testing:
   ```python
   try:
       from machine import Pin, I2C
       from ssd1306 import SSD1306_I2C
   except ImportError:
       Pin = None
       I2C = None
       SSD1306_I2C = None
   ```

---

## Ejemplo de Uso Esperado

```python
from modules.chess import Chess
from modules.chessdisplay import ChessDisplay

# Crear partida
chess = Chess()

# Crear display (pines I2C del ESP32)
display = ChessDisplay(chess, sda=21, scl=22)

# Renderizar posicion inicial
display.render()

# Jugar y actualizar
chess.play('e2-e4')
display.render()

chess.play('e7-e5')
display.render()

# Girar tablero (ver desde perspectiva negras)
display.flip()
display.render()

# Acceder a orientacion
print(display.flipped)  # True

# Con parametros opcionales
display2 = ChessDisplay(
    chess,
    sda=21,
    scl=22,
    flipped=True,
    address=0x3D,
    i2cId=1
)
display2.render()
```

---

## Criterios de Aceptacion

### Tests Automatizados (con mocks de machine, ssd1306 y Chess)

#### AC-01: Crear instancia con parametros requeridos
- **Given** una instancia de Chess y pines SDA=21, SCL=22
- **When** se crea `ChessDisplay(chess, sda=21, scl=22)`
- **Then** la instancia se crea sin errores, con flipped=False, address=0x3C, i2cId=0

#### AC-02: Crear instancia con todos los parametros
- **Given** parametros chess, sda=21, scl=22, flipped=True, address=0x3D, i2cId=1
- **When** se crea `ChessDisplay(chess, sda=21, scl=22, flipped=True, address=0x3D, i2cId=1)`
- **Then** la instancia se crea con los valores proporcionados

#### AC-03: render() dibuja tablero en posicion inicial
- **Given** una instancia de ChessDisplay con Chess en posicion inicial
- **When** se llama `render()`
- **Then** el framebuffer contiene el tablero con todas las piezas en posicion inicial y el panel muestra Turn: W, Mov: 1, sin ultimo movimiento ni capturadas

#### AC-04: render() actualiza despues de movimiento
- **Given** Chess con movimiento e2-e4 ejecutado
- **When** se llama `render()`
- **Then** el panel muestra Turn: B, ultimo movimiento e2-e4, y el peon aparece en e4

#### AC-05: render() muestra estado de jaque
- **Given** Chess en posicion de jaque
- **When** se llama `render()`
- **Then** el panel muestra indicador de CHECK

#### AC-06: render() muestra estado de jaque mate
- **Given** Chess en posicion de jaque mate
- **When** se llama `render()`
- **Then** el panel muestra indicador de MATE

#### AC-07: render() muestra estado de tablas
- **Given** Chess en posicion de tablas
- **When** se llama `render()`
- **Then** el panel muestra indicador de DRAW

#### AC-08: render() muestra estado de ahogado
- **Given** Chess en posicion de stalemate
- **When** se llama `render()`
- **Then** el panel muestra indicador de STALE

#### AC-09: flip() invierte orientacion
- **Given** ChessDisplay con flipped=False
- **When** se llama `flip()`
- **Then** flipped pasa a True

#### AC-10: flip() es toggle
- **Given** ChessDisplay con flipped=True
- **When** se llama `flip()`
- **Then** flipped pasa a False

#### AC-11: flip() no llama a render
- **Given** una instancia de ChessDisplay
- **When** se llama `flip()`
- **Then** display.show() NO es invocado (no se actualiza la pantalla)

#### AC-12: Orientacion flipped=False muestra blancas abajo
- **Given** ChessDisplay con flipped=False y Chess en posicion inicial
- **When** se llama `render()`
- **Then** la fila 1 (piezas blancas) se dibuja en la parte inferior del tablero

#### AC-13: Orientacion flipped=True muestra negras abajo
- **Given** ChessDisplay con flipped=True y Chess en posicion inicial
- **When** se llama `render()`
- **Then** la fila 8 (piezas negras) se dibuja en la parte inferior del tablero

#### AC-14: render() muestra piezas capturadas
- **Given** Chess con piezas capturadas (ej: despues de varias capturas)
- **When** se llama `render()`
- **Then** el panel muestra las piezas capturadas por cada bando

#### AC-15: render() con posicion inicial sin capturas
- **Given** Chess en posicion inicial (sin movimientos)
- **When** se llama `render()`
- **Then** la zona de capturadas esta vacia y no hay ultimo movimiento

#### AC-16: Propiedad flipped es legible y escribible
- **Given** una instancia de ChessDisplay
- **When** se lee `display.flipped` y se asigna `display.flipped = True`
- **Then** los valores se leen y asignan correctamente

#### AC-17: Piezas blancas y negras son visualmente distinguibles
- **Given** una casilla con pieza blanca y otra con pieza negra del mismo tipo
- **When** se llama `render()`
- **Then** los bitmaps generados para ambas piezas son diferentes (verificable comparando bytes del framebuffer)

#### AC-18: Patron ajedrezado correcto
- **Given** un tablero vacio (sin piezas)
- **When** se renderiza
- **Then** a1 es casilla oscura, b1 clara, a2 clara, b2 oscura (patron estandar de ajedrez)

---

## Decisions Log

| Fecha | Decision | Alternativas Consideradas | Razon |
|-------|----------|---------------------------|-------|
| 2026-02-05 | Pantalla SSD1306 128x64, I2C | 128x32, SPI | Usuario confirma hardware disponible |
| 2026-02-05 | Solo renderizado, sin entrada | Render + input (botones/encoder) | Separacion de responsabilidades; input sera modulo aparte |
| 2026-02-05 | Render manual via render() | Auto-render via callbacks, ambos modos | Simplicidad y control explicito; el usuario decide cuando actualizar |
| 2026-02-05 | Pixel art 8x8 para piezas | Letras simples (K/Q/R), dejar que el agente decida | Factible en 48 bytes, mucho mas visual que letras, minimo impacto en RAM |
| 2026-02-05 | Layout 64+64 (tablero + info) | Tablero arriba info abajo, tablero centrado | 8px por casilla = 64px exacto en alto, deja 64px utiles para info |
| 2026-02-05 | Orientacion configurable (flip) | Solo blancas abajo fijo | Permite ver tablero desde ambas perspectivas |
| 2026-02-05 | Sin highlight de ultimo movimiento | Resaltar casillas origen/destino | Fuera de alcance actual; se puede agregar despues |
| 2026-02-05 | Estados como texto en panel | Pantallas especiales fullscreen | Mas simple; no interrumpe la visualizacion del tablero |
| 2026-02-05 | SSD1306 creado internamente | Recibir SSD1306 ya inicializado externamente | Mas simple para el usuario; solo pasa pines |
| 2026-02-05 | Pines I2C obligatorios sin defaults | Defaults SCL=22, SDA=21 | Evita suposiciones; el usuario siempre especifica sus pines |
| 2026-02-05 | Agregar getCapturedPieces() a Chess | Deducir del tablero en display, omitir capturadas | Responsabilidad correcta: Chess conoce las capturas, display solo muestra |
| 2026-02-05 | API minima: render() + flip() | Agregar clear(), showMessage(), setContrast() | YAGNI; mantener modulo simple, expandir solo si se necesita |
| 2026-02-05 | Formato de getCapturedPieces() libre | Dict por color, lista plana | El implementador elige lo mas eficiente para ESP32 |

---

## Observaciones y Decisiones Diferidas

- **Diseno exacto de bitmaps**: Los 6 bitmaps de pixel art (rey, dama, torre, alfil, caballo, peon) deben ser disenados durante la implementacion. El documento de requerimientos provee bocetos conceptuales pero los valores finales en bytes los decide el implementador.
- **Tecnica de diferenciacion blancas/negras en monocromo**: Se dejo a criterio del implementador. Opciones viables: silueta rellena vs outline, inversion completa, o combinacion con el fondo de la casilla.
- **Formato exacto del panel informativo**: La distribucion de las 8 lineas es sugerida pero el implementador puede ajustarla si encuentra una disposicion mas legible dentro de las restricciones de 8 chars x 8 lineas.
- **Orden de piezas capturadas**: Se sugiere mostrar por valor (dama > torre > alfil > caballo > peon) pero es decision del implementador.
- **Truncamiento de capturadas**: Si no caben todas en 8 caracteres, se sugiere priorizar piezas de mayor valor, pero el implementador decide.

---

## Version
- Version del documento: 1.0
- Fecha: Febrero 2026
