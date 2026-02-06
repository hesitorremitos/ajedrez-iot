"""
Modulo de visualizacion de ajedrez para pantalla OLED SSD1306 128x64.
Renderiza un tablero de ajedrez usando pixel art 8x8 a partir de datos
recibidos via renderBoard(). Exclusivamente de renderizado, no maneja
entrada de usuario ni depende de otros modulos del proyecto.
Optimizado para ESP32 con MicroPython.
"""

try:
    from machine import Pin, I2C
    from ssd1306 import SSD1306_I2C
except ImportError:
    Pin = None
    I2C = None
    SSD1306_I2C = None


# Columnas (MONO_VLSB) precalculadas para dibujar por buffer.
# Mayusculas = piezas blancas (silueta rellena)
# Minusculas = piezas negras en contorno (interior hueco),
# ajustadas para mejorar contraste sobre casillas oscuras sin saturar pixeles.
_PIECE_COLS = {
    # Piezas blancas (silueta rellena)
    "K": bytes([0x00, 0xC8, 0xFA, 0xFF, 0xFA, 0xC8, 0x00, 0x00]),
    "Q": bytes([0x00, 0xC7, 0xFC, 0xFF, 0xFC, 0xC7, 0x00, 0x00]),
    "R": bytes([0x00, 0xC3, 0xFE, 0xFF, 0xFF, 0xFE, 0xC3, 0x00]),
    "B": bytes([0x00, 0xC0, 0xEE, 0xFB, 0xEE, 0xC0, 0x00, 0x00]),
    "N": bytes([0x04, 0xC6, 0xEF, 0xFF, 0xFE, 0xC8, 0x00, 0x00]),
    "P": bytes([0x00, 0xC0, 0xEC, 0xFE, 0xFE, 0xEC, 0xC0, 0x00]),
    # Piezas negras (contorno grueso)
    "k": bytes([0x00, 0xC8, 0xFA, 0x8F, 0xFA, 0xC8, 0x00, 0x00]),
    "q": bytes([0x00, 0xC7, 0xFC, 0x87, 0xFC, 0xC7, 0x00, 0x00]),
    "r": bytes([0x00, 0xC3, 0xFE, 0x83, 0x83, 0xFE, 0xC3, 0x00]),
    "b": bytes([0x00, 0xC0, 0xEE, 0x93, 0xEE, 0xC0, 0x00, 0x00]),
    "n": bytes([0x04, 0xC6, 0xEB, 0xBB, 0xFC, 0xC0, 0x00, 0x00]),
    "p": bytes([0x00, 0x40, 0xAC, 0xB6, 0xB6, 0xAC, 0x40, 0x00]),
}

# Patron casilla oscura estilo *-*-* (punto cada 2 espacios).
# Alterna columnas para mantener contraste con piezas negras invertidas.
_DARK_SQUARE_COLS = bytes([0x55, 0x00, 0x55, 0x00, 0x55, 0x00, 0x55, 0x00])
_LIGHT_SQUARE_COLS = bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
_CLEAR_64 = bytes(64)

