"""
Tests for basic piece movements.
"""

import pytest


def assert_piece_at(chess, square, expected_piece):
    """Assert a specific piece is at a square."""
    actual = chess.getPiece(square)
    assert actual == expected_piece, (
        f"Expected '{expected_piece}' at {square}, got '{actual}'"
    )


class TestPawnMoves:
    """Tests for pawn movements."""

    @pytest.mark.basic
    def test_pawn_single_push(self, chess):
        """Pawn can move one square forward."""
        assert chess.play("e2-e3") is True
        assert_piece_at(chess, "e3", "P")
        assert_piece_at(chess, "e2", " ")

    @pytest.mark.basic
    def test_pawn_double_push_from_start(self, chess):
        """Pawn can move two squares from starting position."""
        assert chess.play("e2-e4") is True
        assert_piece_at(chess, "e4", "P")

    @pytest.mark.basic
    def test_black_pawn_single_push(self, chess):
        """Black pawn can move one square forward."""
        chess.play("e2-e4")
        assert chess.play("e7-e6") is True
        assert_piece_at(chess, "e6", "p")

    @pytest.mark.basic
    def test_black_pawn_double_push(self, chess):
        """Black pawn can move two squares from starting position."""
        chess.play("e2-e4")
        assert chess.play("e7-e5") is True
        assert_piece_at(chess, "e5", "p")

    @pytest.mark.basic
    def test_pawn_capture_diagonal(self, chess):
        """Pawn can capture diagonally."""
        chess.play("e2-e4")
        chess.play("d7-d5")
        assert chess.play("e4-d5") is True
        assert_piece_at(chess, "d5", "P")
        assert_piece_at(chess, "e4", " ")

    @pytest.mark.basic
    def test_pawn_cannot_move_backward(self, chess):
        """Pawn cannot move backward."""
        chess.play("e2-e4")
        chess.play("e7-e5")
        assert chess.play("e4-e3") is False

    @pytest.mark.basic
    def test_pawn_cannot_move_diagonal_without_capture(self, chess):
        """Pawn cannot move diagonally without a capture."""
        assert chess.play("e2-d3") is False

    @pytest.mark.basic
    def test_pawn_blocked_by_piece(self, chess):
        """Pawn cannot move through pieces."""
        chess.setFen("4k3/8/8/4p3/4P3/8/8/4K3 w - - 0 1")
        assert chess.play("e4-e5") is False

    @pytest.mark.basic
    def test_pawn_cannot_double_push_after_moving(self, chess):
        """Pawn cannot double push if not on starting rank."""
        chess.play("e2-e3")
        chess.play("e7-e6")
        assert chess.play("e3-e5") is False


class TestKnightMoves:
    """Tests for knight movements."""

    @pytest.mark.basic
    def test_knight_l_shape_move(self, chess):
        """Knight moves in L-shape."""
        assert chess.play("g1-f3") is True
        assert_piece_at(chess, "f3", "N")

    @pytest.mark.basic
    def test_knight_can_jump_over_pieces(self, chess):
        """Knight can jump over other pieces."""
        assert chess.play("b1-c3") is True
        assert_piece_at(chess, "c3", "N")

    @pytest.mark.basic
    def test_black_knight_move(self, chess):
        """Black knight can move."""
        chess.play("e2-e4")
        assert chess.play("b8-c6") is True
        assert_piece_at(chess, "c6", "n")

    @pytest.mark.basic
    def test_knight_cannot_move_straight(self, chess):
        """Knight cannot move in straight lines."""
        assert chess.play("g1-g3") is False

    @pytest.mark.basic
    def test_knight_all_moves(self, chess):
        """Knight has all 8 possible moves from center."""
        chess.setFen("8/8/8/4N3/8/8/8/4K2k w - - 0 1")
        moves = chess.getLegalMoves("e5")
        expected = [
            "e5-f7",
            "e5-g6",
            "e5-g4",
            "e5-f3",
            "e5-d3",
            "e5-c4",
            "e5-c6",
            "e5-d7",
        ]
        assert len(moves) == 8
        for move in expected:
            assert move in moves, f"Missing move: {move}"


class TestBishopMoves:
    """Tests for bishop movements."""

    @pytest.mark.basic
    def test_bishop_diagonal_move(self, chess):
        """Bishop moves diagonally."""
        chess.play("e2-e4")
        chess.play("e7-e5")
        assert chess.play("f1-c4") is True
        assert_piece_at(chess, "c4", "B")

    @pytest.mark.basic
    def test_bishop_blocked_by_pawn(self, chess):
        """Bishop cannot move through pawns."""
        assert chess.play("f1-c4") is False

    @pytest.mark.basic
    def test_bishop_capture(self, chess):
        """Bishop can capture."""
        chess.play("e2-e4")
        chess.play("d7-d5")
        chess.play("f1-b5")
        chess.play("c7-c6")
        assert chess.play("b5-c6") is True
        assert_piece_at(chess, "c6", "B")

    @pytest.mark.basic
    def test_bishop_cannot_move_straight(self, chess):
        """Bishop cannot move in straight lines."""
        chess.setFen("4k3/8/8/4B3/8/8/8/4K3 w - - 0 1")
        assert chess.play("e5-e6") is False


