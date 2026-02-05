"""Tests para el modulo ChessDisplay."""

import sys
import pytest
from modules.chess import Chess
from modules.chessdisplay.ChessDisplay import _PIECE_BITMAPS, _PIECE_OUTLINES

# Obtener referencia al modulo (no la clase) para parchear Pin, I2C, SSD1306_I2C
cd_module = sys.modules["modules.chessdisplay.ChessDisplay"]


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
def chess():
    return Chess()


@pytest.fixture
def display(chess):
    from modules.chessdisplay import ChessDisplay

    return ChessDisplay(chess, sda=21, scl=22)


# ==================== Helper functions ====================


def get_mock_display(chess_display):
    """Obtiene el MockDisplay interno de un ChessDisplay."""
    return chess_display._display


def find_text_call(mock_display, y):
    """Busca una llamada a text() por posicion Y."""
    for call in mock_display.textCalls:
        if call["y"] == y:
            return call
    return None


def find_text_containing(mock_display, substring):
    """Busca una llamada a text() que contenga el substring."""
    for call in mock_display.textCalls:
        if substring in call["text"]:
            return call
    return None


# ==================== AC-01: Crear instancia con parametros requeridos ====================


def test_create_with_required_params(chess):
    from modules.chessdisplay import ChessDisplay

    d = ChessDisplay(chess, sda=21, scl=22)
    assert d.flipped is False
    assert d._display.addr == 0x3C
    assert d._display.i2c.id == 0


# ==================== AC-02: Crear instancia con todos los parametros ====================


def test_create_with_all_params(chess):
    from modules.chessdisplay import ChessDisplay

    d = ChessDisplay(chess, sda=21, scl=22, flipped=True, address=0x3D, i2cId=1)
    assert d.flipped is True
    assert d._display.addr == 0x3D
    assert d._display.i2c.id == 1
    assert d._display.i2c.sda.num == 21
    assert d._display.i2c.scl.num == 22


# ==================== AC-03: render() dibuja tablero en posicion inicial ====================


def test_render_initial_position(display, chess):
    display.render()
    mock = get_mock_display(display)

    # Verifica que show() fue llamado
    assert mock.showCount == 1

    # Verifica panel: Turn W, Mov 1
    turnCall = find_text_call(mock, 0)
    assert turnCall is not None
    assert "W" in turnCall["text"]

    movCall = find_text_call(mock, 8)
    assert movCall is not None
    assert "1" in movCall["text"]

    # No debe haber ultimo movimiento (linea y=16 no deberia existir o estar vacia)
    lastMoveCall = find_text_call(mock, 16)
    assert lastMoveCall is None


# ==================== AC-04: render() actualiza despues de movimiento ====================


def test_render_after_move(display, chess):
    chess.play("e2-e4")
    display.render()
    mock = get_mock_display(display)

    # Turn B
    turnCall = find_text_call(mock, 0)
    assert "B" in turnCall["text"]

    # Ultimo movimiento e2-e4
    lastMoveCall = find_text_call(mock, 16)
    assert lastMoveCall is not None
    assert "e2-e4" in lastMoveCall["text"]

    # El peon debe estar en e4 (file=4, rank=3) y no en e2 (file=4, rank=1)
    # En posicion normal (flipped=False), e4 esta en sx=4*8=32, sy=(7-3)*8=32
    e4_region = mock.getRegion(32, 32, 8, 8)
    # e2 esta en sx=32, sy=(7-1)*8=48
    e2_region = mock.getRegion(32, 48, 8, 8)

    # e4 debe tener pixels de pieza (no todo ceros ni todo unos)
    e4_flat = [p for row in e4_region for p in row]
    assert any(p == 1 for p in e4_flat), "e4 debe tener pixels de pieza"

    # e2 no debe tener pieza (casilla oscura o clara vacia)
    # e2: file=4, rank=1 → (4+1)%2=1 → casilla clara → todo ceros
    e2_flat = [p for row in e2_region for p in row]
    assert all(p == 0 for p in e2_flat), "e2 debe estar vacia (casilla clara)"


# ==================== AC-05: render() muestra estado de jaque ====================


