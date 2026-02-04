"""
Tests for stalemate, draw conditions, and related callbacks.
"""

import pytest
from Chess import Chess


class TestStalemate:
    """Tests for stalemate detection."""

    @pytest.mark.draw
    def test_stalemate_basic(self, stalemate_position):
        """Test basic stalemate detection - king has no legal moves but not in check."""
        assert stalemate_position.isStalemate() is True
        assert stalemate_position.isCheck() is False
        assert stalemate_position.isGameOver() is True
        assert stalemate_position.isCheckmate() is False

    @pytest.mark.draw
    def test_stalemate_king_only(self, chess):
        """Test stalemate with lone king cornered."""
        # White king in a1, black queen in c2, black king in b3
        chess.setFen("8/8/8/8/8/1k6/2q5/K7 w - - 0 1")
        assert chess.isStalemate() is True

    @pytest.mark.draw
    def test_stalemate_with_blocked_pawns(self, chess):
        """Test stalemate detection with blocked pawns."""
        chess.setFen("8/8/8/6pk/5pP1/5P1K/8/8 b - - 0 1")
        moves_k = chess.getLegalMoves("h5")
        moves_p = chess.getLegalMoves("g5")
        all_moves = moves_k + moves_p

        if len(all_moves) == 0:
            assert chess.isStalemate() is True
        else:
            assert chess.isStalemate() is False

    @pytest.mark.draw
    def test_not_stalemate_if_can_move(self, chess):
        """Test that position with legal moves is not stalemate."""
        chess.setFen("k7/8/8/8/8/8/8/4K3 b - - 0 1")
        assert chess.isStalemate() is False
        moves = chess.getLegalMoves("a8")
        assert len(moves) > 0


class TestInsufficientMaterial:
    """Tests for insufficient material draw conditions."""

    @pytest.mark.draw
    def test_k_vs_k(self, insufficient_material_k_vs_k):
        """Test K vs K is draw."""
        assert insufficient_material_k_vs_k.isDraw() is True
        assert insufficient_material_k_vs_k.isGameOver() is True

    @pytest.mark.draw
    def test_k_vs_kb(self, insufficient_material_k_vs_kb):
        """Test K vs K+B is draw."""
        assert insufficient_material_k_vs_kb.isDraw() is True

    @pytest.mark.draw
    def test_k_vs_kn(self, insufficient_material_k_vs_kn):
        """Test K vs K+N is draw."""
        assert insufficient_material_k_vs_kn.isDraw() is True

    @pytest.mark.draw
    def test_kb_vs_kb_same_color(self, chess):
        """Test K+B vs K+B with same colored bishops is draw."""
        # Both bishops on light squares
        # d2 = (3,1) -> 3+1=4 (even = light)
        # f6 = (5,5) -> 5+5=10 (even = light)
        chess.setFen("4k3/8/5b2/8/8/8/3B4/4K3 w - - 0 1")
        assert chess.isDraw() is True

    @pytest.mark.draw
    def test_kb_vs_kb_different_color_is_not_draw(self, chess):
        """Test K+B vs K+B with opposite colored bishops is NOT draw."""
        # White bishop on d2 (light: 3+1=4, even)
        # Black bishop on e6 (dark: 4+5=9, odd)
        chess.setFen("4k3/8/4b3/8/8/8/3B4/4K3 w - - 0 1")
        assert chess.isDraw() is False

    @pytest.mark.draw
    def test_with_pawn_is_not_draw(self, chess):
        """Test that position with pawn is NOT draw (pawn can promote)."""
        chess.setFen("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1")
        assert chess.isDraw() is False

    @pytest.mark.draw
    def test_with_rook_is_not_draw(self, chess):
        """Test that K+R vs K is NOT draw."""
        chess.setFen("4k3/8/8/8/8/8/8/4KR2 w - - 0 1")
        assert chess.isDraw() is False


class TestFiftyMoveRule:
    """Tests for 50-move rule draw."""

    @pytest.mark.draw
    def test_fifty_move_rule_triggers(self, fifty_move_rule_position):
        """Test 50-move rule triggers draw after 100 half-moves without pawn/capture."""
        # Position has halfmove=99, one more move triggers draw
        fifty_move_rule_position.play("f1-f2")
        assert fifty_move_rule_position.isDraw() is True
        assert fifty_move_rule_position.isGameOver() is True

    @pytest.mark.draw
    def test_fifty_move_resets_on_capture(self, chess):
        """Test halfmove clock resets to 0 on capture."""
        chess.setFen("4k3/8/8/8/8/5n2/8/4KR2 w - - 90 50")
        chess.play("f1-f3")  # Capture the knight
        fen = chess.getFen()
        halfmove = int(fen.split()[4])
        assert halfmove == 0

    @pytest.mark.draw
    def test_fifty_move_resets_on_pawn_move(self, chess):
        """Test halfmove clock resets to 0 on pawn move."""
        chess.setFen("4k3/8/8/8/8/8/4P3/4K3 w - - 90 50")
        chess.play("e2-e4")
        fen = chess.getFen()
        halfmove = int(fen.split()[4])
        assert halfmove == 0


class TestDrawCallbacks:
    """Tests for draw-related callbacks."""

    @pytest.mark.callback
    def test_stalemate_callback(self, chess):
        """Test onStalemate callback is called."""
        stalemate_called = [False]
        gameover_called = [False]

        def on_stalemate():
            stalemate_called[0] = True

        def on_gameover():
            gameover_called[0] = True

        chess.onStalemate = on_stalemate
        chess.onGameOver = on_gameover

        # Position where move causes stalemate
        chess.setFen("k7/8/2Q5/8/8/8/8/4K3 w - - 0 1")
        chess.play("c6-b6")  # Queen to b6 causes stalemate

        assert stalemate_called[0] is True
        assert gameover_called[0] is True

    @pytest.mark.callback
    def test_draw_callback_fifty_move(self, chess):
        """Test onDraw callback is called for 50-move rule."""
        draw_called = [False]
        gameover_called = [False]

        def on_draw():
            draw_called[0] = True

        def on_gameover():
            gameover_called[0] = True

        chess.onDraw = on_draw
        chess.onGameOver = on_gameover
        chess.setFen("4k3/8/8/8/8/8/8/4KR2 w - - 99 50")
        chess.play("f1-f2")

        assert draw_called[0] is True
        assert gameover_called[0] is True
