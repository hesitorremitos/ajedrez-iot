"""
Modulo de visualizacion de ajedrez para pantalla OLED SSD1306 128x64.
Renderiza el estado de una partida de ajedrez usando pixel art 8x8.
Exclusivamente de renderizado, no maneja entrada de usuario.
Optimizado para ESP32 con MicroPython.
"""

try:
    from machine import Pin, I2C
    from ssd1306 import SSD1306_I2C
except ImportError:
    Pin = None
    I2C = None
    SSD1306_I2C = None


# Bitmaps de piezas rellenas: 8 bytes por pieza, MSB = pixel izquierdo
# Total: 6 piezas x 8 bytes = 48 bytes
_PIECE_BITMAPS = {
    "K": bytes([0x10, 0x38, 0x10, 0x7C, 0x38, 0x38, 0x7C, 0x7C]),
    "Q": bytes([0x54, 0x54, 0x7C, 0x38, 0x38, 0x38, 0x7C, 0x7C]),
    "R": bytes([0x5A, 0x7E, 0x3C, 0x3C, 0x3C, 0x3C, 0x7E, 0x7E]),
    "B": bytes([0x10, 0x38, 0x28, 0x38, 0x10, 0x38, 0x7C, 0x7C]),
    "N": bytes([0x30, 0x78, 0xF8, 0x3C, 0x18, 0x38, 0x7C, 0x7C]),
    "P": bytes([0x00, 0x18, 0x3C, 0x3C, 0x18, 0x3C, 0x7E, 0x7E]),
}


def _makeExpanded(bmp):
    """
    Expande un bitmap 1 pixel en todas direcciones (4-conectado).
    El resultado es el bitmap original + sus vecinos inmediatos.
    """
    out = []
    for r in range(8):
        above = bmp[r - 1] if r > 0 else 0
        current = bmp[r]
        below = bmp[r + 1] if r < 7 else 0
        # Expandir: arriba, abajo, izquierda, derecha
        expanded = above | current | below | (current << 1) | (current >> 1)
        out.append(expanded & 0xFF)
    return bytes(out)


# Bitmaps expandidos para piezas negras (borde blanco + relleno negro)
_PIECE_EXPANDED = {k: _makeExpanded(v) for k, v in _PIECE_BITMAPS.items()}

# Patron dithering checkerboard para casillas oscuras (8 bytes)
# Simula "gris" en pantalla monocromatica, mejora contraste con piezas
_DARK_SQUARE_PATTERN = bytes([0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55])


