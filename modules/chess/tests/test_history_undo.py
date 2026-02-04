"""
Tests for history, undo, and reset functionality.
"""

import pytest
from Chess import Chess


class TestHistory:
    """Tests for getHistory() functionality."""

    @pytest.mark.history
    def test_history_basic(self, chess):
        """Test basic history tracking."""
        chess.play("e2-e4")
        chess.play("e7-e5")
        chess.play("g1-f3")
        chess.play("b8-c6")

        history = chess.getHistory()

        assert len(history) == 2
        assert history[0] == ("e2-e4", "e7-e5")
        assert history[1] == ("g1-f3", "b8-c6")

    @pytest.mark.history
    def test_history_incomplete_turn(self, chess):
        """Test history with incomplete turn (white moved, black hasn't)."""
        chess.play("e2-e4")
        chess.play("e7-e5")
        chess.play("g1-f3")  # White moves, black hasn't

        history = chess.getHistory()

        assert len(history) == 2
        assert history[1] == ("g1-f3", "")

    @pytest.mark.history
    def test_history_empty(self, chess):
        """Test history is empty at start."""
        history = chess.getHistory()
        assert len(history) == 0


class TestUndo:
    """Tests for undo() functionality."""

    @pytest.mark.history
    def test_undo_single_move(self, chess):
        """Test undo of a single move."""
        chess.play("e2-e4")
        result = chess.undo()

        assert result is True
        assert chess.getPiece("e4") == " "
        assert chess.getPiece("e2") == "P"
        assert chess.getTurn() == "w"

    @pytest.mark.history
    def test_undo_multiple_moves(self, chess):
        """Test undoing multiple moves returns to initial position."""
        chess.play("e2-e4")
        chess.play("e7-e5")
        chess.play("g1-f3")

        chess.undo()  # Undo g1-f3
        assert chess.getPiece("f3") == " "
        assert chess.getPiece("g1") == "N"

        chess.undo()  # Undo e7-e5
        assert chess.getPiece("e5") == " "
        assert chess.getPiece("e7") == "p"

        chess.undo()  # Undo e2-e4
        assert chess.getPiece("e4") == " "
        assert chess.getPiece("e2") == "P"

        # Verify initial position
        fen = chess.getFen()
        expected = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        assert fen == expected

    @pytest.mark.history
    def test_undo_no_moves(self, chess):
        """Test undo returns False when no moves to undo."""
        result = chess.undo()
        assert result is False

    @pytest.mark.history
    def test_undo_capture(self, chess):
        """Test undo restores captured piece."""
        chess.play("e2-e4")
        chess.play("d7-d5")
        chess.play("e4-d5")  # Capture

        chess.undo()

        assert chess.getPiece("e4") == "P"
        assert chess.getPiece("d5") == "p"

    @pytest.mark.special
    def test_undo_castling_kingside(self, castling_ready_white):
        """Test undo of kingside castling."""
        castling_ready_white.play("O-O")
        castling_ready_white.undo()

        assert castling_ready_white.getPiece("e1") == "K"
        assert castling_ready_white.getPiece("h1") == "R"
        assert castling_ready_white.getPiece("g1") == " "
        assert castling_ready_white.getPiece("f1") == " "

    @pytest.mark.special
    def test_undo_castling_queenside(self, castling_ready_white):
        """Test undo of queenside castling."""
        castling_ready_white.play("O-O-O")
        castling_ready_white.undo()

        assert castling_ready_white.getPiece("e1") == "K"
        assert castling_ready_white.getPiece("a1") == "R"
        assert castling_ready_white.getPiece("c1") == " "
        assert castling_ready_white.getPiece("d1") == " "

    @pytest.mark.special
    def test_undo_en_passant(self, chess):
        """Test undo of en passant capture."""
        chess.play("e2-e4")
        chess.play("a7-a6")
        chess.play("e4-e5")
        chess.play("d7-d5")
        chess.play("e5-d6")  # En passant

        chess.undo()

        assert chess.getPiece("e5") == "P"
        assert chess.getPiece("d5") == "p"
        assert chess.getPiece("d6") == " "

    @pytest.mark.special
    def test_undo_promotion(self, promotion_ready_white):
        """Test undo of pawn promotion."""
        promotion_ready_white.play("a7-a8=Q")
        promotion_ready_white.undo()

        assert promotion_ready_white.getPiece("a7") == "P"
        assert promotion_ready_white.getPiece("a8") == " "


class TestReset:
    """Tests for reset() functionality."""

    @pytest.mark.history
    def test_reset(self, chess):
        """Test reset returns to initial position."""
        chess.play("e2-e4")
        chess.play("e7-e5")
        chess.play("g1-f3")

        chess.reset()

        fen = chess.getFen()
        expected = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        assert fen == expected

        history = chess.getHistory()
        assert len(history) == 0

        assert chess.getTurn() == "w"

    @pytest.mark.history
    def test_reset_clears_game_state(self, chess):
        """Test reset clears all game state."""
        chess.play("e2-e4")
        chess.play("e7-e5")

        chess.reset()

        assert chess.isCheck() is False
        assert chess.isCheckmate() is False
        assert chess.isStalemate() is False
        assert chess.isDraw() is False
        assert chess.isGameOver() is False


class TestBoardRepresentation:
    """Tests for board string representation."""

    @pytest.mark.basic
    def test_board_str(self, chess):
        """Test string representation of board."""
        board_str = str(chess)

        assert "a   b   c   d   e   f   g   h" in board_str
        assert "8 |" in board_str
        assert "1 |" in board_str
        assert "Turn:" in board_str or "White" in board_str
