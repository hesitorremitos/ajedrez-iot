---
last_updated: "2026-02-06 16:10"
version: "2.1"
status: draft
author: Discovery Architect
---

# Chess Module - Documento de Requerimientos (v2.1)

> **Cambio mayor respecto a v1.0**: Chess pasa de ser un gestor de partida completo a un **motor puro de reglas**. La logica de partida (historial, undo, capturas, regla 50 movimientos, PGN, isGameOver) se mueve a `ChessGame`. Ver `CHESSGAME_REQUIREMENTS.md`.

## Descripcion General

Modulo de ajedrez llamado `Chess.py` para ESP32 (MicroPython) que **valida y ejecuta movimientos** en un tablero de ajedrez. Es un motor de reglas puro: conoce como se mueven las piezas, detecta jaque/mate/ahogado/material insuficiente, y mantiene el estado de la posicion (incluyendo FEN completo).

**No gestiona**: historial de movimientos, undo, piezas capturadas (tracking), PGN, regla de 50 movimientos como condicion de tablas, ni deteccion de fin de partida (`isGameOver`). Estas responsabilidades son de `ChessGame`.

## Restricciones Tecnicas

- Compatible con MicroPython para ESP32.
- Optimizar uso de memoria RAM y CPU.
- camelCase para todos los nombres de metodos y propiedades.
- Archivo: `modules/chess/Chess.py`
- Clase: `Chess`

---

## API Publica

### Metodos Principales de Juego

| Metodo | Parametros | Retorno | Descripcion |
|--------|------------|---------|-------------|
| `play` | `move: str` | `bool` | Valida y ejecuta un movimiento. Retorna True si exitoso, False si invalido. Dispara callbacks. **No registra historial ni guarda estado para undo.** |
| `getLegalMoves` | `square: str` | `list[str]` | Retorna lista de movimientos legales para la pieza en la casilla indicada |
| `getPiece` | `square: str` | `str` | Retorna la pieza en la casilla. Espacio vacio si no hay pieza |
| `getBoard` | ninguno | `list` | Retorna la representacion interna del tablero como lista de 64 caracteres. **Nuevo en v2.0.** |
| `reset` | ninguno | ninguno | Reinicia el tablero a la posicion inicial |

### Metodos de Estado FEN

| Metodo | Parametros | Retorno | Descripcion |
|--------|------------|---------|-------------|
| `setFen` | `fen: str` | ninguno | Carga una posicion desde notacion FEN (6 campos standard) |
| `getFen` | ninguno | `str` | Exporta la posicion actual a notacion FEN (6 campos standard) |
| `getTurn` | ninguno | `str` | Retorna el jugador en turno: `'w'` o `'b'` |
| `getHalfmoveClock` | ninguno | `int` | Retorna contador de medio-movimientos (campo 5 FEN) |
| `getLastPositionState` | ninguno | `str` | Ultimo estado de posicion evaluado: `'normal'`, `'check'`, `'checkmate'`, `'stalemate'` |

### Metodos de Verificacion de Estado (Posicion)

| Metodo | Parametros | Retorno | Descripcion |
|--------|------------|---------|-------------|
| `isCheck` | ninguno | `bool` | Indica si el jugador en turno esta en jaque |
| `isCheckmate` | ninguno | `bool` | Indica si hay jaque mate |
| `isStalemate` | ninguno | `bool` | Indica si hay ahogado (stalemate) |
| `isInsufficientMaterial` | ninguno | `bool` | Indica si hay material insuficiente para dar mate. **Nuevo como metodo publico en v2.0** (era `_isInsufficientMaterial`). |

---

## Metodos ELIMINADOS en v2.0

Los siguientes metodos se **mueven a ChessGame**:

| Metodo eliminado | Razon | Nuevo hogar |
|------------------|-------|-------------|
| `undo()` | Logica de partida, requiere historial de estados | `ChessGame.undo()` |
| `getHistory()` | Tracking de historial es responsabilidad de partida | `ChessGame.getHistory()` |
| `getPgn()` | Exporta partida completa, no posicion | `ChessGame.getPgn()` |
| `getCapturedPieces()` | Tracking de capturas es responsabilidad de partida | `ChessGame.getCapturedPieces()` |
| `isDraw()` | La regla de 50 movimientos es condicion de partida | `ChessGame.isDraw()` |
| `isGameOver()` | Orquesta condiciones de fin de partida | `ChessGame.isGameOver()` |

