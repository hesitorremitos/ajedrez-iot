"""Tests for FEN functionality of Chess module (v2.0)."""


def test_fen_initial_position(chess):
    expected = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    assert chess.getFen() == expected


def test_fen_after_move_has_turn_and_ep(chess):
    chess.play("e2-e4")
    parts = chess.getFen().split()
    assert parts[1] == "b"
    assert parts[3] == "e3"


def test_get_halfmove_clock(chess):
    assert chess.getHalfmoveClock() == 0
    chess.play("g1-f3")
    assert chess.getHalfmoveClock() == 1
    chess.play("g8-f6")
    assert chess.getHalfmoveClock() == 2


def test_get_last_position_state_normal_after_non_check_move(chess):
    chess.play("e2-e4")
    assert chess.getLastPositionState() == "normal"


def test_set_fen_loads_position(chess):
    test_fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
    chess.setFen(test_fen)
    assert chess.getPiece("c4") == "B"
    assert chess.getPiece("f3") == "N"
    assert chess.getPiece("c6") == "n"
    assert chess.getTurn() == "w"


def test_fen_roundtrip(chess):
    original = "r3k2r/ppp2ppp/2n1b3/3qp3/3P4/2N2N2/PPP2PPP/R1BQK2R b KQkq - 0 8"
    chess.setFen(original)
    assert chess.getFen() == original


def test_reset(chess):
    chess.play("e2-e4")
    chess.play("e7-e5")
    chess.play("g1-f3")

    chess.reset()
    expected = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    assert chess.getFen() == expected
    assert chess.getTurn() == "w"


def test_board_str_contains_coordinates(chess):
    board_str = str(chess)
    assert "a   b   c   d   e   f   g   h" in board_str
    assert "8 |" in board_str
    assert "1 |" in board_str
    assert "Turn:" in board_str or "White" in board_str


def test_get_board_returns_64_chars(chess):
    """getBoard() returns a list of 64 characters."""
    board = chess.getBoard()
    assert len(board) == 64


def test_get_board_initial_position(chess):
    """getBoard() initial position has correct pieces."""
    board = chess.getBoard()
    # a1 = R, e1 = K, a8 = r, e8 = k
    assert board[0] == "R"  # a1
    assert board[4] == "K"  # e1
    assert board[56] == "r"  # a8
    assert board[60] == "k"  # e8
    # e2 = P, e4 = empty
    assert board[12] == "P"  # e2
    assert board[28] == " "  # e4


def test_get_board_after_move(chess):
    """getBoard() reflects move changes."""
    chess.play("e2-e4")
    board = chess.getBoard()
    assert board[12] == " "  # e2 now empty
    assert board[28] == "P"  # e4 has pawn


def test_on_move_callback(chess):
    """onMove callback fires with correct arguments."""
    calls = []

    def handler(moveStr, captured, isPromotion, isCastling, isEnPassant):
        calls.append(
            {
                "move": moveStr,
                "captured": captured,
                "isPromotion": isPromotion,
                "isCastling": isCastling,
                "isEnPassant": isEnPassant,
            }
        )

    chess.onMove = handler
    chess.play("e2-e4")

    assert len(calls) == 1
    assert calls[0]["move"] == "e2-e4"
    assert calls[0]["captured"] is None
    assert calls[0]["isPromotion"] is False
    assert calls[0]["isCastling"] is False
    assert calls[0]["isEnPassant"] is False


def test_on_move_callback_capture(chess):
    """onMove callback reports captured piece."""
    calls = []

    def handler(moveStr, captured, isPromotion, isCastling, isEnPassant):
        calls.append({"captured": captured})

    chess.onMove = handler
    chess.play("e2-e4")
    chess.play("d7-d5")
    chess.play("e4-d5")

    assert len(calls) == 3
    assert calls[2]["captured"] == "p"


def test_on_move_callback_castling(chess):
    """onMove callback reports castling."""
    calls = []

    def handler(moveStr, captured, isPromotion, isCastling, isEnPassant):
        calls.append({"move": moveStr, "isCastling": isCastling})

    chess.onMove = handler
    chess.setFen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1")
    chess.play("O-O")

    assert calls[-1]["move"] == "O-O"
    assert calls[-1]["isCastling"] is True


def test_on_move_callback_en_passant(chess):
    """onMove callback reports en passant capture."""
    calls = []

    def handler(moveStr, captured, isPromotion, isCastling, isEnPassant):
        calls.append({"captured": captured, "isEnPassant": isEnPassant})

    chess.onMove = handler
    chess.play("e2-e4")
    chess.play("a7-a6")
    chess.play("e4-e5")
    chess.play("d7-d5")
    chess.play("e5-d6")

    assert calls[-1]["isEnPassant"] is True
    assert calls[-1]["captured"] == "p"


def test_on_move_callback_promotion(chess):
    """onMove callback reports promotion."""
    calls = []

    def handler(moveStr, captured, isPromotion, isCastling, isEnPassant):
        calls.append({"isPromotion": isPromotion})

    chess.onMove = handler
    chess.setFen("8/P7/8/8/8/8/8/4K2k w - - 0 1")
    chess.play("a7-a8=Q")

    assert calls[-1]["isPromotion"] is True
