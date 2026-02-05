"""
Modulo de ajedrez para ESP32 (MicroPython).
Valida movimientos y gestiona el estado de la partida.
Optimizado para entornos con poca memoria.
"""


class Chess:
    """
    Gestor de partida con validacion de movimientos y seguimiento del estado.

    Representacion del tablero: lista de 64 caracteres
    Indice 0 = a1, indice 63 = h8
    Piezas blancas: P, N, B, R, Q, K (mayusculas)
    Piezas negras: p, n, b, r, q, k (minusculas)
    Casilla vacia: ' ' (espacio)
    """

    # Posicion inicial del tablero
    INITIAL_BOARD = list(
        "RNBQKBNR"  # Fila 1 (a1-h1)
        + "PPPPPPPP"  # Fila 2 (a2-h2)
        + "        "  # Fila 3
        + "        "  # Fila 4
        + "        "  # Fila 5
        + "        "  # Fila 6
        + "pppppppp"  # Fila 7 (a7-h7)
        + "rnbqkbnr"  # Fila 8 (a8-h8)
    )

    INITIAL_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    def __init__(self, debug=False):
        """
        Inicializa una nueva partida de ajedrez.

        Args:
            debug: Habilita modo debug para mensajes de diagnostico
        """
        self._debug = debug
        self._board = None
        self._turn = None  # 'w' o 'b'
        self._castlingRights = None  # formato 'KQkq'
        self._enPassantSquare = None  # ej: 'e3' o None
        self._halfmoveClock = None  # regla de 50 movimientos
        self._fullmoveNumber = None
        self._history = []  # Lista de tuplas [(mov_blancas, mov_negras), ...]
        self._moveStack = []  # Pila de estados para deshacer
        self._currentTurnMove = None  # Movimiento de blancas pendiente de negras
        self._capturedPieces = None  # Piezas capturadas {"w": [], "b": []}

        # Callbacks
        self._onCheck = None
        self._onCheckmate = None
        self._onStalemate = None
        self._onDraw = None
        self._onGameOver = None

        self.reset()

    # ==================== Setters de propiedades para callbacks ====================

    @property
    def onCheck(self):
        return self._onCheck

    @onCheck.setter
    def onCheck(self, callback):
        self._onCheck = callback

    @property
    def onCheckmate(self):
        return self._onCheckmate

    @onCheckmate.setter
    def onCheckmate(self, callback):
        self._onCheckmate = callback

    @property
    def onStalemate(self):
        return self._onStalemate

    @onStalemate.setter
    def onStalemate(self, callback):
        self._onStalemate = callback

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

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value

    # ==================== Metodos auxiliares ====================

    def _log(self, message):
        """Imprime mensaje de debug si esta habilitado."""
        if self._debug:
            print(f"[Chess Debug] {message}")

    def _squareToIndex(self, square):
        """
        Convierte notacion algebraica a indice del tablero.
        a1 = 0, h1 = 7, a8 = 56, h8 = 63
        """
        if len(square) != 2:
            return -1
        col = ord(square[0].lower()) - ord("a")
        row = int(square[1]) - 1
        if 0 <= col <= 7 and 0 <= row <= 7:
            return row * 8 + col
        return -1

    def _indexToSquare(self, index):
        """Convierte indice del tablero a notacion algebraica."""
        if 0 <= index <= 63:
            col = chr(ord("a") + (index % 8))
            row = str((index // 8) + 1)
            return col + row
        return None

    def _getFile(self, index):
        """Obtiene la columna (archivo) 0-7 a partir del indice."""
        return index % 8

    def _getRank(self, index):
        """Obtiene la fila (rank) 0-7 a partir del indice."""
        return index // 8

    def _isWhitePiece(self, piece):
        """Verifica si la pieza es blanca (mayuscula)."""
        return piece.isupper()

    def _isBlackPiece(self, piece):
        """Verifica si la pieza es negra (minuscula)."""
        return piece.islower()

    def _isPieceOfCurrentTurn(self, piece):
        """Verifica si la pieza pertenece al turno actual."""
        if piece == " ":
            return False
        if self._turn == "w":
            return self._isWhitePiece(piece)
        else:
            return self._isBlackPiece(piece)

    def _isEnemyPiece(self, piece):
        """Verifica si la pieza pertenece al oponente."""
        if piece == " ":
            return False
        if self._turn == "w":
            return self._isBlackPiece(piece)
        else:
            return self._isWhitePiece(piece)

    def _findKing(self, color):
        """Encuentra la posicion del rey del color indicado."""
        king = "K" if color == "w" else "k"
        for i, piece in enumerate(self._board):
            if piece == king:
                return i
        return -1

    def _saveState(self):
        """Guarda el estado actual para deshacer."""
        state = {
            "board": self._board[:],
            "turn": self._turn,
            "castlingRights": self._castlingRights,
            "enPassantSquare": self._enPassantSquare,
            "halfmoveClock": self._halfmoveClock,
            "fullmoveNumber": self._fullmoveNumber,
            "history": [tuple(t) for t in self._history],
            "currentTurnMove": self._currentTurnMove,
            "capturedPieces": {
                "w": self._capturedPieces["w"][:],
                "b": self._capturedPieces["b"][:],
            },
        }
        self._moveStack.append(state)

    def _restoreState(self, state):
        """Restaura el estado del juego desde un estado guardado."""
        self._board = state["board"]
        self._turn = state["turn"]
        self._castlingRights = state["castlingRights"]
        self._enPassantSquare = state["enPassantSquare"]
        self._halfmoveClock = state["halfmoveClock"]
        self._fullmoveNumber = state["fullmoveNumber"]
        self._history = [list(t) for t in state["history"]]
        self._currentTurnMove = state["currentTurnMove"]
        self._capturedPieces = state["capturedPieces"]

    # ==================== Deteccion de ataques ====================

    def _isSquareAttackedBy(self, squareIndex, byColor):
        """Verifica si una casilla esta atacada por el color indicado."""
        attackerIsWhite = byColor == "w"

        # Ataques de peones
        pawn = "P" if attackerIsWhite else "p"
        pawnDir = (
            -1 if attackerIsWhite else 1
        )  # Direccion desde donde atacan los peones
        file = self._getFile(squareIndex)
        rank = self._getRank(squareIndex)

        # Los peones atacan en diagonal
        for df in [-1, 1]:
            attackerFile = file + df
            attackerRank = rank + pawnDir
            if 0 <= attackerFile <= 7 and 0 <= attackerRank <= 7:
                attackerIndex = attackerRank * 8 + attackerFile
                if self._board[attackerIndex] == pawn:
                    return True

        # Ataques de caballos
        knight = "N" if attackerIsWhite else "n"
        knightMoves = [
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        ]
        for dr, df in knightMoves:
            attackerRank = rank + dr
            attackerFile = file + df
            if 0 <= attackerFile <= 7 and 0 <= attackerRank <= 7:
                attackerIndex = attackerRank * 8 + attackerFile
                if self._board[attackerIndex] == knight:
                    return True

        # Ataques de rey (casillas adyacentes)
        king = "K" if attackerIsWhite else "k"
        for dr in [-1, 0, 1]:
            for df in [-1, 0, 1]:
                if dr == 0 and df == 0:
                    continue
                attackerRank = rank + dr
                attackerFile = file + df
                if 0 <= attackerFile <= 7 and 0 <= attackerRank <= 7:
                    attackerIndex = attackerRank * 8 + attackerFile
                    if self._board[attackerIndex] == king:
                        return True

        # Ataques de torre/reina (lineas rectas)
        rook = "R" if attackerIsWhite else "r"
        queen = "Q" if attackerIsWhite else "q"
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dr, df in directions:
            r, f = rank + dr, file + df
            while 0 <= r <= 7 and 0 <= f <= 7:
                idx = r * 8 + f
                piece = self._board[idx]
                if piece != " ":
                    if piece == rook or piece == queen:
                        return True
                    break  # Bloqueado por otra pieza
                r += dr
                f += df

        # Ataques de alfil/reina (diagonales)
        bishop = "B" if attackerIsWhite else "b"
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dr, df in directions:
            r, f = rank + dr, file + df
            while 0 <= r <= 7 and 0 <= f <= 7:
                idx = r * 8 + f
                piece = self._board[idx]
                if piece != " ":
                    if piece == bishop or piece == queen:
                        return True
                    break  # Bloqueado por otra pieza
                r += dr
                f += df

        return False

    def _isInCheck(self, color):
        """Verifica si el rey del color indicado esta en jaque."""
        kingIndex = self._findKing(color)
        if kingIndex == -1:
            return False
        enemyColor = "b" if color == "w" else "w"
        return self._isSquareAttackedBy(kingIndex, enemyColor)

    # ==================== Generacion de movimientos ====================

    def _generatePseudoLegalMoves(self, fromIndex):
        """
        Genera movimientos pseudo-legales para una pieza (sin verificar jaque).
        Retorna una lista de indices destino.
        """
        piece = self._board[fromIndex]
        if piece == " ":
            return []

        moves = []
        pieceType = piece.upper()
        isWhite = piece.isupper()
        file = self._getFile(fromIndex)
        rank = self._getRank(fromIndex)

        if pieceType == "P":
            moves.extend(self._generatePawnMoves(fromIndex, isWhite, file, rank))
        elif pieceType == "N":
            moves.extend(self._generateKnightMoves(fromIndex, isWhite, file, rank))
        elif pieceType == "B":
            moves.extend(self._generateBishopMoves(fromIndex, isWhite, file, rank))
        elif pieceType == "R":
            moves.extend(self._generateRookMoves(fromIndex, isWhite, file, rank))
        elif pieceType == "Q":
            moves.extend(self._generateQueenMoves(fromIndex, isWhite, file, rank))
        elif pieceType == "K":
            moves.extend(self._generateKingMoves(fromIndex, isWhite, file, rank))

        return moves

    def _generatePawnMoves(self, fromIndex, isWhite, file, rank):
        """Genera movimientos de peon."""
        moves = []
        direction = 1 if isWhite else -1
        startRank = 1 if isWhite else 6

        # Avance simple
        toRank = rank + direction
        if 0 <= toRank <= 7:
            toIndex = toRank * 8 + file
            if self._board[toIndex] == " ":
                moves.append(toIndex)

                # Avance doble desde la posicion inicial
                if rank == startRank:
                    toRank2 = rank + 2 * direction
                    toIndex2 = toRank2 * 8 + file
                    if self._board[toIndex2] == " ":
                        moves.append(toIndex2)

        # Capturas (incluye en passant)
        for df in [-1, 1]:
            toFile = file + df
            if 0 <= toFile <= 7 and 0 <= toRank <= 7:
                toIndex = toRank * 8 + toFile
                targetPiece = self._board[toIndex]

                # Captura normal
                if targetPiece != " ":
                    if (isWhite and targetPiece.islower()) or (
                        not isWhite and targetPiece.isupper()
                    ):
                        moves.append(toIndex)

                # Captura en passant
                epSquare = self._indexToSquare(toIndex)
                if epSquare == self._enPassantSquare:
                    moves.append(toIndex)

        return moves

    def _generateKnightMoves(self, fromIndex, isWhite, file, rank):
        """Genera movimientos de caballo."""
        moves = []
        offsets = [
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        ]

        for dr, df in offsets:
            toRank = rank + dr
            toFile = file + df
            if 0 <= toRank <= 7 and 0 <= toFile <= 7:
                toIndex = toRank * 8 + toFile
                targetPiece = self._board[toIndex]
                if (
                    targetPiece == " "
                    or (isWhite and targetPiece.islower())
                    or (not isWhite and targetPiece.isupper())
                ):
                    moves.append(toIndex)

        return moves

    def _generateSlidingMoves(self, fromIndex, isWhite, file, rank, directions):
        """Genera movimientos para piezas deslizantes (alfil, torre, reina)."""
        moves = []

        for dr, df in directions:
            r, f = rank + dr, file + df
            while 0 <= r <= 7 and 0 <= f <= 7:
                toIndex = r * 8 + f
                targetPiece = self._board[toIndex]

                if targetPiece == " ":
                    moves.append(toIndex)
                elif (isWhite and targetPiece.islower()) or (
                    not isWhite and targetPiece.isupper()
                ):
                    moves.append(toIndex)
                    break  # Puede capturar pero no continuar
                else:
                    break  # Bloqueado por pieza propia

                r += dr
                f += df

        return moves

    def _generateBishopMoves(self, fromIndex, isWhite, file, rank):
        """Genera movimientos de alfil (diagonales)."""
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        return self._generateSlidingMoves(fromIndex, isWhite, file, rank, directions)

    def _generateRookMoves(self, fromIndex, isWhite, file, rank):
        """Genera movimientos de torre (lineas rectas)."""
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        return self._generateSlidingMoves(fromIndex, isWhite, file, rank, directions)

    def _generateQueenMoves(self, fromIndex, isWhite, file, rank):
        """Genera movimientos de reina (torre + alfil)."""
        directions = [
            (0, 1),
            (0, -1),
            (1, 0),
            (-1, 0),
            (1, 1),
            (1, -1),
            (-1, 1),
            (-1, -1),
        ]
        return self._generateSlidingMoves(fromIndex, isWhite, file, rank, directions)

    def _generateKingMoves(self, fromIndex, isWhite, file, rank):
        """Genera movimientos de rey (una casilla en cualquier direccion)."""
        moves = []

        for dr in [-1, 0, 1]:
            for df in [-1, 0, 1]:
                if dr == 0 and df == 0:
                    continue
                toRank = rank + dr
                toFile = file + df
                if 0 <= toRank <= 7 and 0 <= toFile <= 7:
                    toIndex = toRank * 8 + toFile
                    targetPiece = self._board[toIndex]
                    if (
                        targetPiece == " "
                        or (isWhite and targetPiece.islower())
                        or (not isWhite and targetPiece.isupper())
                    ):
                        moves.append(toIndex)

        return moves

    def _canCastle(self, kingSide, color):
        """Verifica si el enroque es legal."""
        isWhite = color == "w"

        # Verificar derechos de enroque
        if isWhite:
            right = "K" if kingSide else "Q"
        else:
            right = "k" if kingSide else "q"

        if right not in self._castlingRights:
            return False

        # Verificar si el rey esta en jaque
        if self._isInCheck(color):
            return False

        # Obtener posiciones base
        rank = 0 if isWhite else 7
        kingFile = 4
        kingIndex = rank * 8 + kingFile

        if kingSide:
            # Lado rey: rey e->g, torre h->f
            rookFile = 7
            pathFiles = [5, 6]  # f y g deben estar vacias
            kingPathFiles = [4, 5, 6]  # e, f, g no deben estar atacadas
        else:
            # Lado dama: rey e->c, torre a->d
            rookFile = 0
            pathFiles = [1, 2, 3]  # b, c, d deben estar vacias
            kingPathFiles = [2, 3, 4]  # c, d, e no deben estar atacadas

        rookIndex = rank * 8 + rookFile
        rook = "R" if isWhite else "r"

        # Verificar que la torre este en su sitio
        if self._board[rookIndex] != rook:
            return False

        # Verificar que el camino este libre
        for f in pathFiles:
            idx = rank * 8 + f
            if self._board[idx] != " ":
                return False

        # Verificar que el camino del rey no este atacado
        enemyColor = "b" if isWhite else "w"
        for f in kingPathFiles:
            idx = rank * 8 + f
            if self._isSquareAttackedBy(idx, enemyColor):
                return False

        return True

    def _isMoveLegal(self, fromIndex, toIndex, promotion=None):
        """
        Verifica si un movimiento es totalmente legal (incluye no dejar al rey en jaque).
        """
        piece = self._board[fromIndex]
        if piece == " ":
            return False

        # Verificar si es el turno correcto
        if not self._isPieceOfCurrentTurn(piece):
            return False

        # Generar movimientos pseudo-legales
        pseudoMoves = self._generatePseudoLegalMoves(fromIndex)
        if toIndex not in pseudoMoves:
            return False

        # Verificar validez de promocion
        pieceType = piece.upper()
        toRank = self._getRank(toIndex)
        isWhite = piece.isupper()

        if pieceType == "P":
            promotionRank = 7 if isWhite else 0
            if toRank == promotionRank:
                if promotion is None:
                    return False  # Debe especificar pieza de promocion
                if promotion.upper() not in "QRBN":
                    return False
            elif promotion is not None:
                return False  # No se puede promover si no llega a la ultima fila

        # Simular movimiento y comprobar jaque
        savedBoard = self._board[:]
        savedEp = self._enPassantSquare

        # Hacer el movimiento temporalmente
        self._board[toIndex] = piece
        self._board[fromIndex] = " "

        # Manejar captura en passant
        if pieceType == "P" and self._indexToSquare(toIndex) == savedEp:
            capturedPawnRank = 4 if isWhite else 3
            capturedPawnIndex = capturedPawnRank * 8 + self._getFile(toIndex)
            self._board[capturedPawnIndex] = " "

        # Manejar promocion
        if pieceType == "P" and toRank == (7 if isWhite else 0) and promotion:
            self._board[toIndex] = promotion.upper() if isWhite else promotion.lower()

        # Verificar si el propio rey queda en jaque
        color = "w" if isWhite else "b"
        inCheck = self._isInCheck(color)

        # Restaurar tablero
        self._board = savedBoard
        self._enPassantSquare = savedEp

        return not inCheck

    # ==================== Metodos publicos ====================

    def reset(self):
        """Reinicia la partida a la posicion inicial."""
        self._board = self.INITIAL_BOARD[:]
        self._turn = "w"
        self._castlingRights = "KQkq"
        self._enPassantSquare = None
        self._halfmoveClock = 0
        self._fullmoveNumber = 1
        self._history = []
        self._moveStack = []
        self._currentTurnMove = None
        self._capturedPieces = {"w": [], "b": []}
        self._log("Game reset to initial position")

    def play(self, move):
        """
        Ejecuta un movimiento en notacion algebraica.

        Args:
            move: Formato 'e2-e4', 'O-O', 'O-O-O', o 'e7-e8=Q'
                Nota: las capturas usan '-' (no 'x').

        Returns:
            bool: True si el movimiento se ejecuto, False si es invalido
        """
        self._log(f"Attempting move: {move}")

        # Manejar enroque
        if move == "O-O":
            return self._playCastling(kingSide=True)
        elif move == "O-O-O":
            return self._playCastling(kingSide=False)

        # Parsear el movimiento
        parsed = self._parseMove(move)
        if parsed is None:
            self._log(f"Failed to parse move: {move}")
            return False

        fromSquare, toSquare, promotion = parsed
        fromIndex = self._squareToIndex(fromSquare)
        toIndex = self._squareToIndex(toSquare)

        if fromIndex == -1 or toIndex == -1:
            self._log(f"Invalid square in move: {move}")
            return False

        # Validar el movimiento
        if not self._isMoveLegal(fromIndex, toIndex, promotion):
            self._log(f"Illegal move: {move}")
            return False

        # Guardar estado para deshacer
        self._saveState()

        # Ejecutar el movimiento
        self._executeMove(fromIndex, toIndex, promotion, move)

        # Disparar callbacks
        self._triggerCallbacks()

        self._log(f"Move executed: {move}")
        return True

    def _parseMove(self, move):
        """Parsea el string de movimiento en componentes."""
        move = move.strip()

        # Verificar promocion
        promotion = None
        if "=" in move:
            parts = move.split("=")
            if len(parts) != 2 or len(parts[1]) != 1:
                return None
            move = parts[0]
            promotion = parts[1]

        # Parsear origen-destino
        if "-" not in move:
            return None

        parts = move.split("-")
        if len(parts) != 2:
            return None

        fromSquare = parts[0].lower()
        toSquare = parts[1].lower()

        if len(fromSquare) != 2 or len(toSquare) != 2:
            return None

        return (fromSquare, toSquare, promotion)

    def _playCastling(self, kingSide):
        """Ejecuta un enroque."""
        color = self._turn

        if not self._canCastle(kingSide, color):
            self._log(
                f"Castling {'king-side' if kingSide else 'queen-side'} not allowed"
            )
            return False

        # Guardar estado para deshacer
        self._saveState()

        isWhite = color == "w"
        rank = 0 if isWhite else 7

        kingFrom = rank * 8 + 4
        rookFrom = rank * 8 + (7 if kingSide else 0)
        kingTo = rank * 8 + (6 if kingSide else 2)
        rookTo = rank * 8 + (5 if kingSide else 3)

        # Mover las piezas
        king = self._board[kingFrom]
        rook = self._board[rookFrom]

        self._board[kingFrom] = " "
        self._board[rookFrom] = " "
        self._board[kingTo] = king
        self._board[rookTo] = rook

        # Actualizar derechos de enroque
        if isWhite:
            self._castlingRights = self._castlingRights.replace("K", "").replace(
                "Q", ""
            )
        else:
            self._castlingRights = self._castlingRights.replace("k", "").replace(
                "q", ""
            )

        # Limpiar en passant
        self._enPassantSquare = None

        # Actualizar relojes
        self._halfmoveClock += 1

        # Registrar movimiento y cambiar turno
        moveStr = "O-O" if kingSide else "O-O-O"
        self._recordMove(moveStr)
        self._switchTurn()

        # Disparar callbacks
        self._triggerCallbacks()

        self._log(f"Castling executed: {moveStr}")
        return True

    def _executeMove(self, fromIndex, toIndex, promotion, moveStr):
        """Ejecuta un movimiento normal en el tablero."""
        piece = self._board[fromIndex]
        targetPiece = self._board[toIndex]
        pieceType = piece.upper()
        isWhite = piece.isupper()

        # Manejar captura en passant
        isEnPassant = False
        if pieceType == "P" and self._indexToSquare(toIndex) == self._enPassantSquare:
            isEnPassant = True
            capturedPawnRank = 4 if isWhite else 3
            capturedPawnIndex = capturedPawnRank * 8 + self._getFile(toIndex)
            self._board[capturedPawnIndex] = " "

        # Registrar pieza capturada
        captureColor = "w" if isWhite else "b"
        if targetPiece != " ":
            self._capturedPieces[captureColor].append(targetPiece)
        elif isEnPassant:
            capturedPawn = "p" if isWhite else "P"
            self._capturedPieces[captureColor].append(capturedPawn)

        # Mover la pieza
        self._board[toIndex] = piece
        self._board[fromIndex] = " "

        # Manejar promocion
        if pieceType == "P" and self._getRank(toIndex) == (7 if isWhite else 0):
            if promotion:
                self._board[toIndex] = (
                    promotion.upper() if isWhite else promotion.lower()
                )
            else:
                # Por defecto reina si no se especifica promocion (no deberia pasar)
                self._board[toIndex] = "Q" if isWhite else "q"

        # Actualizar casilla en passant
        self._enPassantSquare = None
        if pieceType == "P":
            fromRank = self._getRank(fromIndex)
            toRank = self._getRank(toIndex)
            if abs(toRank - fromRank) == 2:
                # Peon avanzo dos casillas, fijar en passant
                epRank = (fromRank + toRank) // 2
                epFile = self._getFile(fromIndex)
                self._enPassantSquare = self._indexToSquare(epRank * 8 + epFile)

        # Actualizar derechos de enroque
        self._updateCastlingRights(fromIndex, toIndex, piece)

        # Actualizar contador de medio-movimiento
        if pieceType == "P" or targetPiece != " " or isEnPassant:
            self._halfmoveClock = 0
        else:
            self._halfmoveClock += 1

        # Registrar movimiento y cambiar turno
        self._recordMove(moveStr)
        self._switchTurn()

    def _updateCastlingRights(self, fromIndex, toIndex, piece):
        """Actualiza derechos de enroque segun el movimiento."""
        pieceType = piece.upper()

        # Movimientos del rey
        if pieceType == "K":
            if piece.isupper():
                self._castlingRights = self._castlingRights.replace("K", "").replace(
                    "Q", ""
                )
            else:
                self._castlingRights = self._castlingRights.replace("k", "").replace(
                    "q", ""
                )

        # Movimientos o captura de torre
        rookPositions = {
            0: "Q",  # a1 - torre blanca lado dama
            7: "K",  # h1 - torre blanca lado rey
            56: "q",  # a8 - torre negra lado dama
            63: "k",  # h8 - torre negra lado rey
        }

        for pos, right in rookPositions.items():
            if fromIndex == pos or toIndex == pos:
                self._castlingRights = self._castlingRights.replace(right, "")

    def _recordMove(self, moveStr):
        """Registra el movimiento en el historial."""
        if self._turn == "w":
            self._currentTurnMove = moveStr
        else:
            if self._currentTurnMove is not None:
                self._history.append([self._currentTurnMove, moveStr])
            else:
                self._history.append(["", moveStr])
            self._currentTurnMove = None

    def _switchTurn(self):
        """Cambia al turno del otro jugador."""
        if self._turn == "w":
            self._turn = "b"
        else:
            self._turn = "w"
            self._fullmoveNumber += 1

    def _triggerCallbacks(self):
        """Dispara callbacks segun el estado de la partida."""
        if self.isCheckmate():
            if self._onCheckmate:
                self._onCheckmate()
            if self._onGameOver:
                self._onGameOver()
        elif self.isStalemate():
            if self._onStalemate:
                self._onStalemate()
            if self._onGameOver:
                self._onGameOver()
        elif self.isDraw():
            if self._onDraw:
                self._onDraw()
            if self._onGameOver:
                self._onGameOver()
        elif self.isCheck():
            if self._onCheck:
                self._onCheck()

    def getLegalMoves(self, square):
        """
        Obtiene todos los movimientos legales de la pieza en la casilla indicada.

        Args:
            square: Casilla en notacion algebraica (ej. 'e2')

        Returns:
            list: Lista de movimientos en formato ['e2-e3', 'e2-e4', ...]
        """
        fromIndex = self._squareToIndex(square)
        if fromIndex == -1:
            return []

        piece = self._board[fromIndex]
        if piece == " ":
            return []

        # Solo devolver movimientos del turno actual
        if not self._isPieceOfCurrentTurn(piece):
            return []

        legalMoves = []
        pseudoMoves = self._generatePseudoLegalMoves(fromIndex)
        pieceType = piece.upper()
        isWhite = piece.isupper()

        for toIndex in pseudoMoves:
            toSquare = self._indexToSquare(toIndex)
            toRank = self._getRank(toIndex)

            # Manejar promocion de peon
            if pieceType == "P" and toRank == (7 if isWhite else 0):
                for promotionPiece in ["Q", "R", "B", "N"]:
                    if self._isMoveLegal(fromIndex, toIndex, promotionPiece):
                        legalMoves.append(f"{square}-{toSquare}={promotionPiece}")
            else:
                if self._isMoveLegal(fromIndex, toIndex, None):
                    legalMoves.append(f"{square}-{toSquare}")

        # Agregar enroques si aplica
        if pieceType == "K":
            color = "w" if isWhite else "b"
            if self._canCastle(True, color):
                legalMoves.append("O-O")
            if self._canCastle(False, color):
                legalMoves.append("O-O-O")

        return legalMoves

    def getPiece(self, square):
        """
        Obtiene la pieza en la casilla indicada.

        Args:
            square: Casilla en notacion algebraica (ej. 'e4')

        Returns:
            str: Caracter de la pieza o espacio si esta vacia
        """
        index = self._squareToIndex(square)
        if index == -1:
            return " "
        return self._board[index]

    def undo(self):
        """
        Deshace el ultimo movimiento.

        Returns:
            bool: True si se deshizo, False si no hay movimientos
        """
        if not self._moveStack:
            self._log("No moves to undo")
            return False

        state = self._moveStack.pop()
        self._restoreState(state)
        self._log("Move undone")
        return True

    def getCapturedPieces(self):
        """
        Obtiene las piezas capturadas durante la partida.

        Returns:
            dict: {"w": str, "b": str} donde "w" contiene piezas capturadas
                por blancas (piezas negras, minusculas) y "b" piezas capturadas
                por negras (piezas blancas, mayusculas).
                Ordenadas por valor descendente (dama, torre, alfil, caballo, peon).
        """
        order = "qrbnp"

        def sortKey(c):
            cl = c.lower()
            return order.index(cl) if cl in order else 5

        w = "".join(sorted(self._capturedPieces["w"], key=sortKey))
        b = "".join(sorted(self._capturedPieces["b"], key=sortKey))
        return {"w": w, "b": b}

    def getTurn(self):
        """
        Devuelve el turno actual.

        Returns:
            str: 'w' para blancas, 'b' para negras
        """
        return self._turn

    def isCheck(self):
        """
        Verifica si el jugador del turno actual esta en jaque.

        Returns:
            bool: True si esta en jaque
        """
        return self._isInCheck(self._turn)

    def isCheckmate(self):
        """
        Verifica si el jugador actual esta en jaque mate.

        Returns:
            bool: True si es jaque mate
        """
        if not self.isCheck():
            return False
        return not self._hasLegalMoves()

    def isStalemate(self):
        """
        Verifica si la partida esta en tablas por ahogado.

        Returns:
            bool: True si es ahogado
        """
        if self.isCheck():
            return False
        return not self._hasLegalMoves()

    def _hasLegalMoves(self):
        """Verifica si el jugador actual tiene movimientos legales."""
        for i in range(64):
            piece = self._board[i]
            if piece == " ":
                continue
            if not self._isPieceOfCurrentTurn(piece):
                continue

            square = self._indexToSquare(i)
            if self.getLegalMoves(square):
                return True
        return False

    def isDraw(self):
        """
        Verifica si la partida es tablas (regla de 50 o material insuficiente).

        Returns:
            bool: True si es tablas
        """
        # Regla de 50 movimientos
        if self._halfmoveClock >= 100:  # 100 medios = 50 movimientos completos
            return True

        # Material insuficiente
        return self._isInsufficientMaterial()

    def _isInsufficientMaterial(self):
        """Verifica material insuficiente para dar mate."""
        whitePieces = []
        blackPieces = []

        for i in range(64):
            piece = self._board[i]
            if piece == " ":
                continue
            if piece.isupper():
                whitePieces.append((piece, i))
            else:
                blackPieces.append((piece.upper(), i))

        # Quitar reyes
        whitePieces = [(p, i) for p, i in whitePieces if p != "K"]
        blackPieces = [(p, i) for p, i in blackPieces if p != "K"]

        whiteCount = len(whitePieces)
        blackCount = len(blackPieces)

        # K vs K
        if whiteCount == 0 and blackCount == 0:
            return True

        # K vs K+B o K vs K+N
        if whiteCount == 0 and blackCount == 1:
            if blackPieces[0][0] in "BN":
                return True
        if blackCount == 0 and whiteCount == 1:
            if whitePieces[0][0] in "BN":
                return True

        # K+B vs K+B (alfiles del mismo color)
        if whiteCount == 1 and blackCount == 1:
            if whitePieces[0][0] == "B" and blackPieces[0][0] == "B":
                # Verificar si los alfiles estan en el mismo color
                whiteIdx = whitePieces[0][1]
                blackIdx = blackPieces[0][1]
                whiteColor = (self._getFile(whiteIdx) + self._getRank(whiteIdx)) % 2
                blackColor = (self._getFile(blackIdx) + self._getRank(blackIdx)) % 2
                if whiteColor == blackColor:
                    return True

        return False

    def isGameOver(self):
        """
        Verifica si la partida termino.

        Returns:
            bool: True si la partida termino
        """
        return self.isCheckmate() or self.isStalemate() or self.isDraw()

    # ==================== Metodos FEN/PGN ====================

    def setFen(self, fen):
        """
        Carga una posicion desde notacion FEN.

        Args:
            fen: string FEN
        """
        parts = fen.split()
        if len(parts) < 4:
            raise ValueError("FEN invalido: faltan partes")

        # Parsear posicion del tablero
        self._board = [" "] * 64
        ranks = parts[0].split("/")
        if len(ranks) != 8:
            raise ValueError("FEN invalido: numero de filas incorrecto")

        for rankIdx, rankStr in enumerate(ranks):
            boardRank = 7 - rankIdx  # FEN empieza en la fila 8
            file = 0
            for char in rankStr:
                if char.isdigit():
                    file += int(char)
                else:
                    if file > 7:
                        raise ValueError("FEN invalido: overflow de fila")
                    index = boardRank * 8 + file
                    self._board[index] = char
                    file += 1

        # Parsear color activo
        self._turn = parts[1]
        if self._turn not in "wb":
            raise ValueError("FEN invalido: color activo invalido")

        # Parsear derechos de enroque
        self._castlingRights = parts[2] if parts[2] != "-" else ""

        # Parsear casilla en passant
        self._enPassantSquare = parts[3] if parts[3] != "-" else None

        # Parsear contador de medio-movimiento
        self._halfmoveClock = int(parts[4]) if len(parts) > 4 else 0

        # Parsear numero de movimiento completo
        self._fullmoveNumber = int(parts[5]) if len(parts) > 5 else 1

        # Reiniciar historial y pila de movimientos
        self._history = []
        self._moveStack = []
        self._currentTurnMove = None
        self._capturedPieces = {"w": [], "b": []}

        self._log(f"Position loaded from FEN: {fen}")

    def getFen(self):
        """
        Exporta la posicion actual a notacion FEN.

        Returns:
            str: string FEN
        """
        fenParts = []

        # Posicion del tablero
        ranks = []
        for rank in range(7, -1, -1):  # Empezar en la fila 8
            rankStr = ""
            emptyCount = 0
            for file in range(8):
                index = rank * 8 + file
                piece = self._board[index]
                if piece == " ":
                    emptyCount += 1
                else:
                    if emptyCount > 0:
                        rankStr += str(emptyCount)
                        emptyCount = 0
                    rankStr += piece
            if emptyCount > 0:
                rankStr += str(emptyCount)
            ranks.append(rankStr)
        fenParts.append("/".join(ranks))

        # Color activo
        fenParts.append(self._turn)

        # Derechos de enroque
        fenParts.append(self._castlingRights if self._castlingRights else "-")

        # Casilla en passant
        fenParts.append(self._enPassantSquare if self._enPassantSquare else "-")

        # Contador de medio-movimiento
        fenParts.append(str(self._halfmoveClock))

        # Numero de movimiento completo
        fenParts.append(str(self._fullmoveNumber))

        return " ".join(fenParts)

    def getPgn(self, headers=None):
        """
        Exporta la partida a formato PGN.

        Args:
            headers: dict opcional con cabeceras PGN

        Returns:
            str: string PGN
        """
        pgn = ""

        # Cabeceras por defecto
        defaultHeaders = {
            "Event": "?",
            "Site": "?",
            "Date": "????.??.??",
            "Round": "?",
            "White": "?",
            "Black": "?",
            "Result": "*",
        }

        if headers:
            defaultHeaders.update(headers)

        # Determinar resultado
        if self.isCheckmate():
            defaultHeaders["Result"] = "0-1" if self._turn == "w" else "1-0"
        elif self.isStalemate() or self.isDraw():
            defaultHeaders["Result"] = "1/2-1/2"

        # Escribir cabeceras
        for key, value in defaultHeaders.items():
            pgn += f'[{key} "{value}"]\n'
        pgn += "\n"

        # Escribir movimientos
        moveText = ""
        for i, (whiteMove, blackMove) in enumerate(self._history):
            moveNum = i + 1
            if whiteMove:
                moveText += f"{moveNum}. {whiteMove} "
            if blackMove:
                moveText += f"{blackMove} "

        # Agregar turno incompleto si existe
        if self._currentTurnMove:
            moveNum = len(self._history) + 1
            moveText += f"{moveNum}. {self._currentTurnMove} "

        pgn += moveText.strip()
        pgn += " " + defaultHeaders["Result"]

        return pgn

    def getHistory(self):
        """
        Devuelve el historial de movimientos.

        Returns:
            list: Lista de tuplas [(mov_blancas, mov_negras), ...]
        """
        result = [tuple(moves) for moves in self._history]

        # Agregar turno incompleto si existe
        if self._currentTurnMove:
            result.append((self._currentTurnMove, ""))

        return result

    # ==================== Representacion en texto ====================

    def __str__(self):
        """Representacion ASCII del tablero."""
        lines = []
        lines.append("  +---+---+---+---+---+---+---+---+")

        for rank in range(7, -1, -1):
            line = f"{rank + 1} |"
            for file in range(8):
                index = rank * 8 + file
                piece = self._board[index]
                line += f" {piece} |"
            lines.append(line)
            lines.append("  +---+---+---+---+---+---+---+---+")

        lines.append("    a   b   c   d   e   f   g   h")
        lines.append(f"\nTurn: {'White' if self._turn == 'w' else 'Black'}")
        lines.append(f"FEN: {self.getFen()}")

        return "\n".join(lines)