---

## Metodos NUEVOS en v2.0

### getBoard()

Retorna la representacion interna del tablero como lista de 64 caracteres.

- Indice 0 = a1, indice 63 = h8.
- Piezas blancas: `P, N, B, R, Q, K` (mayusculas).
- Piezas negras: `p, n, b, r, q, k` (minusculas).
- Casilla vacia: `' '` (espacio).

**Justificacion**: Este metodo existe porque parsear el FEN para extraer la posicion del tablero es un coste computacional innecesario en ESP32. `getBoard()` provee acceso directo O(1) a la representacion interna.

El implementador decide si retorna una copia de la lista (seguro pero aloca 64 chars) o la referencia directa (zero-allocation pero el consumidor no debe mutar).

### isInsufficientMaterial()

Antes era `_isInsufficientMaterial()` (privado). Ahora es publico porque `ChessGame.isDraw()` lo necesita.

Evalua si las piezas restantes en el tablero son insuficientes para dar mate:
- K vs K
- K vs K+B
- K vs K+N
- K+B vs K+B (alfiles del mismo color de casilla)

### Metodos agregados en v2.1

#### getHalfmoveClock()

Expone el contador de medio-movimientos para evitar que consumidores (como `ChessGame`) lean atributos privados.

#### getLastPositionState()

Expone el resultado de evaluacion de posicion mas reciente tras `play()`. Esto permite reutilizar la evaluacion de `checkmate/stalemate/check` sin recalcular en capas superiores.

---

## Callbacks

### Callbacks de posicion (se mantienen de v1.0)

| Callback | Cuando se ejecuta |
|----------|-------------------|
| `onCheck` | Despues de `play()`, si el jugador en turno queda en jaque |
| `onCheckmate` | Despues de `play()`, si hay jaque mate |
| `onStalemate` | Despues de `play()`, si hay ahogado |

Firma: `callback()` — sin parametros.

### Callback NUEVO en v2.0: onMove

Se dispara despues de cada `play()` exitoso, con detalles del movimiento ejecutado.

```python
def onMove(moveStr, captured, isPromotion, isCastling, isEnPassant):
    pass
```

Parametros:
- `moveStr`: str. Movimiento ejecutado (ej: `'e2-e4'`, `'O-O'`, `'e7-e8=Q'`).
- `captured`: str o None. Pieza capturada (ej: `'p'`, `'N'`). None si no hubo captura. En caso de en passant, es el peon capturado.
- `isPromotion`: bool. True si fue promocion de peon.
- `isCastling`: bool. True si fue enroque.
- `isEnPassant`: bool. True si fue captura al paso.

**Proposito**: Permite a `ChessGame` (u otro consumidor) reaccionar a movimientos sin necesidad de que `play()` retorne datos adicionales. Callbacks son zero-allocation si no hay listener registrado, lo cual es optimo para ESP32.

### Callbacks ELIMINADOS en v2.0

| Callback eliminado | Razon | Nuevo hogar |
|--------------------|-------|-------------|
| `onDraw` | Condicion de partida (regla 50 movs) | `ChessGame.onDraw` |
| `onGameOver` | Orquestacion de fin de partida | `ChessGame.onGameOver` |

### Orden de disparo de callbacks en play()

Despues de ejecutar un movimiento valido:
1. `onMove(moveStr, captured, isPromotion, isCastling, isEnPassant)` — siempre si hay listener.
2. Evaluacion de posicion:
   - Si checkmate → `onCheckmate()`.
   - Si stalemate → `onStalemate()`.
   - Si check (y no mate) → `onCheck()`.

---

## Estado interno SIMPLIFICADO en v2.0

