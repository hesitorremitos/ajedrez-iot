"""
Tests for special moves: castling, promotion, and en passant.
"""

import pytest


def assert_piece_at(chess, square, expected_piece):
    """Assert a specific piece is at a square."""
    actual = chess.getPiece(square)
    assert actual == expected_piece, (
        f"Expected '{expected_piece}' at {square}, got '{actual}'"
    )


class TestCastlingWhite:
    """Tests for white castling."""

    @pytest.mark.special
    def test_kingside_castling(self, castling_ready_white):
        """White can castle kingside."""
        chess = castling_ready_white
        assert chess.play("O-O") is True
        assert_piece_at(chess, "g1", "K")
        assert_piece_at(chess, "f1", "R")
        assert_piece_at(chess, "e1", " ")
        assert_piece_at(chess, "h1", " ")

    @pytest.mark.special
    def test_queenside_castling(self, castling_ready_white):
        """White can castle queenside."""
        chess = castling_ready_white
        assert chess.play("O-O-O") is True
        assert_piece_at(chess, "c1", "K")
        assert_piece_at(chess, "d1", "R")
        assert_piece_at(chess, "e1", " ")
        assert_piece_at(chess, "a1", " ")

    @pytest.mark.special
    def test_castling_in_legal_moves(self, castling_ready_white):
        """Castling moves appear in getLegalMoves."""
        chess = castling_ready_white
        moves = chess.getLegalMoves("e1")
        assert "O-O" in moves
        assert "O-O-O" in moves


class TestCastlingBlack:
    """Tests for black castling."""

    @pytest.mark.special
    def test_kingside_castling(self, castling_ready_black):
        """Black can castle kingside."""
        chess = castling_ready_black
        assert chess.play("O-O") is True
        assert_piece_at(chess, "g8", "k")
        assert_piece_at(chess, "f8", "r")

    @pytest.mark.special
    def test_queenside_castling(self, castling_ready_black):
        """Black can castle queenside."""
        chess = castling_ready_black
        assert chess.play("O-O-O") is True
        assert_piece_at(chess, "c8", "k")
        assert_piece_at(chess, "d8", "r")


class TestCastlingRestrictions:
    """Tests for castling restrictions."""

    @pytest.mark.special
    def test_cannot_castle_in_check(self, chess):
        """Cannot castle while in check."""
        # Bishop on b4 gives check to king on e1 (diagonal b4-e1, d2 pawn removed)
        chess.setFen("r3k2r/pppppppp/8/8/1b6/8/PPP2PPP/R3K2R w KQkq - 0 1")
        assert chess.play("O-O") is False

    @pytest.mark.special
    def test_cannot_castle_through_attack(self, chess):
        """Cannot castle through attacked square."""
        # Bishop on c4 attacks f1 (diagonal c4-f1)
        chess.setFen("r3k2r/pppppppp/8/8/2b5/8/PPPP1PPP/R3K2R w KQkq - 0 1")
        assert chess.play("O-O") is False

    @pytest.mark.special
    def test_cannot_castle_after_king_move(self, chess):
        """Cannot castle after king has moved."""
        chess.play("e2-e4")
        chess.play("e7-e5")
        chess.play("e1-e2")  # King moves
        chess.play("g8-f6")
        chess.play("e2-e1")  # King returns
        chess.play("b8-c6")
        chess.play("g1-f3")
        chess.play("f8-c5")
        chess.play("f1-c4")
        chess.play("d7-d6")
        assert chess.play("O-O") is False

    @pytest.mark.special
    def test_cannot_castle_after_rook_move(self, chess):
        """Cannot castle after rook has moved."""
        chess.play("h2-h4")
        chess.play("e7-e5")
        chess.play("h1-h3")  # h-rook moves
        chess.play("d7-d5")
        chess.play("h3-h1")  # Rook returns
        chess.play("b8-c6")
        chess.play("g1-f3")
        chess.play("f8-c5")
        chess.play("e2-e4")
        chess.play("g8-f6")
        chess.play("f1-c4")
        chess.play("a7-a6")
        assert chess.play("O-O") is False

    @pytest.mark.special
    def test_can_still_castle_other_side(self, chess):
        """Can still castle on side where rook hasn't moved."""
        chess.setFen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w Qq - 0 1")
        # Only queenside castling rights remain
        assert chess.play("O-O") is False
        assert chess.play("O-O-O") is True