# Fuente de reloj 8x16 en formato MONO_VLSB (dos paginas de 8 px).
# Cada glifo es (page0_cols, page1_cols), 8 columnas por glifo.
# Indices guia:
# 0='0', 1='1', 2='2', 3='3', 4='4', 5='5', 6='6', 7='7', 8='8', 9='9', 10=':'
_CLOCK_GLYPH_8X16 = (
    (
        bytes([0x00, 0xF8, 0xF8, 0x18, 0x18, 0xF8, 0xF8, 0x00]),
        bytes([0x00, 0x1F, 0x1F, 0x18, 0x18, 0x1F, 0x1F, 0x00]),
    ),  # 0 -> '0'
    (
        bytes([0x00, 0x60, 0x60, 0xF8, 0xF8, 0x00, 0x00, 0x00]),
        bytes([0x00, 0x18, 0x18, 0x1F, 0x1F, 0x18, 0x18, 0x00]),
    ),  # 1 -> '1'
    (
        bytes([0x00, 0x98, 0x98, 0x98, 0x98, 0xF8, 0xF8, 0x00]),
        bytes([0x00, 0x1F, 0x1F, 0x19, 0x19, 0x19, 0x19, 0x00]),
    ),  # 2 -> '2'
    (
        bytes([0x00, 0x98, 0x98, 0x98, 0x98, 0xF8, 0xF8, 0x00]),
        bytes([0x00, 0x19, 0x19, 0x19, 0x19, 0x1F, 0x1F, 0x00]),
    ),  # 3 -> '3'
    (
        bytes([0x00, 0xF8, 0xF8, 0x80, 0x80, 0xF8, 0xF8, 0x00]),
        bytes([0x00, 0x01, 0x01, 0x01, 0x01, 0x1F, 0x1F, 0x00]),
    ),  # 4 -> '4'
    (
        bytes([0x00, 0xF8, 0xF8, 0x98, 0x98, 0x98, 0x98, 0x00]),
        bytes([0x00, 0x19, 0x19, 0x19, 0x19, 0x1F, 0x1F, 0x00]),
    ),  # 5 -> '5'
    (
        bytes([0x00, 0xF8, 0xF8, 0x98, 0x98, 0x98, 0x98, 0x00]),
        bytes([0x00, 0x1F, 0x1F, 0x19, 0x19, 0x1F, 0x1F, 0x00]),
    ),  # 6 -> '6'
    (
        bytes([0x00, 0x18, 0x18, 0x18, 0x18, 0xF8, 0xF8, 0x00]),
        bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x1F, 0x1F, 0x00]),
    ),  # 7 -> '7'
    (
        bytes([0x00, 0xF8, 0xF8, 0x98, 0x98, 0xF8, 0xF8, 0x00]),
        bytes([0x00, 0x1F, 0x1F, 0x19, 0x19, 0x1F, 0x1F, 0x00]),
    ),  # 8 -> '8'
    (
        bytes([0x00, 0xF8, 0xF8, 0x98, 0x98, 0xF8, 0xF8, 0x00]),
        bytes([0x00, 0x19, 0x19, 0x19, 0x19, 0x1F, 0x1F, 0x00]),
    ),  # 9 -> '9'
    (
        bytes([0x00, 0x00, 0x00, 0x60, 0x60, 0x00, 0x00, 0x00]),
        bytes([0x00, 0x00, 0x00, 0x06, 0x06, 0x00, 0x00, 0x00]),
    ),  # 10 -> ':'
)


def _clockGlyphIndex(ch):
    """
    Mapea un caracter de reloj a indice de _CLOCK_GLYPH_8X16.

    Args:
        ch: Caracter a mapear ('0'-'9' o ':')

    Returns:
        Indice en _CLOCK_GLYPH_8X16 (0-10) o -1 si no reconocido
    """
    asciiCode = ord(ch)

    # Digitos '0'..'9' mapean a indices 0..9
    if 48 <= asciiCode <= 57:
        return asciiCode - 48

    # Dos puntos ':' mapea a indice 10
    if asciiCode == 58:
        return 10

    # Caracter no reconocido
    return -1


