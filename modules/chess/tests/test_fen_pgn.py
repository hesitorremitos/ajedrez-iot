"""
Tests for FEN and PGN functionality.
"""

import pytest
from Chess import Chess


class TestFEN:
    """Tests for FEN import/export functionality."""

    @pytest.mark.fen
    def test_fen_initial_position(self, chess):
        """Test FEN of initial position."""
        fen = chess.getFen()
        expected = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        assert fen == expected

    @pytest.mark.fen
    def test_fen_after_e4(self, chess):
        """Test FEN after 1.e4 - turn and en passant."""
        chess.play("e2-e4")
        fen = chess.getFen()
        parts = fen.split()

        assert parts[1] == "b"  # Black to move
        assert parts[3] == "e3"  # En passant square

    @pytest.mark.fen
    def test_set_fen_position(self, chess):
        """Test loading position from FEN."""
        test_fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
        chess.setFen(test_fen)

        assert chess.getPiece("c4") == "B"
        assert chess.getPiece("f3") == "N"
        assert chess.getPiece("c6") == "n"
        assert chess.getTurn() == "w"

    @pytest.mark.fen
    def test_fen_roundtrip(self, chess):
        """Test FEN is preserved after import/export."""
        original_fen = "r3k2r/ppp2ppp/2n1b3/3qp3/3P4/2N2N2/PPP2PPP/R1BQK2R b KQkq - 0 8"
        chess.setFen(original_fen)
        exported_fen = chess.getFen()
        assert exported_fen == original_fen

    @pytest.mark.fen
    def test_fen_castling_rights(self, castling_ready_white):
        """Test FEN preserves castling rights."""
        fen = castling_ready_white.getFen()
        parts = fen.split()
        assert "K" in parts[2]  # White kingside
        assert "Q" in parts[2]  # White queenside
        assert "k" in parts[2]  # Black kingside
        assert "q" in parts[2]  # Black queenside

    @pytest.mark.fen
    def test_fen_after_castling_removes_rights(self, castling_ready_white):
        """Test FEN removes castling rights after castling."""
        castling_ready_white.play("O-O")
        fen = castling_ready_white.getFen()
        parts = fen.split()
        # White shouldn't have kingside/queenside rights anymore
        assert "K" not in parts[2]
        assert "Q" not in parts[2]


class TestPGN:
    """Tests for PGN export functionality."""

    @pytest.mark.pgn
    def test_pgn_basic(self, chess):
        """Test basic PGN generation."""
        chess.play("e2-e4")
        chess.play("e7-e5")
        chess.play("g1-f3")
        chess.play("b8-c6")

        pgn = chess.getPgn()

        assert "1. e2-e4 e7-e5" in pgn
        assert "2. g1-f3 b8-c6" in pgn
        assert "[Event" in pgn

    @pytest.mark.pgn
    def test_pgn_with_custom_headers(self, chess):
        """Test PGN with custom headers."""
        chess.play("e2-e4")
        chess.play("e7-e5")

        headers = {"Event": "Test Game", "White": "Player1", "Black": "Player2"}
        pgn = chess.getPgn(headers)

        assert '[Event "Test Game"]' in pgn
        assert '[White "Player1"]' in pgn

    @pytest.mark.pgn
    def test_pgn_checkmate_result(self, chess):
        """Test PGN shows checkmate result 1-0."""
        # Scholar's mate
        chess.play("e2-e4")
        chess.play("e7-e5")
        chess.play("f1-c4")
        chess.play("b8-c6")
        chess.play("d1-h5")
        chess.play("g8-f6")
        chess.play("h5-f7")

        pgn = chess.getPgn()
        assert "1-0" in pgn  # White wins

    @pytest.mark.pgn
    def test_pgn_empty_game(self, chess):
        """Test PGN for game with no moves."""
        pgn = chess.getPgn()
        assert "[Event" in pgn
        assert "*" in pgn  # Ongoing/unknown result

    @pytest.mark.pgn
    def test_pgn_stalemate_result(self, chess):
        """Test PGN shows draw result for stalemate."""
        # Set up and cause stalemate
        chess.setFen("k7/8/2Q5/8/8/8/8/4K3 w - - 0 1")
        chess.play("c6-b6")  # Causes stalemate

        pgn = chess.getPgn()
        assert "1/2-1/2" in pgn  # Draw