class ChessDisplay:
    """
    Visualizador de partida de ajedrez en pantalla OLED SSD1306 128x64.

    Renderiza un tablero 64x64 con piezas en pixel art 8x8 y un panel
    informativo 64x64 con turno, movimiento, estado y piezas capturadas.

    Diferenciacion visual de piezas:
    - Piezas blancas: silueta rellena (bitmap completo)
    - Piezas negras: silueta de contorno (solo borde del bitmap)
    - En casillas oscuras: se invierte el color (pieza clara sobre fondo oscuro)
    - En casillas claras: pieza oscura sobre fondo claro
    """

    def __init__(self, chess, sda, scl, flipped=False, address=0x3C, i2cId=0):
        """
        Inicializa el display de ajedrez.

        Args:
            chess: Instancia del modulo Chess para leer estado
            sda: Numero de pin GPIO para SDA
            scl: Numero de pin GPIO para SCL
            flipped: Orientacion inicial. False = blancas abajo, True = negras abajo
            address: Direccion I2C del SSD1306
            i2cId: Numero de bus I2C a usar
        """
        self._chess = chess
        self._flipped = flipped
        i2c = I2C(i2cId, sda=Pin(sda), scl=Pin(scl))
        self._display = SSD1306_I2C(128, 64, i2c, addr=address)

    @property
    def flipped(self):
        """Orientacion actual del tablero."""
        return self._flipped

    @flipped.setter
    def flipped(self, value):
        self._flipped = value

    def flip(self):
        """
        Invierte la orientacion del tablero (toggle).
        No llama a render() automaticamente.
        """
        self._flipped = not self._flipped

    def render(self):
        """Dibuja el estado actual completo (tablero + panel info) en la pantalla."""
        self._display.fill(0)
        self._renderBoard()
        self._renderPanel()
        self._display.show()

    def _renderBoard(self):
        """Dibuja el tablero de ajedrez en la zona izquierda (64x64 pixels)."""
        board = self._chess._board
        display = self._display

        for rank in range(8):
            for file in range(8):
                # Coordenadas de pantalla segun orientacion
                if self._flipped:
                    sx = (7 - file) * 8
                    sy = rank * 8
                else:
                    sx = file * 8
                    sy = (7 - rank) * 8

                # Patron ajedrezado: a1 (file=0, rank=0) es casilla oscura
                isDark = (file + rank) % 2 == 0

                # Dibujar casilla oscura con patron dithering (simula gris)
                if isDark:
                    for row in range(8):
                        rowByte = _DARK_SQUARE_PATTERN[row]
                        for col in range(8):
                            if rowByte & (0x80 >> col):
                                display.pixel(sx + col, sy + row, 1)

                # Pieza en esta casilla
                piece = board[rank * 8 + file]
                if piece == " ":
                    continue

                isWhite = piece.isupper()
                pieceKey = piece.upper()
                bmp = _PIECE_BITMAPS[pieceKey]

                # Limpiar area de la pieza (quita dithering debajo)
                if isDark:
                    display.fill_rect(sx, sy, 8, 8, 0)

                if isWhite:
                    # Pieza blanca: bitmap solido blanco
                    self._drawBitmap(display, sx, sy, bmp, 1)
                else:
                    # Pieza negra: borde blanco expandido + relleno negro (solida con borde)
                    self._drawBitmap(display, sx, sy, _PIECE_EXPANDED[pieceKey], 1)
                    self._drawBitmap(display, sx, sy, bmp, 0)

    def _drawBitmap(self, display, sx, sy, bitmap, color):
        """Dibuja un bitmap 8x8 en la posicion indicada."""
        for row in range(8):
            rowByte = bitmap[row]
            if rowByte == 0:
                continue
            for col in range(8):
                if rowByte & (0x80 >> col):
                    display.pixel(sx + col, sy + row, color)

    def _renderPanel(self):
        """Dibuja el panel informativo en la zona derecha (64x64 pixels)."""
        display = self._display
        chess = self._chess
        px = 64  # X offset del panel

        # Linea 0: Turno actual
        turn = chess.getTurn()
        display.text("Turn: " + ("W" if turn == "w" else "B"), px, 0, 1)

        # Linea 1: Numero de movimiento
        display.text("Mov:%4d" % chess._fullmoveNumber, px, 8, 1)

        # Linea 2: Ultimo movimiento jugado
        lastMove = self._getLastMove()
        if lastMove:
            display.text(lastMove[:8], px, 16, 1)

        # Linea 3: vacia (separador)

        # Linea 4: Estado de la partida
        status = self._getStatus()
        if status:
            display.text(status, px, 32, 1)

        # Linea 5: Etiqueta capturadas
        display.text("Capt:", px, 40, 1)

        # Linea 6: Piezas capturadas por blancas (piezas negras)
        captured = chess.getCapturedPieces()
        if captured["w"]:
            display.text(captured["w"][:8], px, 48, 1)

        # Linea 7: Piezas capturadas por negras (piezas blancas)
        if captured["b"]:
            display.text(captured["b"][:8], px, 56, 1)

    def _getLastMove(self):
        """Obtiene el ultimo movimiento jugado desde el historial."""
        history = self._chess.getHistory()
        if not history:
            return ""
        lastTurn = history[-1]
        if lastTurn[1]:
            return lastTurn[1]
        return lastTurn[0]

    def _getStatus(self):
        """Obtiene el texto de estado de la partida."""
        chess = self._chess
        if chess.isCheckmate():
            return "MATE!"
        if chess.isStalemate():
            return "STALE"
        if chess.isDraw():
            return "DRAW"
        if chess.isCheck():
            return "CHECK!"
        return ""
