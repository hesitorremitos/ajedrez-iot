"""Tests para el modulo ChessDisplay v2.0."""

import sys
import pytest
from modules.chessdisplay.ChessDisplay import _PIECE_COLS

# Obtener referencia al modulo (no la clase) para parchear Pin, I2C, SSD1306_I2C
cd_module = sys.modules["modules.chessdisplay.ChessDisplay"]

# Posicion inicial como cadena de 64 caracteres (indice 0 = a1, indice 63 = h8)
INITIAL_BOARD = "RNBQKBNRPPPPPPPP                                pppppppprnbqkbnr"

EMPTY_BOARD = " " * 64


# ==================== Mock classes ====================


class MockPin:
    """Mock para machine.Pin."""

    def __init__(self, num):
        self.num = num


class MockI2C:
    """Mock para machine.I2C."""

    def __init__(self, id, sda=None, scl=None):
        self.id = id
        self.sda = sda
        self.scl = scl


class MockDisplay:
    """Mock para ssd1306.SSD1306_I2C con buffer de pixels."""

    def __init__(self, width, height, i2c, addr=0x3C):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.buffer = [[0] * width for _ in range(height)]
        self.showCount = 0
        self.fillCount = 0
        self.textCalls = []

    def fill(self, color):
        self.fillCount += 1
        for y in range(self.height):
            for x in range(self.width):
                self.buffer[y][x] = color

    def fill_rect(self, x, y, w, h, color):
        for dy in range(h):
            for dx in range(w):
                px = x + dx
                py = y + dy
                if 0 <= px < self.width and 0 <= py < self.height:
                    self.buffer[py][px] = color

    def pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y][x] = color

    def text(self, string, x, y, color):
        self.textCalls.append({"text": string, "x": x, "y": y, "color": color})

    def show(self):
        self.showCount += 1

    def getRegion(self, x, y, w, h):
        """Extrae una region rectangular del buffer como lista de listas."""
        region = []
        for dy in range(h):
            row = []
            for dx in range(w):
                row.append(self.buffer[y + dy][x + dx])
            region.append(row)
        return region


# ==================== Fixtures ====================


@pytest.fixture(autouse=True)
def patch_hardware():
    """Parchea las dependencias de hardware para todos los tests."""
    origPin = cd_module.Pin
    origI2C = cd_module.I2C
    origSSD = cd_module.SSD1306_I2C
    cd_module.Pin = MockPin
    cd_module.I2C = MockI2C
    cd_module.SSD1306_I2C = MockDisplay
    yield
    cd_module.Pin = origPin
    cd_module.I2C = origI2C
    cd_module.SSD1306_I2C = origSSD


@pytest.fixture
def display():
    from modules.chessdisplay import ChessDisplay

    return ChessDisplay(sda=21, scl=22)


# ==================== Helper functions ====================


def get_mock_display(chess_display):
    """Obtiene el MockDisplay interno de un ChessDisplay."""
    return chess_display._display


# ==================== AC-01: Crear instancia con parametros requeridos ====================


def test_create_with_required_params():
    from modules.chessdisplay import ChessDisplay

    d = ChessDisplay(sda=21, scl=22)
    assert d._display.addr == 0x3C
    assert d._display.i2c.id == 0


# ==================== AC-02: Crear instancia con todos los parametros ====================


def test_create_with_all_params():
    from modules.chessdisplay import ChessDisplay

    d = ChessDisplay(sda=21, scl=22, address=0x3D, i2cId=1)
    assert d._display.addr == 0x3D
    assert d._display.i2c.id == 1
    assert d._display.i2c.sda.num == 21
    assert d._display.i2c.scl.num == 22


# ==================== AC-03: render() dibuja tablero en posicion inicial ====================


def test_render_initial_position(display):
    display.renderBoard(INITIAL_BOARD)
    mock = get_mock_display(display)

    # Verifica que show() fue llamado
    assert mock.showCount == 1

    # Verifica que no hay llamadas a text() (panel removido en v2.0)
    assert len(mock.textCalls) == 0


# ==================== AC-04: render() actualiza despues de mover peon ====================