### Se mantienen

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `_board` | `list[str]` | Tablero de 64 caracteres |
| `_turn` | `str` | `'w'` o `'b'` |
| `_castlingRights` | `str` | Formato `'KQkq'` |
| `_enPassantSquare` | `str` o `None` | Casilla en passant |
| `_halfmoveClock` | `int` | Contador para FEN campo 5 (se actualiza en play: reset en captura/peon, +1 en otros) |
| `_fullmoveNumber` | `int` | Numero de movimiento completo para FEN campo 6 (incrementa tras turno negro) |
| `_debug` | `bool` | Modo debug |

### Se eliminan

| Campo eliminado | Razon |
|-----------------|-------|
| `_history` | Movido a ChessGame |
| `_moveStack` | Movido a ChessGame |
| `_currentTurnMove` | Movido a ChessGame |
| `_capturedPieces` | Movido a ChessGame |
| `_onDraw` | Callback movido a ChessGame |
| `_onGameOver` | Callback movido a ChessGame |

### Se agregan

| Campo nuevo | Tipo | Descripcion |
|-------------|------|-------------|
| `_onMove` | `callable` o `None` | Callback onMove |

---

## Comportamiento de play() en v2.0

`play(move)` ejecuta un movimiento. Flujo simplificado:

1. Parsea el movimiento (o detecta enroque).
2. Valida legalidad (turno correcto, movimiento pseudo-legal, no deja rey en jaque).
3. Si invalido: retorna False.
4. Si valido:
   a. Ejecuta el movimiento en el tablero (mueve piezas, maneja en passant, promocion, enroque).
   b. Actualiza derechos de enroque.
   c. Actualiza casilla en passant.
   d. Actualiza `_halfmoveClock` (reset en captura/peon, +1 en otros).
   e. Cambia turno (`_switchTurn`).
   f. Dispara `onMove(moveStr, captured, isPromotion, isCastling, isEnPassant)`.
   g. Evalua posicion y dispara callbacks de posicion (onCheckmate, onStalemate, onCheck).
   h. Retorna True.

**Diferencia con v1.0**: No guarda estado para undo, no registra historial, no trackea capturas, no evalua isDraw ni isGameOver.

---

## Comportamiento de reset() en v2.0

`reset()` reinicia solo el estado de posicion:

1. Tablero a posicion inicial.
2. Turno: `'w'`.
3. Derechos de enroque: `'KQkq'`.
4. En passant: None.
5. `_halfmoveClock`: 0.
6. `_fullmoveNumber`: 1.

**Diferencia con v1.0**: No limpia historial, moveStack, ni capturedPieces (ya no existen en Chess).

---

## Notacion de Movimientos

Sin cambios respecto a v1.0.

| Tipo | Formato | Ejemplo |
|------|---------|---------|
| Movimiento normal | `origen-destino` | `e2-e4` |
| Captura | `origen-destino` | `e4-d5` |
| Promocion | `origen-destino=PIEZA` | `e7-e8=Q` |
| Enroque corto | `O-O` | `O-O` |
| Enroque largo | `O-O-O` | `O-O-O` |
| En passant | `origen-destino` | `e5-d6` |

---

## Reglas Implementadas

### Movimientos Especiales
- Enroque (corto y largo) con validacion de casillas no atacadas y derechos.
- Promocion de peon al llegar a ultima fila.
- Captura al paso (en passant).

### Evaluacion de Posicion
- Jaque (isCheck).
- Jaque mate (isCheckmate).
- Ahogado / stalemate (isStalemate).
- Material insuficiente (isInsufficientMaterial): K vs K, K vs K+B, K vs K+N, K+B vs K+B mismo color.

### Validaciones
- Validacion estricta de turno.
- Validar que el movimiento no deje al propio rey en jaque.
- Validar legalidad segun reglas de cada pieza.

---

## Funcionalidad Excluida (movida a ChessGame)

- Historial de movimientos (getHistory, _recordMove)
- Pila de undo (undo, _saveState, _restoreState, _moveStack)
- Tracking de piezas capturadas (getCapturedPieces, _capturedPieces)
- Exportacion PGN (getPgn)
- Regla de 50 movimientos como condicion de tablas (isDraw con halfmoveClock >= 100)
- Deteccion de fin de partida (isGameOver)
- Callbacks onDraw y onGameOver

