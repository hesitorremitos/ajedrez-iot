"""
Pytest configuration and fixtures for Chess module tests.
"""

import sys
import os
import pytest

# Add parent directory to path to import Chess module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Chess import Chess


@pytest.fixture
def chess():
    """Fixture that provides a fresh Chess instance for each test."""
    return Chess()


@pytest.fixture
def chess_debug():
    """Fixture that provides a Chess instance with debug mode enabled."""
    return Chess(debug=True)


@pytest.fixture
def italian_game(chess):
    """Fixture that sets up the Italian Game opening."""
    moves = ["e2-e4", "e7-e5", "g1-f3", "b8-c6", "f1-c4", "f8-c5"]
    for move in moves:
        chess.play(move)
    return chess


@pytest.fixture
def scholars_mate_position(chess):
    """Fixture that sets up position just before Scholar's mate."""
    moves = ["e2-e4", "e7-e5", "f1-c4", "b8-c6", "d1-h5", "g8-f6"]
    for move in moves:
        chess.play(move)
    return chess


@pytest.fixture
def castling_ready_white(chess):
    """Fixture with white ready to castle both sides."""
    chess.setFen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1")
    return chess


@pytest.fixture
def castling_ready_black(chess):
    """Fixture with black ready to castle (black to move)."""
    chess.setFen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R b kq - 0 1")
    return chess


@pytest.fixture
def promotion_ready_white(chess):
    """Fixture with white pawn ready to promote."""
    chess.setFen("8/P7/8/8/8/8/8/4K2k w - - 0 1")
    return chess


@pytest.fixture
def promotion_ready_black(chess):
    """Fixture with black pawn ready to promote."""
    chess.setFen("4K2k/8/8/8/8/8/p7/8 b - - 0 1")
    return chess


@pytest.fixture
def en_passant_ready_white(chess):
    """Fixture with white pawn ready for en passant capture."""
    chess.setFen("4k3/8/8/pP6/8/8/8/4K3 w - a6 0 1")
    return chess


@pytest.fixture
def en_passant_ready_black(chess):
    """Fixture with black pawn ready for en passant capture."""
    chess.setFen("4k3/8/8/8/Pp6/8/8/4K3 b - a3 0 1")
    return chess


@pytest.fixture
def stalemate_position(chess):
    """Fixture with stalemate position (black to move, no legal moves but not in check)."""
    chess.setFen("k7/8/1Q6/8/8/8/8/4K3 b - - 0 1")
    return chess


@pytest.fixture
def checkmate_position(chess):
    """Fixture with checkmate position (black in checkmate)."""
    chess.setFen("k7/RR6/8/8/8/8/8/4K3 b - - 0 1")
    return chess


@pytest.fixture
def insufficient_material_k_vs_k(chess):
    """Fixture with K vs K (insufficient material)."""
    chess.setFen("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
    return chess


@pytest.fixture
def insufficient_material_k_vs_kb(chess):
    """Fixture with K vs K+B (insufficient material)."""
    chess.setFen("4k3/8/8/8/8/8/8/4KB2 w - - 0 1")
    return chess


@pytest.fixture
def insufficient_material_k_vs_kn(chess):
    """Fixture with K vs K+N (insufficient material)."""
    chess.setFen("4k3/8/8/8/8/8/8/4KN2 w - - 0 1")
    return chess


@pytest.fixture
def fifty_move_rule_position(chess):
    """Fixture with position near 50-move rule draw."""
    chess.setFen("4k3/8/8/8/8/8/8/4KR2 w - - 99 50")
    return chess


@pytest.fixture
def complex_middlegame(chess):
    """Fixture with a complex middlegame position."""
    chess.setFen(
        "r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 8"
    )
    return chess


@pytest.fixture
def pinned_piece_position(chess):
    """Fixture with a pinned piece (bishop pinned to king)."""
    chess.setFen("4k3/4b3/8/8/8/8/8/4RK2 b - - 0 1")
    return chess


@pytest.fixture
def discovered_check_position(chess):
    """Fixture ready for discovered check."""
    chess.setFen("4k3/8/8/4B3/4R3/8/8/4K3 w - - 0 1")
    return chess


# Helper functions for tests
def make_moves(chess, moves):
    """Helper to make a series of moves."""
    results = []
    for move in moves:
        results.append(chess.play(move))
    return results


def assert_piece_at(chess, square, expected_piece):
    """Assert a specific piece is at a square."""
    actual = chess.getPiece(square)
    assert actual == expected_piece, (
        f"Expected '{expected_piece}' at {square}, got '{actual}'"
    )
