---
last_updated: "2026-02-06 21:10"
version: "2.4"
status: draft
author: Discovery Architect
---

# ChessDisplay Module - Documento de Requerimientos (v2.4)

## Descripcion General

`ChessDisplay` es un modulo de renderizado para OLED SSD1306 128x64 (I2C) orientado a ESP32/MicroPython.

Responsabilidad:
- Dibujar tablero 8x8 en la mitad izquierda.
- Dibujar panel lateral completo con dos relojes (`w` y `b`), estado de turno y contador de turnos.

No responsabilidad:
- Logica de ajedrez.
- Orquestacion de turnos.
- Lectura de botones.
- Control de tiempo interno.

El modulo no depende de `Chess`; solo recibe datos crudos.

## Restricciones Tecnicas

- Runtime: MicroPython (ESP32)
- Archivo: `modules/chessdisplay/ChessDisplay.py`
- Clase: `ChessDisplay`
- Convencion: camelCase
- Driver: `ssd1306.SSD1306_I2C`
- Pantalla: 128x64, monocromo

## Cambios respecto a v2.0

- Se elimina API en dos pasos (`setTable()` + `render()`).
- API nueva y directa:
  - `renderBoard(board)`
  - `renderClock(clockText, color)`
  - `renderTurn(color)`
  - `renderTurnCount(turnCount)`
  - `renderSidePanel(whiteClock, blackClock, activeColor, turnCount)`
- `renderClock` usa glifos 8x16 precomputados en bytes hex y soporta inversion del reloj activo.

## API Publica

### Constructor

```python
ChessDisplay(sda, scl, address=0x3C, i2cId=0)
```

### Metodos

| Metodo | Parametros | Retorno | Descripcion |
|--------|------------|---------|-------------|
| `renderBoard` | `board` | ninguno | Dibuja tablero 8x8 en zona izquierda y llama `show()` |
| `renderClock` | `clockText`, `color` | ninguno | Actualiza reloj del color indicado y repinta panel lateral |
| `renderTurn` | `color` | ninguno | Actualiza turno activo (`w`/`b`) y repinta panel lateral |
| `renderTurnCount` | `turnCount` | ninguno | Actualiza numero de turnos y repinta panel lateral |
| `renderSidePanel` | `whiteClock`, `blackClock`, `activeColor`, `turnCount` | ninguno | Actualiza todo el panel lateral en una llamada |

## Formato de Datos

### `board`

- Tipo: `str`
- Longitud: 64
- Mapeo: indice `0 = a1`, indice `63 = h8`
- Piezas blancas: `P N B R Q K`
- Piezas negras: `p n b r q k`
- Vacio: `' '`

### `clockText`

- Tipo: `str`
- Formato esperado: `MM:SS`
- Se renderizan hasta 5 caracteres (`text[:5]`).

### `color` / `activeColor`

- Tipo: `str`
- Valores validos: `'w'` o `'b'`
- En panel central se muestra:
  - `'B'` cuando `activeColor == 'w'` (Blancas)
  - `'N'` cuando `activeColor == 'b'` (Negras)

### `turnCount`

- Tipo: `int`
- Restriccion: `>= 0`

## Layout de Pantalla

```text
|<--- 64px --->|<--- 64px --->|
+==============+==============+
|              |   03:00      | <- reloj superior
|   Tablero    |              |
|   8x8        |  B    12     | <- estado central (turno + turnos)
|              |              |
|              |   02:58      | <- reloj inferior
+==============+==============+
```

- Zona izquierda (x=0..63): tablero completo 8x8.
- Zona derecha superior (x=64..127, y=0..15): reloj del jugador de arriba.
- Zona derecha central (x=64..127, y=24..39): estado (`B`/`N`) + turnCount.
- Zona derecha inferior (x=64..127, y=48..63): reloj del jugador de abajo.

## Estrategia de Render (Performance)

### Tablero

