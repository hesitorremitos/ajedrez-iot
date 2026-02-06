"""
Modulo orquestador de partidas de ajedrez para ESP32 (MicroPython).
Coordina el motor de reglas (Chess), dos relojes (ChessClock),
historial de movimientos, piezas capturadas y deteccion de fin de partida.
ChessGame es la unica interfaz publica para el usuario.
"""

from modules.chess import Chess
from modules.chessclock import ChessClock

# Orden de valor para piezas capturadas (descendente)
_PIECE_ORDER = "QRBNP"


class ChessGame:
    """
    Orquestador de partida de ajedrez.

    Crea y gestiona internamente instancias de Chess (motor de reglas)
    y ChessClock (2 relojes). Expone una API unificada para controlar
    la partida completa: movimientos, relojes, historial, undo, y
    deteccion de fin de partida.
    """

    def __init__(self, debug=False):
        """
        Inicializa el orquestador de partida.

        Args:
            debug: Habilita logs de diagnostico
        """
        self._debug = debug

        # Motor de reglas
        self._chess = Chess(debug=debug)

        # Relojes (uno por jugador)
        self._whiteClock = ChessClock(debug=debug)
        self._blackClock = ChessClock(debug=debug)

        # Estado de partida
        self._increment = 0
        self._history = []
        self._currentTurnMove = None
        self._moveStack = []
        self._capturedPieces = {"w": [], "b": []}
        self._gameOver = False
        self._gameOverReason = None
        self._gameOverWinner = None

        # Callbacks propios
        self._onTimeout = None
        self._onDraw = None
        self._onGameOver = None

        # Registrar handlers internos
        self._chess.onMove = self._onChessMove
        self._whiteClock.onTimeout = self._onWhiteTimeout
        self._blackClock.onTimeout = self._onBlackTimeout

    def _log(self, message):
        """Log de diagnostico interno."""
        if self._debug:
            print("[ChessGame]", message)

    # ==================== Callbacks propios ====================

    @property
    def onTimeout(self):
        return self._onTimeout

    @onTimeout.setter
    def onTimeout(self, callback):
        self._onTimeout = callback

    @property
    def onDraw(self):
        return self._onDraw

    @onDraw.setter
    def onDraw(self, callback):
        self._onDraw = callback

    @property
    def onGameOver(self):
        return self._onGameOver

    @onGameOver.setter
    def onGameOver(self, callback):
        self._onGameOver = callback

    # ==================== Callbacks delegados de Chess ====================

    @property
    def onCheck(self):
        return self._chess.onCheck

    @onCheck.setter
    def onCheck(self, callback):
        self._chess.onCheck = callback

    @property
    def onCheckmate(self):
        return self._chess.onCheckmate

    @onCheckmate.setter
    def onCheckmate(self, callback):
        self._chess.onCheckmate = callback

    @property
    def onStalemate(self):
        return self._chess.onStalemate

    @onStalemate.setter
    def onStalemate(self, callback):
        self._chess.onStalemate = callback

    # ==================== Handlers internos ====================

    def _onChessMove(self, moveStr, captured, isPromotion, isCastling, isEnPassant):
        """
        Handler interno para el callback onMove de Chess.
        Actualiza historial y piezas capturadas.
        """
        # Actualizar capturas
        if captured is not None:
            if captured.isupper():
                # Pieza blanca capturada por negras
                self._capturedPieces["b"].append(captured)
                self._sortCaptured("b")
            else:
                # Pieza negra capturada por blancas
                self._capturedPieces["w"].append(captured)
                self._sortCaptured("w")

        # Actualizar historial
        # Nota: cuando onMove se dispara, Chess ya cambio el turno.
        # Si ahora es turno de negras, blancas acaban de mover.
        # Si ahora es turno de blancas, negras acaban de mover.
        currentTurn = self._chess.getTurn()
        if currentTurn == "b":
            # Blancas acaban de mover
            self._currentTurnMove = moveStr
        else:
            # Negras acaban de mover
            if self._currentTurnMove is not None:
                self._history.append((self._currentTurnMove, moveStr))
                self._currentTurnMove = None
            else:
                # Caso edge: negras mueven primero (posicion custom)
                self._history.append(("", moveStr))

    def _sortCaptured(self, color):
        """Ordena piezas capturadas por valor descendente."""
        pieces = self._capturedPieces[color]
        pieces.sort(
            key=lambda p: _PIECE_ORDER.index(p.upper())
            if p.upper() in _PIECE_ORDER
            else 99
        )

    def _onWhiteTimeout(self):
        """Handler de timeout del reloj blanco."""
        self._handleTimeout("w")

    def _onBlackTimeout(self):
        """Handler de timeout del reloj negro."""
        self._handleTimeout("b")

    def _handleTimeout(self, loserColor):
        """Procesa el evento de timeout."""
        if self._gameOver:
            return
        self._gameOver = True
        winnerColor = "b" if loserColor == "w" else "w"
        self._gameOverReason = "timeout"
        self._gameOverWinner = winnerColor
        self._log("Timeout: %s lost on time, %s wins" % (loserColor, winnerColor))
        if self._onTimeout:
            self._onTimeout(loserColor)
        if self._onGameOver:
            self._onGameOver("timeout", winnerColor)

    # ==================== Control de Partida ====================

    def start(self, timeBase, increment=0):
        """
        Configura relojes e inicia la partida.

        Args:
            timeBase: int (ms). Tiempo base por jugador.
            increment: int (ms). Fischer increment por movimiento. Default 0.
        """
        self._increment = increment
        self._history = []
        self._currentTurnMove = None
        self._moveStack = []
        self._capturedPieces = {"w": [], "b": []}
        self._gameOver = False
        self._gameOverReason = None
        self._gameOverWinner = None

        # Configurar relojes
        self._whiteClock.start(timeBase)
        self._blackClock.reset(timeBase)

        self._log("Game started: timeBase=%d, increment=%d" % (timeBase, increment))

    def reset(self):
        """
        Reinicia todo al estado inicial para permitir una nueva partida.
        Despues de reset(), se debe llamar start() para iniciar.
        """
        self._chess.reset()
        self._history = []
        self._currentTurnMove = None
        self._moveStack = []
        self._capturedPieces = {"w": [], "b": []}
        self._gameOver = False
        self._gameOverReason = None
        self._gameOverWinner = None

        # Detener relojes
        self._whiteClock.pause()
        self._blackClock.pause()

        self._log("Game reset")

    def play(self, move):
        """
        Ejecuta un movimiento en la partida.

        Args:
            move: str. Formato: 'e2-e4', 'O-O', 'O-O-O', 'e7-e8=Q'

        Returns:
            bool: True si el movimiento se ejecuto, False si invalido o partida terminada
        """
        if self._gameOver:
            self._log("Play rejected: game is over")
            return False

        # Turno actual (antes de que Chess cambie turno)
        currentColor = self._chess.getTurn()

        # Guardar estado para undo
        undoState = self._saveUndoState()

        # Delegar a Chess (esto dispara _onChessMove si es valido)
        result = self._chess.play(move)
        if not result:
            self._log("Play rejected by Chess engine: %s" % move)
            return False

        # Movimiento valido - gestionar relojes
        if currentColor == "w":
            moverClock = self._whiteClock
            opponentClock = self._blackClock
        else:
            moverClock = self._blackClock
            opponentClock = self._whiteClock

        # Pausar reloj del jugador que movio
        moverClock.pause()

        # Aplicar Fischer increment
        if self._increment > 0:
            moverClock.addTime(self._increment)

        # Reanudar reloj del oponente
        opponentClock.resume()

        # Guardar estado de undo (ahora que se confirmo el movimiento)
        self._moveStack.append(undoState)

        # Evaluar fin de partida
        self._checkGameEnd(currentColor)

        self._log("Play executed: %s by %s" % (move, currentColor))
        return True

    def _saveUndoState(self):
        """Guarda el estado actual para undo."""
        return {
            "fen": self._chess.getFen(),
            "whiteTime": self._whiteClock.getTime(),
            "blackTime": self._blackClock.getTime(),
            "history": list(self._history),
            "currentTurnMove": self._currentTurnMove,
            "capturedPieces": {
                "w": list(self._capturedPieces["w"]),
                "b": list(self._capturedPieces["b"]),
            },
            "gameOver": self._gameOver,
        }

    def _checkGameEnd(self, lastMoveColor):
        """Evalua si la partida termino despues de un movimiento."""
        if self._chess.isCheckmate():
            self._gameOver = True
            self._gameOverReason = "checkmate"
            self._gameOverWinner = lastMoveColor
            self._log("Checkmate! %s wins" % lastMoveColor)
            if self._onGameOver:
                self._onGameOver("checkmate", lastMoveColor)

        elif self._chess.isStalemate():
            self._gameOver = True
            self._gameOverReason = "stalemate"
            self._gameOverWinner = None
            self._log("Stalemate!")
            if self._onGameOver:
                self._onGameOver("stalemate", None)

        elif self.isDraw():
            self._gameOver = True
            self._gameOverReason = "draw"
            self._gameOverWinner = None
            self._log("Draw!")
            if self._onDraw:
                self._onDraw()
            if self._onGameOver:
                self._onGameOver("draw", None)

    def undo(self):
        """
        Deshace el ultimo movimiento. Restaura tablero y tiempos de relojes.

        Returns:
            bool: True si se deshizo, False si no hay movimientos
        """
        if not self._moveStack:
            self._log("Undo rejected: no moves to undo")
            return False

        state = self._moveStack.pop()

        # Restaurar posicion
        self._chess.setFen(state["fen"])

        # Restaurar tiempos
        self._whiteClock.pause()
        self._blackClock.pause()
        self._whiteClock.setTime(state["whiteTime"])
        self._blackClock.setTime(state["blackTime"])

        # Restaurar historial y capturas
        self._history = state["history"]
        self._currentTurnMove = state["currentTurnMove"]
        self._capturedPieces = state["capturedPieces"]

        # Restaurar gameOver
        self._gameOver = state["gameOver"]
        if not self._gameOver:
            self._gameOverReason = None
            self._gameOverWinner = None

        # Reanudar reloj del turno actual
        currentTurn = self._chess.getTurn()
        if currentTurn == "w":
            self._whiteClock.resume()
        else:
            self._blackClock.resume()

        self._log("Undo executed, turn: %s" % currentTurn)
        return True

    # ==================== Consultas delegadas a Chess ====================

    def getLegalMoves(self, square):
        """
        Obtiene movimientos legales de la pieza en la casilla indicada.

        Args:
            square: Casilla en notacion algebraica (ej. 'e2')

        Returns:
            list: Lista de movimientos en formato ['e2-e3', 'e2-e4', ...]
        """
        return self._chess.getLegalMoves(square)

    def getPiece(self, square):
        """
        Obtiene la pieza en la casilla indicada.

        Args:
            square: Casilla en notacion algebraica (ej. 'e4')

        Returns:
            str: Caracter de la pieza o espacio si esta vacia
        """
        return self._chess.getPiece(square)

    def getBoard(self):
        """
        Retorna la representacion del tablero como lista de 64 caracteres.

        Returns:
            list: Lista de 64 caracteres
        """
        return self._chess.getBoard()

    def isCheck(self):
        """
        Verifica si el jugador del turno actual esta en jaque.

        Returns:
            bool
        """
        return self._chess.isCheck()

    def isCheckmate(self):
        """
        Verifica si el jugador actual esta en jaque mate.

        Returns:
            bool
        """
        return self._chess.isCheckmate()

    def isStalemate(self):
        """
        Verifica si la partida esta en ahogado.

        Returns:
            bool
        """
        return self._chess.isStalemate()

    def getTurn(self):
        """
        Devuelve el turno actual.

        Returns:
            str: 'w' para blancas, 'b' para negras
        """
        return self._chess.getTurn()

    # ==================== Consultas de Partida ====================

    def isDraw(self):
        """
        Verifica si la partida es tablas.
        Evalua regla de 50 movimientos y material insuficiente.

        Returns:
            bool
        """
        # Regla de 50 movimientos (100 half-moves)
        if self._chess._halfmoveClock >= 100:
            return True
        # Material insuficiente
        if self._chess.isInsufficientMaterial():
            return True
        return False

    def isGameOver(self):
        """
        Verifica si la partida termino por cualquier razon.

        Returns:
            bool
        """
        return self._gameOver

    def getHistory(self):
        """
        Devuelve el historial de movimientos.

        Returns:
            list: Formato [('e2-e4', 'e7-e5'), ('g1-f3', '')]
        """
        result = list(self._history)
        # Si hay un movimiento de blancas pendiente, agregar con vacio
        if self._currentTurnMove is not None:
            result.append((self._currentTurnMove, ""))
        return result

    def getCapturedPieces(self):
        """
        Obtiene las piezas capturadas durante la partida.

        Returns:
            dict: {"w": str, "b": str}
                  "w": piezas negras capturadas por blancas (minusculas)
                  "b": piezas blancas capturadas por negras (mayusculas)
        """
        return {
            "w": "".join(self._capturedPieces["w"]),
            "b": "".join(self._capturedPieces["b"]),
        }

    def getFen(self):
        """
        Exporta la posicion actual a notacion FEN completa (6 campos).

        Returns:
            str: FEN standard completo
        """
        return self._chess.getFen()

    def setFen(self, fen):
        """
        Carga una posicion desde notacion FEN.
        Llamar ANTES de start() para partidas con posicion custom.

        Args:
            fen: str. FEN standard (4 a 6 campos)
        """
        self._chess.setFen(fen)

    def getPgn(self, headers=None):
        """
        Exporta la partida a formato PGN.

        Args:
            headers: dict opcional con cabeceras PGN

        Returns:
            str: PGN completo con cabeceras y movimientos
        """
        parts = []

        # Cabeceras
        defaultHeaders = {
            "Event": "?",
            "Site": "?",
            "Date": "????.??.??",
            "Round": "?",
            "White": "?",
            "Black": "?",
        }
        if headers:
            defaultHeaders.update(headers)

        # Resultado
        result = self._getPgnResult()
        defaultHeaders["Result"] = result

        for key, value in defaultHeaders.items():
            parts.append('[%s "%s"]' % (key, value))

        parts.append("")

        # Movimientos
        history = self.getHistory()
        moveParts = []
        for i, turn in enumerate(history):
            moveNum = i + 1
            whiteMove = turn[0]
            blackMove = turn[1] if len(turn) > 1 else ""
            if whiteMove:
                moveParts.append("%d. %s" % (moveNum, whiteMove))
            if blackMove:
                moveParts.append(blackMove)

        moveParts.append(result)
        parts.append(" ".join(moveParts))

        return "\n".join(parts)

    def _getPgnResult(self):
        """Determina el resultado PGN segun estado de partida."""
        if not self._gameOver:
            return "*"
        if self._gameOverReason == "checkmate":
            return "1-0" if self._gameOverWinner == "w" else "0-1"
        if self._gameOverReason == "timeout":
            return "1-0" if self._gameOverWinner == "w" else "0-1"
        if self._gameOverReason in ("stalemate", "draw"):
            return "1/2-1/2"
        return "*"

    # ==================== Consultas de Relojes ====================

    def getTime(self, color):
        """
        Retorna tiempo restante en ms.

        Args:
            color: 'w' o 'b'

        Returns:
            int: tiempo restante en ms
        """
        clock = self._whiteClock if color == "w" else self._blackClock
        return clock.getTime()

    def getText(self, color):
        """
        Retorna tiempo restante en formato MM:SS.

        Args:
            color: 'w' o 'b'

        Returns:
            str: formato 'MM:SS'
        """
        clock = self._whiteClock if color == "w" else self._blackClock
        return clock.getText()

    def getSeconds(self, color):
        """
        Retorna tiempo restante en segundos (floor).

        Args:
            color: 'w' o 'b'

        Returns:
            int
        """
        clock = self._whiteClock if color == "w" else self._blackClock
        return clock.getSeconds()