def test_render_after_pawn_move(display):
    # Board con peon blanco en e4 en lugar de e2
    board = list(INITIAL_BOARD)
    # e2 = rank 1, file 4 = index 12
    board[12] = " "
    # e4 = rank 3, file 4 = index 28
    board[28] = "P"
    display.renderBoard("".join(board))
    mock = get_mock_display(display)

    # El peon debe estar en e4 (file=4, rank=3) y no en e2 (file=4, rank=1)
    # Orientacion fija: e4 esta en sx=4*8=32, sy=(7-3)*8=32
    e4_region = mock.getRegion(32, 32, 8, 8)
    # e2 esta en sx=32, sy=(7-1)*8=48
    e2_region = mock.getRegion(32, 48, 8, 8)

    # e4 debe tener pixels de pieza (no todo ceros ni todo unos)
    e4_flat = [p for row in e4_region for p in row]
    assert any(p == 1 for p in e4_flat), "e4 debe tener pixels de pieza"

    # e2 no debe tener pieza (casilla oscura o clara vacia)
    # e2: file=4, rank=1 -> (4+1)%2=1 -> casilla clara -> todo ceros
    e2_flat = [p for row in e2_region for p in row]
    assert all(p == 0 for p in e2_flat), "e2 debe estar vacia (casilla clara)"


# ==================== AC-05: renderBoard() actualiza board ====================


def test_set_table_stores_data(display):
    display.renderBoard(INITIAL_BOARD)
    assert display._board == INITIAL_BOARD


def test_set_table_overwrites_data(display):
    display.renderBoard(INITIAL_BOARD)
    display.renderBoard(EMPTY_BOARD)
    assert display._board == EMPTY_BOARD


# ==================== AC-06: renderBoard() llama a show ====================


def test_set_table_does_not_call_show(display):
    mock = get_mock_display(display)
    display.renderBoard(INITIAL_BOARD)
    assert mock.showCount == 1


# ==================== AC-07: renderBoard() con tablero vacio ====================


def test_render_without_set_table_draws_empty_board(display):
    display.renderBoard(EMPTY_BOARD)
    mock = get_mock_display(display)
    assert mock.showCount == 1

    # Sin piezas, solo dithering en casillas oscuras
    # b1 (file=1, rank=0): casilla clara -> todo ceros (sin piezas)
    b1_region = mock.getRegion(8, 56, 8, 8)
    for row in b1_region:
        assert all(p == 0 for p in row), "b1 sin pieza debe estar vacia"


# ==================== AC-08: Orientacion fija muestra blancas abajo ====================


def test_white_at_bottom(display):
    display.renderBoard(INITIAL_BOARD)
    mock = get_mock_display(display)

    # Orientacion fija: rank 0 (fila 1, blancas) se dibuja en sy=(7-0)*8=56
    # La torre blanca en a1 (file=0, rank=0) esta en sx=0, sy=56
    a1_region = mock.getRegion(0, 56, 8, 8)
    a1_flat = [p for row in a1_region for p in row]
    # a1 es casilla oscura (0+0)%2==0, pieza blanca -> pixels sobre fondo limpio
    assert any(p == 0 for p in a1_flat) and any(p == 1 for p in a1_flat), (
        "a1 debe tener pieza blanca sobre casilla oscura"
    )

    # La torre negra en a8 (file=0, rank=7) esta en sx=0, sy=(7-7)*8=0
    a8_region = mock.getRegion(0, 0, 8, 8)
    a8_flat = [p for row in a8_region for p in row]
    # a8 es casilla clara (0+7)%2==1, pieza negra -> outline pixels ON
    assert any(p == 1 for p in a8_flat), "a8 debe tener pieza negra"


# ==================== AC-09: Piezas blancas y negras son visualmente distinguibles ====================


def test_white_black_pieces_distinguishable(display):
    display.renderBoard(INITIAL_BOARD)

    # Comparar los bitmaps directamente
    rook_white = _PIECE_COLS["R"]
    rook_black = _PIECE_COLS["r"]
    assert rook_white != rook_black, "Bitmap blanca e invertida deben ser diferentes"

    # Verificar para todas las piezas
    for piece_type in "KQRBNP":
        white = _PIECE_COLS[piece_type]
        black = _PIECE_COLS[piece_type.lower()]
        assert white != black, (
            f"Bitmap de {piece_type}: blanca y negra deben ser diferentes"
        )