---

## Modo Debug

Sin cambios respecto a v1.0.

- Propiedad `debug` (getter/setter).
- Parametro de constructor: `Chess(debug=False)`.
- Mensajes con prefijo `[Chess Debug]`.

---

## Renderizado del Tablero

Sin cambios: metodo `__str__` para representacion ASCII (para debug).

---

## Estructura de Archivos

```text
modules/
  CHESS_REQUIREMENTS.md          # Este documento
  chess/
    __init__.py                  # Exporta Chess
    Chess.py                     # Motor de reglas

tests/
  modules/
    chess/
      test_basic_moves.py
      test_special_moves.py
      test_check_checkmate.py
      test_stalemate_draw.py     # Actualizar: tests de regla 50 movs se migran a chessgame
      test_captured_pieces.py    # Migrar a chessgame
      test_fen_pgn_history.py    # Migrar tests de PGN, history y undo a chessgame. Mantener tests FEN
```

### Migracion de tests

Los siguientes tests deben **migrarse** a `tests/modules/chessgame/`:

| Test actual | Migrar | Mantener en chess |
|-------------|--------|-------------------|
| `test_stalemate_draw.py` — tests de stalemate | No | Si (evaluacion de posicion) |
| `test_stalemate_draw.py` — tests de regla 50 movs (`test_fifty_move_*`) | Si | No |
| `test_stalemate_draw.py` — callbacks de draw/gameover | Si | No |
| `test_stalemate_draw.py` — callback de stalemate | Parcial | Mantener callback de stalemate en Chess |
| `test_captured_pieces.py` — todos | Si | No |
| `test_fen_pgn_history.py` — tests de PGN | Si | No |
| `test_fen_pgn_history.py` — tests de history | Si | No |
| `test_fen_pgn_history.py` — tests de undo | Si | No |
| `test_fen_pgn_history.py` — tests de FEN | No | Si |
| `test_fen_pgn_history.py` — test de reset | Adaptar | Adaptar (reset ya no limpia historial) |

---

## Ejemplo de Uso (v2.0)

```python
from modules.chess import Chess

chess = Chess()

# Motor de reglas puro
chess.play('e2-e4')          # True
chess.getLegalMoves('d7')    # ['d7-d6', 'd7-d5']
chess.getTurn()              # 'b'
chess.isCheck()              # False
chess.getPiece('e4')         # 'P'
chess.getBoard()             # lista de 64 caracteres
chess.getFen()               # FEN completo con 6 campos

# Callbacks
chess.onMove = lambda move, cap, prom, castle, ep: print(f"Move: {move}")
chess.onCheck = lambda: print("Check!")
chess.onCheckmate = lambda: print("Checkmate!")

# isInsufficientMaterial (ahora publico)
chess.setFen("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
chess.isInsufficientMaterial()  # True (K vs K)

# Nota: NO hay undo(), getHistory(), getPgn(), getCapturedPieces(),
#       isDraw(), isGameOver(). Usar ChessGame para estas funcionalidades.
```

---

## Criterios de Aceptacion (v2.0)

### AC-01: play() retorna bool sin efectos secundarios de partida
- **Given** Chess en posicion inicial
- **When** se llama `play('e2-e4')`
- **Then** retorna True, tablero actualizado, turno cambia a 'b'. No hay historial ni estado de undo guardado.

### AC-02: onMove callback se dispara con detalles
- **Given** callback registrado en onMove y posicion con peon negro en d5
- **When** blancas juegan `play('e4-d5')` (captura)
- **Then** onMove recibe: `('e4-d5', 'p', False, False, False)`

### AC-03: onMove con en passant
- **Given** posicion con en passant posible
- **When** se ejecuta captura al paso
- **Then** onMove recibe: `(moveStr, capturedPawn, False, False, True)`

### AC-04: onMove con promocion
- **Given** peon blanco en e7, casilla e8 vacia
- **When** se juega `play('e7-e8=Q')`
- **Then** onMove recibe: `('e7-e8=Q', None, True, False, False)` (o captured si habia pieza)

