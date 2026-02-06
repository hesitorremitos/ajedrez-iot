---
last_updated: "2026-02-06 20:15"
version: "2.3"
status: draft
author: Discovery Architect
---

# ChessDisplay Module - Documento de Requerimientos (v2.3)

## Descripcion General

`ChessDisplay` es un modulo de renderizado para OLED SSD1306 128x64 (I2C) orientado a ESP32/MicroPython.

Responsabilidad:
- Dibujar tablero 8x8 en la mitad izquierda.
- Dibujar reloj grande `MM:SS` en la parte superior derecha.

No responsabilidad:
- Logica de ajedrez.
- Orquestacion de turnos.
- Lectura de botones.
- Control de tiempo interno.

El modulo no depende de `Chess` ni `ChessGame`; solo recibe datos crudos.

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
  - `renderClock(clockText)`
- `renderClock` usa glifos 8x16 precomputados en bytes hex.

## API Publica

### Constructor

```python
ChessDisplay(sda, scl, flipped=False, address=0x3C, i2cId=0)
```

### Metodos

| Metodo | Parametros | Retorno | Descripcion |
|--------|------------|---------|-------------|
| `renderBoard` | `board` | ninguno | Dibuja tablero 8x8 en zona izquierda y llama `show()` |
| `renderClock` | `clockText` | ninguno | Dibuja reloj grande `MM:SS` en zona derecha superior y llama `show()` |
| `flip` | ninguno | ninguno | Toggle de orientacion del tablero |

### Propiedad

| Propiedad | Tipo | Lectura | Escritura |
|-----------|------|---------|-----------|
| `flipped` | `bool` | si | si |

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

## Layout de Pantalla

```text
|<--- 64px --->|<--- 64px --->|
+==============+==============+
|              |   MM:SS      |
|   Tablero    |  (8x16 font) |
|   8x8        |              |
|              |   (libre)    |
+==============+==============+
```

- Zona izquierda (x=0..63): tablero completo 8x8.
- Zona derecha superior (x=64..127, y=0..15): reloj grande.
- Zona derecha inferior (x=64..127, y=16..63): reservada.

## Estrategia de Render (Performance)

### Tablero

- Escritura directa en `display.buffer` cuando el buffer es plano (`bytearray` MONO_VLSB).
- Tile de 8x8 dibujado como 8 bytes por casilla (alineado por paginas).
- Fallback a `pixel()` solo para mocks de pruebas (buffer 2D).

### Reloj

- Glifos 8x16 precomputados en hex.
- Se escriben dos paginas (page0 y page1) por columna, evitando `fill_rect`/`pixel` en flujo normal.
- Solo se limpia y redibuja la region `x=64..127, y=0..15`.

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

### `renderClock(clockText)`

1. Limpia solo region derecha superior (`64x16`).
2. Dibuja `clockText` con glifos 8x16.
3. Llama `show()`.

### `flip()`

- Cambia orientacion.
- No dibuja automaticamente.

## Ejemplos de Uso

```python
>>> from modules.chess import Chess
>>> from modules.chessdisplay import ChessDisplay
>>> chess = Chess()
>>> display = ChessDisplay(21, 22)
>>> display.renderBoard(chess.getBoard())
>>> display.renderClock("05:00")
>>> chess.play("e2-e4")
>>> display.renderBoard(chess.getBoard())
```

## Criterios de Aceptacion

- AC-01: instancia se crea con parametros default de I2C.
- AC-02: `renderBoard(board)` dibuja piezas en posiciones correctas y llama `show()`.
- AC-03: `renderClock('05:00')` dibuja pixeles en region derecha superior y llama `show()`.
- AC-04: `flip()` alterna orientacion y no llama `show()`.
- AC-05: en casilla oscura vacia existe patron de baja densidad (no relleno completo).
- AC-06: pieza negra se distingue claramente de pieza blanca del mismo tipo.

## Decisions Log

| Fecha | Decision | Razon |
|-------|----------|-------|
| 2026-02-06 | Reemplazar `setTable()+render()` por `renderBoard()` | API mas directa para orquestador |
| 2026-02-06 | Separar reloj en `renderClock()` | Permite refresco de tiempo sin redibujar tablero |
| 2026-02-06 | Fuente reloj en hex precomputado | Menor CPU por frame |
| 2026-02-06 | Mantener `ssd1306.py` y optimizar capa superior | Reusar driver estable y reducir complejidad |

## Fuera de alcance

- Auto-refresh interno con timer propio.
- Inyectar objeto `ChessClock` directamente en display.
- Animaciones de piezas.
- Multiples tamanos de fuente generales (solo reloj 8x16 por ahora).
