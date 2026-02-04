# Chess Module - Documento de Requerimientos

## Descripcion General

Desarrollar un modulo de ajedrez llamado `Chess.py` para ESP32 (MicroPython) que valide movimientos y gestione el estado de una partida. El modulo debe estar fuertemente inspirado en la libreria ubicada en `test1/chess.py` del repositorio https://github.com/shuki25/smart-chessboard-upython, adaptando su logica y funcionalidad a los requerimientos especificos aqui definidos.

## Restricciones Tecnicas

- El modulo debe ser compatible con MicroPython para ESP32
- Debe optimizar el uso de memoria RAM y CPU considerando las limitaciones del microcontrolador
- Usar camelCase para todos los nombres de metodos y propiedades
- El archivo debe ubicarse en: `modules/Chess.py`
- Nombre de la clase: `Chess`

---

## API Publica

### Metodos Principales de Juego

| Metodo | Parametros | Retorno | Descripcion |
|--------|------------|---------|-------------|
| `play` | `move: str` | `bool` | Ejecuta un movimiento en notacion algebraica. Retorna True si exitoso, False si invalido |
| `getLegalMoves` | `square: str` | `list[str]` | Retorna lista de movimientos legales para la pieza en la casilla indicada. Formato: lista de movimientos completos |
| `getPiece` | `square: str` | `str` | Retorna la pieza en la casilla especificada. Espacio vacio si no hay pieza |
| `undo` | ninguno | `bool` | Deshace el ultimo movimiento realizado. Retorna True si exitoso |
| `reset` | ninguno | ninguno | Reinicia la partida a la posicion inicial |

### Metodos de Estado FEN/PGN

| Metodo | Parametros | Retorno | Descripcion |
|--------|------------|---------|-------------|
| `setFen` | `fen: str` | ninguno | Carga una posicion desde notacion FEN |
| `getFen` | ninguno | `str` | Exporta la posicion actual a notacion FEN |
| `getPgn` | `headers: dict` (opcional) | `str` | Exporta la partida completa a formato PGN |
| `getHistory` | ninguno | `list[tuple]` | Retorna historial de movimientos en tuplas por turno: [(blancas, negras), ...] |
| `getTurn` | ninguno | `str` | Retorna el jugador en turno: 'w' para blancas, 'b' para negras |

### Metodos de Verificacion de Estado

| Metodo | Parametros | Retorno | Descripcion |
|--------|------------|---------|-------------|
| `isCheck` | ninguno | `bool` | Indica si el jugador en turno esta en jaque |
| `isCheckmate` | ninguno | `bool` | Indica si hay jaque mate |
| `isStalemate` | ninguno | `bool` | Indica si hay ahogado (stalemate) |
| `isDraw` | ninguno | `bool` | Indica si hay tablas (por regla 50 movs o material insuficiente) |
| `isGameOver` | ninguno | `bool` | Indica si la partida ha terminado |

### Callbacks Opcionales

Los callbacks deben poder registrarse como funciones que se ejecutan automaticamente despues de cada llamada a `play()` cuando corresponda:

| Callback | Cuando se ejecuta |
|----------|-------------------|
| `onCheck` | Cuando el jugador en turno queda en jaque |
| `onCheckmate` | Cuando hay jaque mate |
| `onStalemate` | Cuando hay ahogado |
| `onDraw` | Cuando hay tablas |
| `onGameOver` | Cuando la partida termina (cualquier razon) |

El agente debe determinar la mejor forma de registrar estos callbacks (setters, constructor, o metodo dedicado).

---

## Notacion de Movimientos

### Formato General
- Usar guion como separador: `e2-e4` (no `e2e4`)
- Casillas en notacion algebraica estandar: columna (a-h) + fila (1-8)

### Movimientos Especiales

| Tipo | Formato | Ejemplo |
|------|---------|---------|
| Movimiento normal | `origen-destino` | `e2-e4` |
| Captura | `origen-destino` (igual) | `e4-d5` |
| Promocion | `origen-destino=PIEZA` | `e7-e8=Q` |
| Enroque corto | `O-O` | `O-O` |
| Enroque largo | `O-O-O` | `O-O-O` |
| En passant | `origen-destino` (igual) | `e5-d6` |

### Piezas (notacion interna)
- Mayusculas: piezas blancas (P, N, B, R, Q, K)
- Minusculas: piezas negras (p, n, b, r, q, k)
- Espacio vacio: ` ` (caracter espacio)

---

## Reglas a Implementar

### Movimientos Especiales
- Enroque (corto y largo) con validacion de casillas no atacadas y derechos de enroque
- Promocion de peon al llegar a ultima fila
- Captura al paso (en passant)

### Condiciones de Fin de Partida
- Jaque mate
- Ahogado (stalemate)
- Tablas por regla de 50 movimientos
- Tablas por material insuficiente (K vs K, K vs K+B, K vs K+N, K+B vs K+B mismo color)

### Validaciones
- Validacion estricta de turno: solo se pueden mover piezas del jugador en turno
- Validar que el movimiento no deje al propio rey en jaque
- Validar legalidad de todos los movimientos segun reglas de cada pieza

---

## Caracteristicas Adicionales

### Modo Debug
- Incluir modo debug activable/desactivable
- Cuando esta activo, imprimir mensajes de diagnostico
- Por defecto: desactivado
- El agente debe determinar la mejor forma de activarlo (propiedad, metodo, o parametro de constructor)

### Renderizado del Tablero
- Incluir metodo `__str__` para representacion ASCII del tablero (para debug)
- No incluir renderizado con Segoe Chess Font (eliminar del original)

### Historial de Movimientos
- Almacenar todos los movimientos de la partida
- Formato de tuplas por turno: `[('e2-e4', 'e7-e5'), ('g1-f3', 'b8-c6')]`
- Si las negras no han movido en el ultimo turno, la tupla tendra string vacio: `('d2-d4', '')`

---

## Funcionalidad a NO Incluir (Eliminar del Original)

- Renderizado con Segoe Chess Font
- Metodo para obtener todos los movimientos del jugador en turno (getAllMoves) - por optimizacion de memoria
- Constantes de fuentes graficas (SEGOE_CHESS_FONT_*)

---

## Consideraciones de Implementacion

El agente desarrollador debe:

1. Analizar la libreria original en `test1/chess.py` como base de referencia
2. Adaptar la logica de generacion de movimientos legales
3. Adaptar la logica de validacion de movimientos
4. Implementar el sistema de callbacks de forma eficiente para ESP32
5. Optimizar el uso de memoria donde sea posible
6. Mantener la representacion interna del tablero como lista de 64 caracteres (indice 0 = a1, indice 63 = h8)
7. Decidir la mejor forma de implementar funcionalidad de undo (puede requerir almacenar estados anteriores o reconstruir desde historial)

---

## Ejemplo de Uso Esperado

El modulo debe permitir interacciones como:

```
chess = Chess()
chess.play('e2-e4')  # True
chess.getLegalMoves('d7')  # ['d7-d6', 'd7-d5']
chess.getTurn()  # 'b'
chess.isCheck()  # False
chess.getPiece('e4')  # 'P'
chess.undo()  # True
chess.getFen()  # posicion inicial
```

---

## Version
- Version del documento: 1.0
- Fecha: Enero 2025
