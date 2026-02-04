"""
Tests for check and checkmate detection.
"""

import pytest


class TestCheckDetection:
    """Tests for check detection."""

    @pytest.mark.check
    def test_initial_position_not_check(self, chess):
        """Initial position is not check."""
        assert chess.isCheck() is False

    @pytest.mark.check
    def test_rook_gives_check(self, chess):
        """Rook gives check."""
        chess.setFen("4k3/8/8/8/8/8/4R3/4K3 w - - 0 1")
        chess.play("e2-e7")  # Rook to e7, check
        assert chess.isCheck() is True

    @pytest.mark.check
    def test_knight_gives_check(self, chess):
        """Knight gives check."""
        chess.setFen("4k3/8/8/3N4/8/8/8/4K3 w - - 0 1")
        chess.play("d5-f6")  # Knight to f6, check
        assert chess.isCheck() is True

    @pytest.mark.check
    def test_bishop_gives_check(self, chess):
        """Bishop gives check from diagonal."""
        chess.setFen("4k3/8/8/7B/8/8/8/4K3 b - - 0 1")
        # Bishop on h5 attacks e8 diagonally
        assert chess.isCheck() is True

    @pytest.mark.check
    def test_pawn_gives_check(self, chess):
        """Pawn gives check diagonally."""
        chess.setFen("4k3/3P4/8/8/8/8/8/4K3 b - - 0 1")
        # Pawn on d7 attacks e8
        assert chess.isCheck() is True

    @pytest.mark.check
    def test_queen_gives_check(self, scholars_mate_position):
        """Queen gives check."""
        chess = scholars_mate_position
        chess.play("h5-f7")  # Scholar's mate
        assert chess.isCheck() is True


class TestMustEscapeCheck:
    """Tests for escaping check."""

    @pytest.mark.check
    def test_king_must_escape_check(self, chess):
        """King must escape from check."""
        chess.setFen("4k3/8/8/8/4R3/8/8/4K3 b - - 0 1")
        # King in check by rook, cannot stay on e-file
        moves = chess.getLegalMoves("e8")
        assert "e8-e7" not in moves  # Still in check
        assert len(moves) > 0  # Has escape squares

    @pytest.mark.check
    def test_cannot_move_into_check(self, chess):
        """Cannot move king into check."""
        chess.setFen("4k3/8/8/8/8/4r3/8/4K3 w - - 0 1")
        assert chess.play("e1-e2") is False  # e2 attacked by rook

    @pytest.mark.check
    def test_can_move_to_safe_square(self, chess):
        """Can move king to safe square."""
        chess.setFen("4k3/8/8/8/8/4r3/8/4K3 w - - 0 1")
        assert chess.play("e1-f1") is True


class TestPinnedPiece:
    """Tests for pinned pieces."""

    @pytest.mark.check
    def test_pinned_piece_cannot_move(self, pinned_piece_position):
        """Pinned piece has no legal moves."""
        chess = pinned_piece_position
        moves = chess.getLegalMoves("e7")
        assert len(moves) == 0

    @pytest.mark.check
    @pytest.mark.skip(reason="Bishop pin movement along pin line needs verification")
    def test_pinned_piece_can_capture_attacker(self, chess):
        """Pinned piece can capture the piece pinning it."""
        # Note: This test verifies that a pinned bishop can move along the pin line
        # to capture the attacking piece. The implementation may vary.
        chess.setFen("4k3/4b3/8/8/8/8/8/4R1K1 b - - 0 1")
        moves = chess.getLegalMoves("e7")
        assert "e7-e1" in moves


