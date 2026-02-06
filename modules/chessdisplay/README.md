# ChessDisplay

Renderizador de tablero para OLED SSD1306 128x64 (I2C), optimizado para ESP32/MicroPython.

> v2.2: Validacion estricta + Codigo legible priorizado
> - Lanza `ValueError` si encuentra caracteres invalidos en board
> - Optimizacion de diccionario unificado mantiene legibilidad
> - Comentarios exhaustivos en funciones criticas

> v2.4: Panel lateral doble para relojes por jugador
> - `renderClock(clockText, color)` actualiza reloj por color (`w`/`b`)
> - Resalta en invertido el reloj del jugador en turno
> - Centro del panel muestra `B` (blancas) o `N` (negras) + numero de turnos

El modulo es solo de renderizado: no valida jugadas, no maneja entrada de usuario y no depende de `Chess` ni `ChessGame`.

## API

### Constructor

```python
ChessDisplay(sda, scl, address=0x3C, i2cId=0)
```

### Metodos

- `renderBoard(board)`
  - Dibuja el tablero en la mitad izquierda (64x64) y llama `show()`.
  - `board` debe ser `str` de 64 caracteres (indice 0 = a1, 63 = h8).
  - **Caracteres validos:**
    - `' '` (espacio): casilla vacia
    - `K,Q,R,B,N,P`: piezas blancas
    - `k,q,r,b,n,p`: piezas negras
  - **Lanza `ValueError`** si encuentra un caracter no reconocido

- `renderClock(clockText, color)`
  - Actualiza reloj `MM:SS` del jugador indicado por `color` (`'w'` o `'b'`).
  - Repinta el panel lateral y llama `show()`.

- `renderTurn(color)`
  - Actualiza jugador en turno (`'w'` o `'b'`) y repinta panel lateral.

- `renderTurnCount(turnCount)`
  - Actualiza numero de turnos y repinta panel lateral.

- `renderSidePanel(whiteClock, blackClock, activeColor, turnCount)`
  - Actualiza todo el panel lateral en una sola llamada.

## Uso con modulo Chess

```python
from modules.chess import Chess
from modules.chessdisplay import ChessDisplay

# Instancias base
chess = Chess()
display = ChessDisplay(21, 22)

# Render inicial de tablero y panel lateral
display.renderBoard(chess.getBoard())
display.renderSidePanel("05:00", "05:00", "w", 1)

# Tras un movimiento, actualizar tablero
chess.play("e2-e4")
display.renderBoard(chess.getBoard())
display.renderClock("04:58", "w")
display.renderTurn("b")
display.renderTurnCount(1)
```

## Layout actual

```text
|<--- 64px --->|<--- 64px --->|
+==============+==============+
|              |   03:00      |  <- reloj superior
|   Tablero    |              |
|   8x8        |  B   12      |  <- jugador en turno + turnos
|              |              |
|              |   02:58      |  <- reloj inferior
+==============+==============+
```

- Izquierda: tablero completo 8x8 (casillas de 8x8).
- Derecha: panel lateral completo (reloj superior, estado central, reloj inferior).

## Notas de rendimiento

- Tablero dibujado por escritura directa a `display.buffer` (tile 8x8 en bytes), evitando loops `pixel()` en el flujo normal.
- Patron oscuro estilo `*-*-*` para mantener lectura de casillas.
- Piezas negras en contorno ajustado (interior hueco) para mejor contraste en casillas oscuras.
- `renderClock()` usa glifos 8x16 precomputados en hex para minimizar trabajo por frame.
- Solo se redibuja el panel lateral cuando cambian relojes/turno/contador.

### Optimizaciones v2.1+

- **Diccionario unificado de piezas**: Un solo `_PIECE_COLS` con mayusculas (K,Q,R,B,N,P) para blancas y minusculas (k,q,r,b,n,p) para negras. Elimina lookups dobles y condicionales en `_renderBoard()`.
- **Reduccion de ramas**: La logica de renderizado ahora usa acceso directo `_PIECE_COLS[piece]` sin necesidad de `isupper()` ni transformacion `upper()`.
- **Codigo legible priorizado (v2.2)**: Funciones helper documentadas, variables descriptivas, comentarios exhaustivos en flujo critico. Legibilidad > brevedad.

Estas optimizaciones mejoran el rendimiento en ESP32, especialmente durante redraws frecuentes (animaciones de reloj, feedback de movimientos).

### Validacion v2.2+

El modulo ahora valida **estrictamente** los caracteres de entrada:
- Si `renderBoard()` encuentra un caracter que no es ` ` (espacio) ni una pieza valida (K/Q/R/B/N/P o k/q/r/b/n/p), **lanza `ValueError`** con mensaje descriptivo
- Esto previene renderizados incorrectos por datos corruptos
- Facilita debugging mostrando exactamente que caracter y en que posicion fallo

## Pruebas

```bash
uv run pytest tests/modules/chessdisplay/test_chess_display.py
```

## Version

2.4 - Febrero 2026