class ChessDisplay:
    """
    Visualizador de tablero de ajedrez en pantalla OLED SSD1306 128x64.

    Renderiza un tablero 64x64 con piezas en pixel art 8x8.
    Recibe datos del tablero via renderBoard() como cadena de 64 caracteres.
    No depende de ningun otro modulo del proyecto.

    Diferenciacion visual de piezas:
    - Piezas blancas (mayusculas K,Q,R,B,N,P): silueta rellena
    - Piezas negras (minusculas k,q,r,b,n,p): contorno con interior hueco
    - Casillas oscuras: patron *-*-* de baja densidad
    - Dibujo optimizado por buffer para reducir llamadas a pixel()

    Caracteres validos en board:
    - ' ' (espacio): casilla vacia
    - K,Q,R,B,N,P: piezas blancas (Rey, Reina, Torre, Alfil, Caballo, Peon)
    - k,q,r,b,n,p: piezas negras
    - Cualquier otro caracter lanza ValueError
    """

    def __init__(self, sda, scl, address=0x3C, i2cId=0):
        """
        Inicializa el display de ajedrez.

        Args:
            sda: Numero de pin GPIO para SDA
            scl: Numero de pin GPIO para SCL
            address: Direccion I2C del SSD1306
            i2cId: Numero de bus I2C a usar
        """
        self._board = " " * 64
        self._clockWhite = ""
        self._clockBlack = ""
        self._activeColor = "w"
        self._turnCount = 1
        i2c = I2C(i2cId, sda=Pin(sda), scl=Pin(scl))
        self._display = SSD1306_I2C(128, 64, i2c, addr=address)

    def renderBoard(self, board):
        """
        Dibuja el tablero 8x8 en la mitad izquierda y hace show().

        Args:
            board: Cadena de 64 caracteres representando el tablero.
                   Caracteres validos: ' ' (vacio), K/Q/R/B/N/P (blancas), k/q/r/b/n/p (negras)

        Raises:
            TypeError: Si board no es cadena
            ValueError: Si board no tiene 64 caracteres
            ValueError: Si encuentra un caracter no reconocido en board
        """
        if not isinstance(board, str):
            raise TypeError("board debe ser str de 64 caracteres")
        if len(board) != 64:
            raise ValueError("board debe tener exactamente 64 caracteres")

        self._board = board
        self._renderBoard()
        self._display.show()

    def renderClock(self, clockText, color):
        """Actualiza reloj de un color y repinta el panel lateral."""
        if color not in ("w", "b"):
            raise ValueError("color debe ser 'w' o 'b'")

        text = clockText if clockText else ""
        if color == "w":
            self._clockWhite = text
        else:
            self._clockBlack = text

        self._renderSidePanel()
        self._display.show()

    def renderTurn(self, color):
        """Actualiza jugador en turno ('w' o 'b') y repinta panel lateral."""
        if color not in ("w", "b"):
            raise ValueError("color debe ser 'w' o 'b'")
        self._activeColor = color
        self._renderSidePanel()
        self._display.show()

    def renderTurnCount(self, turnCount):
        """Actualiza contador de turnos y repinta panel lateral."""
        if turnCount < 0:
            raise ValueError("turnCount debe ser >= 0")
        self._turnCount = turnCount
        self._renderSidePanel()
        self._display.show()

    def renderSidePanel(self, whiteClock, blackClock, activeColor, turnCount):
        """Actualiza todo el panel lateral en una sola llamada."""
        if activeColor not in ("w", "b"):
            raise ValueError("activeColor debe ser 'w' o 'b'")
        if turnCount < 0:
            raise ValueError("turnCount debe ser >= 0")

        self._clockWhite = whiteClock if whiteClock else ""
        self._clockBlack = blackClock if blackClock else ""
        self._activeColor = activeColor
        self._turnCount = turnCount

        self._renderSidePanel()
        self._display.show()

    def _renderSidePanel(self):
        """Dibuja panel derecho: reloj superior, estado centro, reloj inferior."""
        display = self._display
        buf = display.buffer
        width = display.width
        flatBuffer = not (isinstance(buf, list) and buf and isinstance(buf[0], list))

        panelX0 = 64
        panelX1 = 128

        topColor = "b"
        bottomColor = "w"

        topClock = self._clockWhite if topColor == "w" else self._clockBlack
        bottomClock = self._clockWhite if bottomColor == "w" else self._clockBlack
        topInvert = self._activeColor == topColor
        bottomInvert = self._activeColor == bottomColor

        if flatBuffer:
            for page in range(8):
                start = page * width + panelX0
                buf[start : start + 64] = _CLEAR_64

            self._drawClockLineFlat(buf, width, 0, topClock, topInvert)
            self._drawClockLineFlat(buf, width, 48, bottomClock, bottomInvert)

            activeLabel = "B" if self._activeColor == "w" else "N"
            display.text(activeLabel, 70, 28, 1)
            display.text(str(self._turnCount), 86, 28, 1)
            return

        # Fallback para mocks con buffer 2D
        display.fill_rect(panelX0, 0, 64, 64, 0)
        self._drawClockLineFallback(display, 0, topClock, topInvert)
        self._drawClockLineFallback(display, 48, bottomClock, bottomInvert)

        activeLabel = "B" if self._activeColor == "w" else "N"
        display.text(activeLabel, 70, 28, 1)
        display.text(str(self._turnCount), 86, 28, 1)

    def _drawClockLineFlat(self, buf, width, y, text, invert):
        """Dibuja un reloj MM:SS en y usando buffer plano MONO_VLSB."""
        page = y >> 3
        pageBase0 = page * width
        pageBase1 = (page + 1) * width
        x0 = 66
        charStep = 9
        clockWidth = 44

        if invert:
            for x in range(x0, x0 + clockWidth):
                buf[pageBase0 + x] = 0xFF
                buf[pageBase1 + x] = 0xFF

        x = x0
        for ch in text[:5]:
            idx = _clockGlyphIndex(ch)
            if idx >= 0:
                lowCols, highCols = _CLOCK_GLYPH_8X16[idx]
                for col in range(8):
                    px = x + col
                    if px >= 128:
                        continue

                    low = lowCols[col]
                    high = highCols[col]

                    if invert:
                        buf[pageBase0 + px] &= (~low) & 0xFF
                        buf[pageBase1 + px] &= (~high) & 0xFF
                    else:
                        buf[pageBase0 + px] |= low
                        buf[pageBase1 + px] |= high
            x += charStep

    def _drawClockLineFallback(self, display, y, text, invert):
        """Fallback de reloj para mocks por pixel."""
        x0 = 66
        charStep = 9
        clockWidth = 44

        if invert:
            display.fill_rect(x0, y, clockWidth, 16, 1)

        x = x0
        for ch in text[:5]:
            idx = _clockGlyphIndex(ch)
            if idx >= 0:
                lowCols, highCols = _CLOCK_GLYPH_8X16[idx]
                for col in range(8):
                    px = x + col
                    if px >= 128:
                        continue
                    low = lowCols[col]
                    high = highCols[col]
                    for row in range(8):
                        bitLow = 1 if (low & (1 << row)) else 0
                        bitHigh = 1 if (high & (1 << row)) else 0
                        if invert:
                            display.pixel(px, y + row, 0 if bitLow else 1)
                            display.pixel(px, y + 8 + row, 0 if bitHigh else 1)
                        else:
                            display.pixel(px, y + row, bitLow)
                            display.pixel(px, y + 8 + row, bitHigh)
            x += charStep

    def _renderBoard(self):
        """
        Dibuja el tablero de ajedrez en la zona izquierda (64x64 pixels).

        Itera sobre cada casilla del tablero, determina el patron de fondo
        (oscuro/claro) segun patron ajedrezado, y dibuja la pieza correspondiente
        si existe.

        Raises:
            ValueError: Si encuentra un caracter de pieza no reconocido
        """
        board = self._board
        display = self._display
        buf = display.buffer
        width = display.width
        flatBuffer = not (isinstance(buf, list) and buf and isinstance(buf[0], list))

        def writeTile(sx, sy, tile):
            """Escribe un tile de 8x8 bytes en la posicion especificada."""
            if flatBuffer:
                # Escritura directa a buffer flat (modo normal ESP32)
                base = sx + ((sy >> 3) * width)
                for col in range(8):
                    buf[base + col] = tile[col]
                return

            # Fallback para mocks de tests que usan buffer 2D por pixel
            for col in range(8):
                colByte = tile[col]
                x = sx + col
                for row in range(8):
                    y = sy + row
                    display.pixel(x, y, 1 if (colByte & (1 << row)) else 0)

        # Iterar sobre cada casilla del tablero 8x8
        for rank in range(8):
            for file in range(8):
                # Orientacion fija: blancas abajo, negras arriba
                sx = file * 8
                sy = (7 - rank) * 8

                # Determinar patron de fondo: a1 (file=0, rank=0) es casilla oscura
                isDarkSquare = (file + rank) % 2 == 0

                # Obtener pieza en esta casilla
                piece = board[rank * 8 + file]

                # Seleccionar tile a dibujar
                if piece == " ":
                    # Casilla vacia: usar patron de fondo
                    tile = _DARK_SQUARE_COLS if isDarkSquare else _LIGHT_SQUARE_COLS

                elif piece in _PIECE_COLS:
                    # Pieza valida: usar su bitmap
                    tile = _PIECE_COLS[piece]

                else:
                    # Pieza desconocida: lanzar error
                    if isinstance(piece, str) and len(piece) == 1:
                        asciiCode = ord(piece)
                    else:
                        asciiCode = -1

                    raise ValueError(
                        "Caracter de pieza no reconocido: '%s' (ASCII %d) en posicion file=%d, rank=%d"
                        % (piece, asciiCode, file, rank)
                    )

                writeTile(sx, sy, tile)