# ==================== AC-10: Patron ajedrezado correcto ====================


def test_checkered_pattern_correct(display):
    # Usar tablero vacio para verificar solo el patron
    display.renderBoard(EMPTY_BOARD)
    mock = get_mock_display(display)

    # a1 (file=0, rank=0): isDark = (0+0)%2==0 -> oscura (patron dithering)
    # En pantalla (orientacion fija): sx=0, sy=(7-0)*8=56
    a1_region = mock.getRegion(0, 56, 8, 8)
    a1_flat = [p for row in a1_region for p in row]
    count_ones = sum(a1_flat)
    assert count_ones == 16, (
        "Casilla oscura debe tener patron *-*-* (16 pixels encendidos)"
    )

    # b1 (file=1, rank=0): isDark = (1+0)%2==1 -> clara (pixels=0)
    b1_region = mock.getRegion(8, 56, 8, 8)
    for row in b1_region:
        assert all(p == 0 for p in row), "b1 debe ser casilla clara (todo 0s)"

    # a2 (file=0, rank=1): isDark = (0+1)%2==1 -> clara
    a2_region = mock.getRegion(0, 48, 8, 8)
    for row in a2_region:
        assert all(p == 0 for p in row), "a2 debe ser casilla clara (todo 0s)"

    # b2 (file=1, rank=1): isDark = (1+1)%2==0 -> oscura (patron dithering)
    b2_region = mock.getRegion(8, 48, 8, 8)
    b2_flat = [p for row in b2_region for p in row]
    count_ones = sum(b2_flat)
    assert count_ones == 16, (
        "Casilla oscura debe tener patron *-*-* (16 pixels encendidos)"
    )


# ==================== Tests adicionales ====================


def test_render_calls_fill_and_show(display):
    display.renderBoard(EMPTY_BOARD)
    mock = get_mock_display(display)
    assert mock.fillCount == 0
    assert mock.showCount == 1


def test_multiple_renders(display):
    display.renderBoard(INITIAL_BOARD)
    # Simular movimiento actualizando tablero
    board = list(INITIAL_BOARD)
    board[12] = " "  # e2 vacio
    board[28] = "P"  # e4 peon
    display.renderBoard("".join(board))
    mock = get_mock_display(display)
    assert mock.showCount == 2
    assert mock.fillCount == 0


def test_render_clock_calls_show(display):
    mock = get_mock_display(display)
    display.renderClock("05:00", "w")
    assert mock.showCount == 1


def test_render_clock_draws_right_top_region(display):
    mock = get_mock_display(display)
    display.renderClock("12:34", "b")

    # Zona reloj: derecha superior (x=64..127, y=0..15)
    region = mock.getRegion(64, 0, 64, 16)
    flat = [p for row in region for p in row]
    assert any(p == 1 for p in flat), (
        "El reloj debe encender pixeles en la zona superior derecha"
    )


def test_render_clock_draws_bottom_clock_for_white(display):
    mock = get_mock_display(display)
    display.renderClock("09:59", "w")

    # Zona reloj inferior: derecha inferior (x=64..127, y=48..63)
    region = mock.getRegion(64, 48, 64, 16)
    flat = [p for row in region for p in row]
    assert any(p == 1 for p in flat), (
        "El reloj blanco debe encender pixeles en la zona inferior derecha"
    )


def test_render_turn_and_turn_count_draw_center_status(display):
    mock = get_mock_display(display)
    display.renderTurn("b")
    display.renderTurnCount(12)

    texts = [c["text"] for c in mock.textCalls]
    assert "N" in texts, "Debe dibujar estado central N/B"
    assert "12" in texts, "Debe dibujar turnCount junto al estado central"


def test_display_width_height(display):
    mock = get_mock_display(display)
    assert mock.width == 128
    assert mock.height == 64


def test_no_panel_text(display):
    """Verifica que no hay textos renderizados (panel removido en v2.0)."""
    display.renderBoard(INITIAL_BOARD)
    mock = get_mock_display(display)
    assert len(mock.textCalls) == 0