def test_render_shows_check(display, chess):
    # Posicion de jaque directo: dama negra en h4 da jaque al rey blanco en e1
    chess.setFen("4k3/8/8/8/7q/8/8/4K3 w - - 0 1")
    assert chess.isCheck() is True, "La posicion debe ser jaque"
    display.render()
    mock = get_mock_display(display)

    statusCall = find_text_containing(mock, "CHECK")
    assert statusCall is not None


# ==================== AC-06: render() muestra estado de jaque mate ====================


def test_render_shows_checkmate(display, chess):
    # Mate del pastor
    chess.play("e2-e4")
    chess.play("e7-e5")
    chess.play("f1-c4")
    chess.play("b8-c6")
    chess.play("d1-h5")
    chess.play("g8-f6")
    chess.play("h5-f7")  # Jaque mate
    display.render()
    mock = get_mock_display(display)

    statusCall = find_text_containing(mock, "MATE")
    assert statusCall is not None


# ==================== AC-07: render() muestra estado de tablas ====================


def test_render_shows_draw(display, chess):
    # Material insuficiente: K vs K
    chess.setFen("8/8/8/4k3/8/8/8/4K3 w - - 0 1")
    display.render()
    mock = get_mock_display(display)

    statusCall = find_text_containing(mock, "DRAW")
    assert statusCall is not None


# ==================== AC-08: render() muestra estado de ahogado ====================


def test_render_shows_stalemate(display, chess):
    # Posicion de ahogado clasica
    chess.setFen("k7/8/1K6/8/8/8/8/8 b - - 0 1")
    # Negro no tiene movimientos legales pero no esta en jaque
    # Verificar si es stalemate
    if chess.isStalemate():
        display.render()
        mock = get_mock_display(display)
        statusCall = find_text_containing(mock, "STALE")
        assert statusCall is not None
    else:
        # Usar posicion alternativa de stalemate
        chess.setFen("5k2/5P2/5K2/8/8/8/8/8 b - - 0 1")
        display.render()
        mock = get_mock_display(display)
        statusCall = find_text_containing(mock, "STALE")
        assert statusCall is not None


# ==================== AC-09: flip() invierte orientacion ====================


def test_flip_changes_false_to_true(display):
    assert display.flipped is False
    display.flip()
    assert display.flipped is True


# ==================== AC-10: flip() es toggle ====================


def test_flip_changes_true_to_false(chess):
    from modules.chessdisplay import ChessDisplay

    d = ChessDisplay(chess, sda=21, scl=22, flipped=True)
    assert d.flipped is True
    d.flip()
    assert d.flipped is False


# ==================== AC-11: flip() no llama a render ====================


def test_flip_does_not_call_show(display):
    mock = get_mock_display(display)
    display.flip()
    assert mock.showCount == 0


# ==================== AC-12: Orientacion flipped=False muestra blancas abajo ====================


def test_flipped_false_white_at_bottom(display, chess):
    display.render()
    mock = get_mock_display(display)

    # Con flipped=False, rank 0 (fila 1, blancas) se dibuja en sy=(7-0)*8=56
    # La torre blanca en a1 (file=0, rank=0) esta en sx=0, sy=56
    a1_region = mock.getRegion(0, 56, 8, 8)
    a1_flat = [p for row in a1_region for p in row]
    # a1 es casilla oscura (0+0)%2==0, pieza blanca → pixels 0 sobre fondo 1
    # Debe haber una mezcla de 0s y 1s (pieza sobre casilla oscura)
    assert any(p == 0 for p in a1_flat) and any(p == 1 for p in a1_flat), (
        "a1 debe tener pieza blanca sobre casilla oscura"
    )

    # La torre negra en a8 (file=0, rank=7) esta en sx=0, sy=(7-7)*8=0
    a8_region = mock.getRegion(0, 0, 8, 8)
    a8_flat = [p for row in a8_region for p in row]
    # a8 es casilla clara (0+7)%2==1, pieza negra → pixels 1 (outline) sobre fondo 0
    assert any(p == 1 for p in a8_flat), "a8 debe tener pieza negra"