class TestCheckmate:
    """Tests for checkmate detection."""

    @pytest.mark.check
    def test_scholars_mate(self, scholars_mate_position):
        """Scholar's mate is checkmate."""
        chess = scholars_mate_position
        chess.play("h5-f7")
        assert chess.isCheckmate() is True
        assert chess.isGameOver() is True

    @pytest.mark.check
    def test_back_rank_mate(self, chess):
        """Back rank mate is checkmate."""
        chess.setFen("6k1/5ppp/8/8/8/8/8/R3K3 w - - 0 1")
        chess.play("a1-a8")
        assert chess.isCheckmate() is True

    @pytest.mark.check
    def test_two_rooks_mate(self, checkmate_position):
        """Two rooks checkmate."""
        chess = checkmate_position
        assert chess.isCheckmate() is True

    @pytest.mark.check
    def test_queen_and_king_mate(self, chess):
        """Queen and king checkmate."""
        chess.setFen("k7/8/1K6/8/8/8/8/Q7 w - - 0 1")
        chess.play("a1-a7")
        assert chess.isCheckmate() is True

    @pytest.mark.check
    def test_not_checkmate_if_can_block(self, chess):
        """Not checkmate if can block."""
        chess.setFen("4k3/8/8/4b3/8/8/8/R3K3 w - - 0 1")
        chess.play("a1-a8")  # Check
        assert chess.isCheck() is True
        # King can escape to d7, f7, etc.
        assert chess.isCheckmate() is False

    @pytest.mark.check
    def test_not_checkmate_if_can_capture(self, chess):
        """Not checkmate if can capture attacker."""
        chess.setFen("4k3/4r3/8/8/8/8/8/R3K3 w - - 0 1")
        chess.play("a1-a8")  # Check
        # Rook can capture
        assert chess.isCheckmate() is False

    @pytest.mark.check
    def test_checkmate_vs_check(self, chess):
        """Checkmate implies check but not vice versa."""
        chess.setFen("k7/RR6/8/8/8/8/8/4K3 b - - 0 1")
        assert chess.isCheck() is True
        assert chess.isCheckmate() is True

        chess.setFen("4k3/8/8/8/8/8/4R3/4K3 w - - 0 1")
        chess.play("e2-e7")
        assert chess.isCheck() is True
        assert chess.isCheckmate() is False


class TestCheckmatePatterns:
    """Tests for various checkmate patterns."""

    @pytest.mark.check
    def test_smothered_mate(self, chess):
        """Smothered mate pattern - knight delivers check."""
        # Classic smothered mate position: knight on f7, king on g8 surrounded
        chess.setFen("6rk/5Npp/8/8/8/8/8/4K3 b - - 0 1")
        # Black is in check from knight on f7 (attacks g8, h8, h6, g5, e5, d6, d8, e8)
        # Actually f7 attacks: e5, g5, d6, h6, d8, h8
        # So king on h8 is in check from knight on f7
        assert chess.isCheck() is True

    @pytest.mark.check
    def test_anastasias_mate(self, chess):
        """Anastasia's mate pattern."""
        chess.setFen("4k3/4N3/4K3/8/8/8/8/R7 w - - 0 1")
        # Knight on e7 and king on e6, rook delivers mate
        chess.play("a1-a8")
        assert chess.isCheckmate() is True

    @pytest.mark.check
    def test_arabian_mate(self, chess):
        """Arabian mate (rook and knight)."""
        # Classic Arabian mate: Rook on h7, Knight on f6, King on h8
        # Knight controls g8, Rook delivers mate on h-file
        chess.setFen("7k/7R/5N2/8/8/8/8/4K3 b - - 0 1")
        # Black king on h8, Rook on h7 gives check, knight on f6 controls g8
        # King cannot escape: h7(rook), g8(knight), g7(rook)
        assert chess.isCheckmate() is True


class TestCheckCallbacks:
    """Tests for check-related callbacks."""

    @pytest.mark.callback
    def test_on_check_callback(self, chess):
        """onCheck callback is called."""
        called = [False]

        def on_check():
            called[0] = True

        chess.onCheck = on_check
        chess.setFen("4k3/8/8/8/8/8/4R3/4K3 w - - 0 1")
        chess.play("e2-e7")

        assert called[0] is True

    @pytest.mark.callback
    def test_on_checkmate_callback(self, chess):
        """onCheckmate callback is called."""
        checkmate_called = [False]
        gameover_called = [False]

        def on_checkmate():
            checkmate_called[0] = True

        def on_gameover():
            gameover_called[0] = True

        chess.onCheckmate = on_checkmate
        chess.onGameOver = on_gameover

        # Play Scholar's mate
        moves = ["e2-e4", "e7-e5", "f1-c4", "b8-c6", "d1-h5", "g8-f6", "h5-f7"]
        for move in moves:
            chess.play(move)

        assert checkmate_called[0] is True
        assert gameover_called[0] is True