### AC-05: onMove con enroque
- **Given** posicion donde enroque es legal
- **When** se juega `play('O-O')`
- **Then** onMove recibe: `('O-O', None, False, True, False)`

### AC-06: getBoard() retorna 64 caracteres
- **Given** Chess en posicion inicial
- **When** se llama `getBoard()`
- **Then** retorna lista de 64 caracteres con piezas en posiciones correctas. `board[0]` = 'R' (a1), `board[63]` = 'r' (h8).

### AC-07: isInsufficientMaterial() es publico
- **Given** posicion K vs K
- **When** se llama `isInsufficientMaterial()`
- **Then** retorna True

### AC-08: No hay undo, historial ni capturedPieces
- **Given** instancia de Chess
- **When** se intenta acceder a `undo()`, `getHistory()`, `getCapturedPieces()`, `getPgn()`, `isDraw()`, `isGameOver()`
- **Then** AttributeError (estos metodos no existen)

### AC-09: Callbacks de posicion se disparan en orden
- **Given** callbacks onMove, onCheckmate registrados, posicion de mate en 1
- **When** se ejecuta el mate
- **Then** primero se dispara onMove, luego onCheckmate

### AC-10: halfmoveClock se actualiza en play()
- **Given** Chess con halfmoveClock=0
- **When** se ejecuta movimiento sin captura ni peon (ej: caballo)
- **Then** halfmoveClock en FEN (campo 5) es 1

### AC-11: FEN roundtrip completo (6 campos)
- **Given** un FEN standard de 6 campos
- **When** se llama `setFen(fen)` y luego `getFen()`
- **Then** retorna el mismo FEN

### AC-12: reset() solo resetea posicion
- **Given** Chess con posicion modificada
- **When** se llama `reset()`
- **Then** tablero en posicion inicial, turno 'w', castling 'KQkq', enPassant None, halfmoveClock 0, fullmoveNumber 1

---

## Decisions Log

| Fecha | Decision | Alternativas | Razon |
|-------|----------|--------------|-------|
| 2025-01 | v1.0: Chess como gestor completo de partida | Separar motor y partida desde el inicio | Alcance inicial simplificado |
| 2026-02-06 | v2.0: Chess pasa a motor puro de reglas | Mantener todo en Chess; Chess + ChessGame con duplicacion | Separacion de responsabilidades para integrar ChessGame con relojes |
| 2026-02-06 | play() retorna solo bool | Dict con detalles; tupla | Callback onMove evita allocaciones (ESP32) |
| 2026-02-06 | getBoard() retorna lista de 64 chars | Parsear FEN; no exponer | Parsear FEN es coste innecesario en ESP32. Acceso directo O(1) |
| 2026-02-06 | isInsufficientMaterial() se hace publico | Dejar privado y duplicar en ChessGame | Reutilizar logica existente sin duplicacion |
| 2026-02-06 | halfmoveClock/fullmoveNumber se mantienen en Chess | Moverlos a ChessGame; FEN parcial | Son parte del FEN standard. Chess los actualiza como datos de posicion. ChessGame usa el dato para evaluar regla 50 |
| 2026-02-06 | onMove callback con 5 parametros | Callback simple; retornar dict | Maximo detalle sin allocaciones. Parametros son primitivos |
| 2026-02-06 | Exponer `getHalfmoveClock()` en API publica | Leer `_halfmoveClock` desde fuera | Mejor encapsulacion y menor acoplamiento |
| 2026-02-06 | Exponer `getLastPositionState()` en API publica | Recalcular estado en `ChessGame` | Evita trabajo duplicado por movimiento (CPU) |

## Observaciones y decisiones diferidas

- **Retorno de getBoard() (copia vs referencia)**: El implementador decide si retorna una copia de la lista (seguro, aloca 64 chars) o referencia directa (zero-allocation, riesgo de mutacion externa). Para ESP32, referencia es preferible si el consumidor es confiable (ChessGame).
- **Migracion de tests**: Los tests afectados deben migrarse a `tests/modules/chessgame/` cuando se implemente ChessGame. Durante la transicion, puede ser necesario mantener tests temporalmente en ambos lados.