# ==================== AC-13: Orientacion flipped=True muestra negras abajo ====================


def test_flipped_true_black_at_bottom(chess):
    from modules.chessdisplay import ChessDisplay

    d = ChessDisplay(chess, sda=21, scl=22, flipped=True)
    d.render()
    mock = get_mock_display(d)

    # Con flipped=True, rank 7 (fila 8, negras) se dibuja en sy=7*8=56
    # La torre negra en a8 (file=0, rank=7) esta en sx=(7-0)*8=56, sy=7*8=56
    # (flipped invierte file: sx=(7-file)*8, sy=rank*8)
    a8_region = mock.getRegion(56, 56, 8, 8)
    a8_flat = [p for row in a8_region for p in row]
    # a8: file=0, rank=7, isDark=(0+7)%2==1 → casilla clara, pieza negra → outline pixels ON
    assert any(p == 1 for p in a8_flat), "a8 (negra abajo) debe tener pieza"

    # La torre blanca en a1 (file=0, rank=0) esta en sx=(7-0)*8=56, sy=0*8=0
    a1_region = mock.getRegion(56, 0, 8, 8)
    a1_flat = [p for row in a1_region for p in row]
    assert any(p == 0 for p in a1_flat) and any(p == 1 for p in a1_flat), (
        "a1 (blanca arriba) debe tener pieza"
    )


# ==================== AC-14: render() muestra piezas capturadas ====================


def test_render_shows_captured_pieces(display, chess):
    # Italian game con capturas
    chess.play("e2-e4")
    chess.play("e7-e5")
    chess.play("d2-d4")
    chess.play("e5-d4")  # Peon negro captura peon blanco
    chess.play("d1-d4")  # Dama blanca captura peon negro

    display.render()
    mock = get_mock_display(display)

    # Linea 6 (y=48): capturadas por blancas → peon negro 'p'
    captW = find_text_call(mock, 48)
    assert captW is not None
    assert "p" in captW["text"]

    # Linea 7 (y=56): capturadas por negras → peon blanco 'P'
    captB = find_text_call(mock, 56)
    assert captB is not None
    assert "P" in captB["text"]


# ==================== AC-15: render() con posicion inicial sin capturas ====================


def test_render_initial_no_captures_no_last_move(display, chess):
    display.render()
    mock = get_mock_display(display)

    # Sin ultimo movimiento
    lastMoveCall = find_text_call(mock, 16)
    assert lastMoveCall is None

    # Sin capturadas (lineas 48 y 56 no deben tener text con piezas)
    captW = find_text_call(mock, 48)
    captB = find_text_call(mock, 56)
    assert captW is None
    assert captB is None


# ==================== AC-16: Propiedad flipped es legible y escribible ====================


def test_flipped_property_read_write(display):
    assert display.flipped is False
    display.flipped = True
    assert display.flipped is True
    display.flipped = False
    assert display.flipped is False


# ==================== AC-17: Piezas blancas y negras son visualmente distinguibles ====================


def test_white_black_pieces_distinguishable(display, chess):
    # Posicion con torre blanca en a1 y torre negra en a8
    # a1: casilla oscura, torre blanca (filled bitmap, color=0)
    # b1: casilla clara, caballo blanco (filled bitmap, color=1)
    # a8: casilla clara, torre negra (outline bitmap, color=1)
    # b8: casilla oscura, caballo negro (outline bitmap, color=0)
    display.render()
    mock = get_mock_display(display)

    # Torre blanca en a1 vs torre negra en a8
    # Ambas en casillas de diferente color, pero la comparacion de bitmaps debe
    # mostrar diferencia entre filled y outline
    # Comparar los bitmaps directamente
    rook_filled = _PIECE_BITMAPS["R"]
    rook_outline = _PIECE_OUTLINES["R"]
    assert rook_filled != rook_outline, "Bitmap relleno y contorno deben ser diferentes"

    # Verificar para todas las piezas
    for piece_type in "KQRBNP":
        filled = _PIECE_BITMAPS[piece_type]
        outline = _PIECE_OUTLINES[piece_type]
        assert filled != outline, (
            f"Bitmap de {piece_type}: relleno y contorno deben ser diferentes"
        )