- Escritura directa en `display.buffer` cuando el buffer es plano (`bytearray` MONO_VLSB).
- Tile de 8x8 dibujado como 8 bytes por casilla (alineado por paginas).
- Fallback a `pixel()` solo para mocks de pruebas (buffer 2D).

### Reloj

- Glifos 8x16 precomputados en hex.
- Se escriben dos paginas (page0 y page1) por columna, evitando `fill_rect`/`pixel` en flujo normal.
- Se limpia y redibuja todo el panel lateral (`x=64..127, y=0..63`) al actualizar estado de panel.
- El reloj del jugador activo se dibuja en modo invertido para resaltarlo.

### Contraste visual

- Casilla oscura con patron `*-*-*` de baja densidad.
- Pieza blanca: silueta rellena.
- Pieza negra: contorno ajustado con interior hueco para mayor legibilidad.

## Comportamiento esperado

### `renderBoard(board)`

1. Guarda `board` internamente.
2. Redibuja solo la mitad izquierda (tablero completo).
3. Conserva lo ya dibujado en la mitad derecha.
4. Llama `show()`.

### `renderClock(clockText, color)`

1. Actualiza reloj del color indicado (`w`/`b`).
2. Redibuja panel lateral completo.
3. Aplica inversion al reloj del jugador activo.
4. Llama `show()`.

### `renderTurn(color)`

1. Actualiza turno activo (`w`/`b`).
2. Redibuja panel lateral y central (`B`/`N`).
3. Llama `show()`.

### `renderTurnCount(turnCount)`

1. Actualiza contador de turnos.
2. Redibuja panel lateral.
3. Llama `show()`.

## Ejemplos de Uso

```python
from modules.chess import Chess
from modules.chessdisplay import ChessDisplay

# Instancias base
chess = Chess()
display = ChessDisplay(21, 22)

# Render inicial de tablero y reloj
display.renderBoard(chess.getBoard())
display.renderSidePanel("05:00", "05:00", "w", 1)

# Tras un movimiento, actualizar tablero
chess.play("e2-e4")
display.renderBoard(chess.getBoard())
display.renderClock("04:58", "w")
display.renderTurn("b")
display.renderTurnCount(1)
```

## Criterios de Aceptacion

- AC-01: instancia se crea con parametros default de I2C.
- AC-02: `renderBoard(board)` dibuja piezas en posiciones correctas y llama `show()`.
- AC-03: `renderClock('05:00', 'w')` actualiza reloj blanco y llama `show()`.
- AC-04: `renderTurn('b')` actualiza estado central a `N` y llama `show()`.
- AC-05: `renderTurnCount(12)` dibuja valor de turnos junto al estado central.
- AC-05: en casilla oscura vacia existe patron de baja densidad (no relleno completo).
- AC-06: pieza negra se distingue claramente de pieza blanca del mismo tipo.

## Decisions Log

| Fecha | Decision | Razon |
|-------|----------|-------|
| 2026-02-06 | Reemplazar `setTable()+render()` por `renderBoard()` | API mas directa para orquestador |
| 2026-02-06 | Doble reloj por jugador con `renderClock(clockText, color)` | Requiere panel lateral consistente y por color |
| 2026-02-06 | Resaltar reloj activo con inversion | Mejor legibilidad del turno sin reducir tamano de fuente |
| 2026-02-06 | Estado central `B`/`N` + turnCount | Publico hispanohablante y referencia visual compacta |
| 2026-02-06 | Fuente reloj en hex precomputado | Menor CPU por frame |
| 2026-02-06 | Mantener `ssd1306.py` y optimizar capa superior | Reusar driver estable y reducir complejidad |

## Fuera de alcance

- Auto-refresh interno con timer propio.
- Inyectar objeto `ChessClock` directamente en display.
- Animaciones de piezas.
- Multiples tamanos de fuente generales (solo reloj 8x16 por ahora).