class TestRookMoves:
    """Tests for rook movements."""

    @pytest.mark.basic
    def test_rook_vertical_move(self, chess):
        """Rook moves vertically."""
        chess.play("a2-a4")
        chess.play("e7-e5")
        assert chess.play("a1-a3") is True
        assert_piece_at(chess, "a3", "R")

    @pytest.mark.basic
    def test_rook_horizontal_move(self, chess):
        """Rook moves horizontally."""
        chess.play("a2-a4")
        chess.play("e7-e5")
        chess.play("a1-a3")
        chess.play("d7-d5")
        assert chess.play("a3-h3") is True
        assert_piece_at(chess, "h3", "R")

    @pytest.mark.basic
    def test_rook_blocked_by_pawn(self, chess):
        """Rook cannot move through pawns."""
        assert chess.play("a1-a5") is False

    @pytest.mark.basic
    def test_rook_cannot_move_diagonal(self, chess):
        """Rook cannot move diagonally."""
        chess.setFen("4k3/8/8/4R3/8/8/8/4K3 w - - 0 1")
        assert chess.play("e5-f6") is False


class TestQueenMoves:
    """Tests for queen movements."""

    @pytest.mark.basic
    def test_queen_diagonal_move(self, chess):
        """Queen moves diagonally."""
        chess.play("e2-e4")
        chess.play("e7-e5")
        assert chess.play("d1-h5") is True
        assert_piece_at(chess, "h5", "Q")

    @pytest.mark.basic
    def test_queen_straight_move(self, chess):
        """Queen moves in straight lines."""
        chess.play("d2-d4")
        chess.play("e7-e5")
        assert chess.play("d1-d3") is True
        assert_piece_at(chess, "d3", "Q")

    @pytest.mark.basic
    def test_queen_blocked(self, chess):
        """Queen cannot move through pieces."""
        assert chess.play("d1-d5") is False


class TestKingMoves:
    """Tests for king movements."""

    @pytest.mark.basic
    def test_king_one_square_move(self, chess):
        """King moves one square."""
        chess.play("e2-e4")
        chess.play("e7-e5")
        assert chess.play("e1-e2") is True
        assert_piece_at(chess, "e2", "K")

    @pytest.mark.basic
    def test_king_cannot_move_two_squares(self, chess):
        """King cannot move more than one square (except castling)."""
        chess.play("e2-e4")
        chess.play("e7-e5")
        assert chess.play("e1-e3") is False

    @pytest.mark.basic
    def test_king_cannot_move_to_attacked_square(self, chess):
        """King cannot move to attacked square."""
        chess.setFen("4k3/8/8/8/8/4r3/8/4K3 w - - 0 1")
        assert chess.play("e1-e2") is False  # e2 attacked by rook

    @pytest.mark.basic
    def test_king_can_move_to_safe_square(self, chess):
        """King can move to non-attacked square."""
        chess.setFen("4k3/8/8/8/8/4r3/8/4K3 w - - 0 1")
        assert chess.play("e1-f1") is True


class TestTurnValidation:
    """Tests for turn validation."""

    @pytest.mark.basic
    def test_cannot_move_opponent_piece(self, chess):
        """Cannot move opponent's pieces."""
        assert chess.play("e7-e5") is False  # Black piece on white's turn

    @pytest.mark.basic
    def test_turn_changes_after_move(self, chess):
        """Turn changes after a move."""
        assert chess.getTurn() == "w"
        chess.play("e2-e4")
        assert chess.getTurn() == "b"

    @pytest.mark.basic
    def test_turn_alternates(self, chess):
        """Turn alternates between players."""
        chess.play("e2-e4")
        chess.play("e7-e5")
        assert chess.getTurn() == "w"


class TestGetLegalMoves:
    """Tests for getLegalMoves method."""

    @pytest.mark.basic
    def test_pawn_initial_moves(self, chess):
        """Pawn has 2 moves from starting position."""
        moves = chess.getLegalMoves("e2")
        assert "e2-e3" in moves
        assert "e2-e4" in moves
        assert len(moves) == 2

    @pytest.mark.basic
    def test_knight_initial_moves(self, chess):
        """Knight has 2 moves from starting position."""
        moves = chess.getLegalMoves("g1")
        assert "g1-f3" in moves
        assert "g1-h3" in moves
        assert len(moves) == 2

    @pytest.mark.basic
    def test_empty_square_no_moves(self, chess):
        """Empty square returns no moves."""
        moves = chess.getLegalMoves("e4")
        assert moves == []

    @pytest.mark.basic
    def test_opponent_piece_no_moves(self, chess):
        """Opponent's piece returns no moves on current turn."""
        moves = chess.getLegalMoves("e7")  # Black pawn, white's turn
        assert moves == []


class TestGetPiece:
    """Tests for getPiece method."""

    @pytest.mark.basic
    def test_get_white_pieces(self, chess):
        """Get white pieces from initial position."""
        assert chess.getPiece("e1") == "K"
        assert chess.getPiece("d1") == "Q"
        assert chess.getPiece("a1") == "R"
        assert chess.getPiece("b1") == "N"
        assert chess.getPiece("c1") == "B"
        assert chess.getPiece("e2") == "P"

    @pytest.mark.basic
    def test_get_black_pieces(self, chess):
        """Get black pieces from initial position."""
        assert chess.getPiece("e8") == "k"
        assert chess.getPiece("d8") == "q"
        assert chess.getPiece("a8") == "r"
        assert chess.getPiece("b8") == "n"
        assert chess.getPiece("c8") == "b"
        assert chess.getPiece("e7") == "p"

    @pytest.mark.basic
    def test_get_empty_square(self, chess):
        """Empty square returns space character."""
        assert chess.getPiece("e4") == " "

    @pytest.mark.basic
    def test_get_invalid_square(self, chess):
        """Invalid square returns space character."""
        assert chess.getPiece("z9") == " "