def test_inverted_is_not_identical_to_solid():
    """Verifica que cada glifo invertido difiere del glifo solido."""
    for piece_type in "KQRBNP":
        white = _PIECE_COLS[piece_type]
        black = _PIECE_COLS[piece_type.lower()]
        assert white != black


def test_inverted_has_high_contrast():
    """Verifica que el invertido mantiene alto contraste en cada pieza."""
    for piece_type in "KQRBNP":
        white = _PIECE_COLS[piece_type]
        black = _PIECE_COLS[piece_type.lower()]
        white_count = sum(bin(b).count("1") for b in white)
        black_count = sum(bin(b).count("1") for b in black)
        assert black_count != white_count


def test_default_board_is_empty(display):
    """Verifica que el board interno inicia como espacios vacios."""
    assert display._board == " " * 64


def test_render_board_rejects_list(display):
    """Verifica que renderBoard exige cadena para formato estandar."""
    board = list(INITIAL_BOARD)
    with pytest.raises(TypeError):
        display.renderBoard(board)


def test_render_single_piece():
    """Verifica renderizado con una sola pieza en el tablero."""
    from modules.chessdisplay import ChessDisplay

    d = ChessDisplay(sda=21, scl=22)
    # Rey blanco en e1 (file=4, rank=0, index=4)
    board = list(EMPTY_BOARD)
    board[4] = "K"
    d.renderBoard("".join(board))
    mock = get_mock_display(d)

    # e1 (orientacion fija): sx=4*8=32, sy=(7-0)*8=56
    e1_region = mock.getRegion(32, 56, 8, 8)
    e1_flat = [p for row in e1_region for p in row]
    assert any(p == 1 for p in e1_flat), "e1 debe tener pixels de pieza (rey blanco)"


def test_render_black_piece_on_light_square():
    """Verifica renderizado de pieza negra en casilla clara."""
    from modules.chessdisplay import ChessDisplay

    d = ChessDisplay(sda=21, scl=22)
    # Rey negro en e8 (file=4, rank=7, index=60)
    # e8: (4+7)%2 == 1 -> casilla clara
    board = list(EMPTY_BOARD)
    board[60] = "k"
    d.renderBoard("".join(board))
    mock = get_mock_display(d)

    # e8 (orientacion fija): sx=4*8=32, sy=(7-7)*8=0
    e8_region = mock.getRegion(32, 0, 8, 8)
    e8_flat = [p for row in e8_region for p in row]
    # Pieza negra en casilla clara: expanded=1, filled=0
    assert any(p == 1 for p in e8_flat), "e8 debe tener pixels de pieza negra"
    assert any(p == 0 for p in e8_flat), (
        "e8 debe tener pixels vacios (relleno de pieza negra)"
    )


# ==================== Tests de validacion ====================


def test_render_invalid_piece_raises_error(display):
    """Verifica que renderizar una pieza invalida lanza ValueError."""
    board = list(EMPTY_BOARD)
    board[0] = "X"  # Caracter invalido

    with pytest.raises(ValueError) as excinfo:
        display.renderBoard("".join(board))

    assert "no reconocido" in str(excinfo.value)
    assert "X" in str(excinfo.value)


def test_render_number_raises_error(display):
    """Verifica que renderizar un numero lanza ValueError."""
    board = list(EMPTY_BOARD)
    board[10] = "5"  # Numero invalido

    with pytest.raises(ValueError) as excinfo:
        display.renderBoard("".join(board))

    assert "no reconocido" in str(excinfo.value)


def test_render_special_char_raises_error(display):
    """Verifica que renderizar un caracter especial lanza ValueError."""
    board = list(EMPTY_BOARD)
    board[20] = "@"  # Caracter especial invalido

    with pytest.raises(ValueError) as excinfo:
        display.renderBoard("".join(board))

    assert "no reconocido" in str(excinfo.value)


def test_valid_pieces_do_not_raise_error(display):
    """Verifica que todas las piezas validas NO lanzan error."""
    validPieces = "KQRBNPkqrbnp "

    for i, piece in enumerate(validPieces):
        board = list(EMPTY_BOARD)
        board[i] = piece
        # No debe lanzar excepcion
        display.renderBoard("".join(board))
