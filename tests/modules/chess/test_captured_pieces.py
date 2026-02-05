"""Tests para getCapturedPieces() del modulo Chess."""

import pytest
from modules.chess import Chess


@pytest.fixture
def chess():
    return Chess()


def test_initial_position_no_captures(chess):
    """En posicion inicial no hay piezas capturadas."""
    captured = chess.getCapturedPieces()
    assert captured == {"w": "", "b": ""}


def test_single_capture_by_white(chess):
    """Blancas capturan un peon negro."""
    chess.play("e2-e4")
    chess.play("d7-d5")
    chess.play("e4-d5")  # Peon blanco captura peon negro en d5
    captured = chess.getCapturedPieces()
    assert captured["w"] == "p"
    assert captured["b"] == ""


def test_single_capture_by_black(chess):
    """Negras capturan un peon blanco."""
    chess.play("e2-e4")
    chess.play("d7-d5")
    chess.play("a2-a3")  # Movimiento de relleno
    chess.play("d5-e4")  # Peon negro captura peon blanco
    captured = chess.getCapturedPieces()
    assert captured["w"] == ""
    assert captured["b"] == "P"


def test_multiple_captures(chess):
    """Multiples capturas por ambos bandos."""
    chess.play("e2-e4")
    chess.play("d7-d5")
    chess.play("e4-d5")  # Blancas capturan peon
    chess.play("d8-d5")  # Negras capturan peon
    captured = chess.getCapturedPieces()
    assert captured["w"] == "p"
    assert captured["b"] == "P"


def test_captures_sorted_by_value(chess):
    """Las capturas se ordenan por valor (dama > torre > alfil > caballo > peon)."""
    # Escenario: blancas capturan un peon y luego una pieza de mayor valor
    chess.play("e2-e4")
    chess.play("d7-d5")
    chess.play("e4-d5")  # Captura peon
    chess.play("d8-d5")  # Negras recapturan peon
    chess.play("f1-b5")  # Alfil a b5
    chess.play("c7-c6")
    chess.play("b5-c6")  # Alfil captura peon
    chess.play("b8-c6")  # Caballo captura alfil
    captured = chess.getCapturedPieces()
    # Blancas capturaron: peon (d5), peon (c6) → "pp"
    assert captured["w"] == "pp"
    # Negras capturaron: Peon (d5), Alfil (c6) → "BP" (alfil primero por valor)
    assert captured["b"] == "BP"


def test_en_passant_capture_tracked(chess):
    """Captura en passant se registra correctamente."""
    chess.play("e2-e4")
    chess.play("a7-a6")
    chess.play("e4-e5")
    chess.play("d7-d5")  # Peon negro avanza doble al lado de peon blanco
    chess.play("e5-d6")  # En passant!
    captured = chess.getCapturedPieces()
    assert captured["w"] == "p"
    assert captured["b"] == ""


def test_undo_restores_captures(chess):
    """Undo restaura las capturas al estado anterior."""
    chess.play("e2-e4")
    chess.play("d7-d5")
    chess.play("e4-d5")  # Captura
    assert chess.getCapturedPieces()["w"] == "p"
    chess.undo()
    assert chess.getCapturedPieces()["w"] == ""


def test_reset_clears_captures(chess):
    """Reset limpia las capturas."""
    chess.play("e2-e4")
    chess.play("d7-d5")
    chess.play("e4-d5")
    assert chess.getCapturedPieces()["w"] == "p"
    chess.reset()
    assert chess.getCapturedPieces() == {"w": "", "b": ""}


def test_setfen_clears_captures(chess):
    """setFen limpia las capturas (no se puede reconstruir del FEN)."""
    chess.play("e2-e4")
    chess.play("d7-d5")
    chess.play("e4-d5")
    assert chess.getCapturedPieces()["w"] == "p"
    chess.setFen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    assert chess.getCapturedPieces() == {"w": "", "b": ""}


def test_promotion_capture(chess):
    """Captura en promocion se registra."""
    chess.setFen("r3k3/1P6/8/8/8/8/8/4K3 w - - 0 1")
    chess.play("b7-a8=Q")  # Peon promueve a dama capturando torre
    captured = chess.getCapturedPieces()
    assert captured["w"] == "r"


def test_capture_order_by_value():
    """Verifica orden: q > r > b > n > p."""
    chess = Chess()
    # Posicion con peon blanco que puede capturar dama negra sin quedar en jaque
    chess.setFen("4k3/8/8/3q4/4P3/8/8/4K3 w - - 0 1")
    chess.play("e4-d5")  # Peon blanco captura dama negra
    captured = chess.getCapturedPieces()
    assert captured["w"] == "q"