# ==================== AC-18: Patron ajedrezado correcto ====================


def test_checkered_pattern_correct(display, chess):
    # Usar tablero vacio para verificar solo el patron
    chess.setFen("8/8/8/8/8/8/8/8 w - - 0 1")
    display.render()
    mock = get_mock_display(display)

    # a1 (file=0, rank=0): isDark = (0+0)%2==0 → oscura (pixels=1)
    # En pantalla con flipped=False: sx=0, sy=(7-0)*8=56
    a1_region = mock.getRegion(0, 56, 8, 8)
    for row in a1_region:
        assert all(p == 1 for p in row), "a1 debe ser casilla oscura (todo 1s)"

    # b1 (file=1, rank=0): isDark = (1+0)%2==1 → clara (pixels=0)
    # sx=8, sy=56
    b1_region = mock.getRegion(8, 56, 8, 8)
    for row in b1_region:
        assert all(p == 0 for p in row), "b1 debe ser casilla clara (todo 0s)"

    # a2 (file=0, rank=1): isDark = (0+1)%2==1 → clara
    # sx=0, sy=(7-1)*8=48
    a2_region = mock.getRegion(0, 48, 8, 8)
    for row in a2_region:
        assert all(p == 0 for p in row), "a2 debe ser casilla clara (todo 0s)"

    # b2 (file=1, rank=1): isDark = (1+1)%2==0 → oscura
    # sx=8, sy=48
    b2_region = mock.getRegion(8, 48, 8, 8)
    for row in b2_region:
        assert all(p == 1 for p in row), "b2 debe ser casilla oscura (todo 1s)"


# ==================== Tests adicionales ====================


def test_render_calls_fill_and_show(display):
    display.render()
    mock = get_mock_display(display)
    assert mock.fillCount == 1
    assert mock.showCount == 1


def test_multiple_renders(display, chess):
    display.render()
    chess.play("e2-e4")
    display.render()
    mock = get_mock_display(display)
    assert mock.showCount == 2
    assert mock.fillCount == 2


def test_display_width_height(display):
    mock = get_mock_display(display)
    assert mock.width == 128
    assert mock.height == 64


def test_panel_text_x_offset(display):
    """Verifica que todos los textos del panel comienzan en x=64."""
    display.render()
    mock = get_mock_display(display)
    for call in mock.textCalls:
        assert call["x"] == 64, f"Text '{call['text']}' debe estar en x=64"


def test_outline_is_subset_of_filled():
    """Verifica que cada pixel del outline esta tambien en el bitmap relleno."""
    for piece_type in "KQRBNP":
        filled = _PIECE_BITMAPS[piece_type]
        outline = _PIECE_OUTLINES[piece_type]
        for row in range(8):
            # Todos los bits del outline deben estar en el filled
            assert (outline[row] & filled[row]) == outline[row], (
                f"Pieza {piece_type} row {row}: outline tiene bits fuera del filled"
            )


def test_outline_has_fewer_pixels():
    """Verifica que el outline tiene estrictamente menos pixels que el filled."""
    for piece_type in "KQRBNP":
        filled = _PIECE_BITMAPS[piece_type]
        outline = _PIECE_OUTLINES[piece_type]
        filled_count = sum(bin(b).count("1") for b in filled)
        outline_count = sum(bin(b).count("1") for b in outline)
        assert outline_count < filled_count, (
            f"Pieza {piece_type}: outline ({outline_count}) debe tener menos "
            f"pixels que filled ({filled_count})"
        )


def test_castling_display(display, chess):
    """Verifica que enroque se muestra como ultimo movimiento."""
    chess.play("e2-e4")
    chess.play("e7-e5")
    chess.play("g1-f3")
    chess.play("b8-c6")
    chess.play("f1-c4")
    chess.play("g8-f6")
    chess.play("O-O")
    display.render()
    mock = get_mock_display(display)

    lastMoveCall = find_text_call(mock, 16)
    assert lastMoveCall is not None
    assert "O-O" in lastMoveCall["text"]