class TestPawnPromotion:
    """Tests for pawn promotion."""

    @pytest.mark.special
    def test_promote_to_queen(self, promotion_ready_white):
        """Pawn promotes to queen."""
        chess = promotion_ready_white
        assert chess.play("a7-a8=Q") is True
        assert_piece_at(chess, "a8", "Q")

    @pytest.mark.special
    def test_promote_to_rook(self, promotion_ready_white):
        """Pawn promotes to rook."""
        chess = promotion_ready_white
        assert chess.play("a7-a8=R") is True
        assert_piece_at(chess, "a8", "R")

    @pytest.mark.special
    def test_promote_to_bishop(self, promotion_ready_white):
        """Pawn promotes to bishop."""
        chess = promotion_ready_white
        assert chess.play("a7-a8=B") is True
        assert_piece_at(chess, "a8", "B")

    @pytest.mark.special
    def test_promote_to_knight(self, promotion_ready_white):
        """Pawn promotes to knight."""
        chess = promotion_ready_white
        assert chess.play("a7-a8=N") is True
        assert_piece_at(chess, "a8", "N")

    @pytest.mark.special
    def test_black_promotion(self, promotion_ready_black):
        """Black pawn promotes."""
        chess = promotion_ready_black
        assert chess.play("a2-a1=Q") is True
        assert_piece_at(chess, "a1", "q")

    @pytest.mark.special
    def test_promotion_with_capture(self, chess):
        """Pawn promotes while capturing."""
        chess.setFen("1r6/P7/8/8/8/8/8/4K2k w - - 0 1")
        assert chess.play("a7-b8=Q") is True
        assert_piece_at(chess, "b8", "Q")

    @pytest.mark.special
    def test_must_specify_promotion(self, promotion_ready_white):
        """Must specify promotion piece."""
        chess = promotion_ready_white
        assert chess.play("a7-a8") is False

    @pytest.mark.special
    def test_promotion_in_legal_moves(self, promotion_ready_white):
        """All promotion options in getLegalMoves."""
        chess = promotion_ready_white
        moves = chess.getLegalMoves("a7")
        assert "a7-a8=Q" in moves
        assert "a7-a8=R" in moves
        assert "a7-a8=B" in moves
        assert "a7-a8=N" in moves


class TestEnPassant:
    """Tests for en passant capture."""

    @pytest.mark.special
    def test_en_passant_white(self, chess):
        """White can capture en passant."""
        chess.play("e2-e4")
        chess.play("a7-a6")
        chess.play("e4-e5")
        chess.play("d7-d5")  # Black pawn moves two squares

        # Verify en passant is available
        moves = chess.getLegalMoves("e5")
        assert "e5-d6" in moves

        # Execute en passant
        assert chess.play("e5-d6") is True
        assert_piece_at(chess, "d6", "P")
        assert_piece_at(chess, "d5", " ")  # Captured pawn removed

    @pytest.mark.special
    def test_en_passant_black(self, chess):
        """Black can capture en passant."""
        chess.play("a2-a3")
        chess.play("e7-e5")
        chess.play("a3-a4")
        chess.play("e5-e4")
        chess.play("d2-d4")  # White pawn moves two squares

        # Execute en passant
        assert chess.play("e4-d3") is True
        assert_piece_at(chess, "d3", "p")
        assert_piece_at(chess, "d4", " ")

    @pytest.mark.special
    def test_en_passant_expires(self, chess):
        """En passant opportunity expires after one turn."""
        chess.play("e2-e4")
        chess.play("a7-a6")
        chess.play("e4-e5")
        chess.play("d7-d5")  # En passant available
        chess.play("a2-a3")  # White makes different move
        chess.play("a6-a5")  # Black moves

        # En passant no longer available
        moves = chess.getLegalMoves("e5")
        assert "e5-d6" not in moves

    @pytest.mark.special
    def test_en_passant_from_fixture(self, en_passant_ready_white):
        """En passant works with fixture position."""
        chess = en_passant_ready_white
        assert chess.play("b5-a6") is True
        assert_piece_at(chess, "a6", "P")
        assert_piece_at(chess, "a5", " ")

    @pytest.mark.special
    def test_en_passant_only_immediately_after(self, chess):
        """En passant only works immediately after double push."""
        chess.play("e2-e4")
        chess.play("d7-d5")  # d5 pawn pushed
        chess.play("e4-e5")
        chess.play("f7-f5")  # Now f5 is the en passant target, not d5

        # e5 can capture f6 en passant, but not d6
        moves = chess.getLegalMoves("e5")
        assert "e5-f6" in moves
        assert "e5-d6" not in moves


class TestSpecialMovesCombinations:
    """Tests for combinations of special moves."""

    @pytest.mark.special
    def test_promotion_gives_check(self, chess):
        """Promotion can give check."""
        chess.setFen("4k3/P7/8/8/8/8/8/4K3 w - - 0 1")
        chess.play("a7-a8=Q")
        assert chess.isCheck() is True

    @pytest.mark.special
    def test_promotion_gives_checkmate(self, chess):
        """Promotion can give checkmate."""
        # Use a back-rank mate style position
        # Black king on h8, white pawn on g7, white king far away
        # After g7-g8=Q: Queen on g8 gives checkmate (back rank)
        chess.setFen("6rk/6P1/8/8/8/8/8/4K3 w - - 0 1")
        chess.play("g7-g8=Q")  # Captures rook and gives check
        # Now queen on g8, king on h8 - but king can escape to h7
        # Let's use a better position
        chess.reset()
        chess.setFen("5r1k/6P1/6K1/8/8/8/8/8 w - - 0 1")
        chess.play("g7-f8=Q")  # Capture rook, queen on f8
        # King on h8, Queen on f8, King on g6
        # h8: controlled by Qf8, g8: controlled by Kg6, h7: controlled by Kg6
        assert chess.isCheckmate() is True

    @pytest.mark.special
    def test_underpromotion_avoids_stalemate(self, chess):
        """Underpromotion can be used to avoid stalemate."""
        # Position where promoting to queen would be stalemate but knight gives check
        chess.setFen("8/P1k5/2K5/8/8/8/8/8 w - - 0 1")
        # a7-a8=N gives discovered check
        chess.play("a7-a8=N")
        assert chess.isStalemate() is False
