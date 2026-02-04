def test_fen_initial_position(chess):
    expected = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    assert chess.getFen() == expected


def test_fen_after_move_has_turn_and_ep(chess):
    chess.play("e2-e4")
    parts = chess.getFen().split()
    assert parts[1] == "b"
    assert parts[3] == "e3"


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


def test_pgn_basic(chess):
    chess.play("e2-e4")
    chess.play("e7-e5")
    chess.play("g1-f3")
    chess.play("b8-c6")

    pgn = chess.getPgn()
    assert "1. e2-e4 e7-e5" in pgn
    assert "2. g1-f3 b8-c6" in pgn
    assert "[Event" in pgn


def test_pgn_with_headers(chess):
    chess.play("e2-e4")
    chess.play("e7-e5")
    headers = {"Event": "Test Game", "White": "Player1", "Black": "Player2"}
    pgn = chess.getPgn(headers)
    assert '[Event "Test Game"]' in pgn
    assert '[White "Player1"]' in pgn


def test_pgn_checkmate_result(chess):
    moves = ["e2-e4", "e7-e5", "f1-c4", "b8-c6", "d1-h5", "g8-f6", "h5-f7"]
    for move in moves:
        chess.play(move)

    assert "1-0" in chess.getPgn()


def test_history_basic(chess):
    chess.play("e2-e4")
    chess.play("e7-e5")
    chess.play("g1-f3")
    chess.play("b8-c6")

    history = chess.getHistory()
    assert len(history) == 2
    assert history[0] == ("e2-e4", "e7-e5")
    assert history[1] == ("g1-f3", "b8-c6")


def test_history_incomplete_turn(chess):
    chess.play("e2-e4")
    chess.play("e7-e5")
    chess.play("g1-f3")

    history = chess.getHistory()
    assert len(history) == 2
    assert history[1] == ("g1-f3", "")


def test_undo_single_move(chess):
    chess.play("e2-e4")
    assert chess.undo() is True
    assert chess.getPiece("e4") == " "
    assert chess.getPiece("e2") == "P"
    assert chess.getTurn() == "w"


def test_undo_multiple_moves(chess):
    chess.play("e2-e4")
    chess.play("e7-e5")
    chess.play("g1-f3")

    chess.undo()
    assert chess.getPiece("f3") == " "
    assert chess.getPiece("g1") == "N"

    chess.undo()
    assert chess.getPiece("e5") == " "
    assert chess.getPiece("e7") == "p"

    chess.undo()
    assert chess.getPiece("e4") == " "
    assert chess.getPiece("e2") == "P"

    expected = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    assert chess.getFen() == expected


def test_undo_no_moves(chess):
    assert chess.undo() is False


def test_undo_capture(chess):
    chess.play("e2-e4")
    chess.play("d7-d5")
    chess.play("e4-d5")

    chess.undo()
    assert chess.getPiece("e4") == "P"
    assert chess.getPiece("d5") == "p"


def test_undo_castling(chess):
    chess.setFen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1")
    chess.play("O-O")

    chess.undo()
    assert chess.getPiece("e1") == "K"
    assert chess.getPiece("h1") == "R"
    assert chess.getPiece("g1") == " "
    assert chess.getPiece("f1") == " "


def test_undo_en_passant(chess):
    chess.play("e2-e4")
    chess.play("a7-a6")
    chess.play("e4-e5")
    chess.play("d7-d5")
    chess.play("e5-d6")

    chess.undo()
    assert chess.getPiece("e5") == "P"
    assert chess.getPiece("d5") == "p"
    assert chess.getPiece("d6") == " "


def test_undo_promotion(chess):
    chess.setFen("8/P7/8/8/8/8/8/4K2k w - - 0 1")
    chess.play("a7-a8=Q")

    chess.undo()
    assert chess.getPiece("a7") == "P"
    assert chess.getPiece("a8") == " "


def test_reset(chess):
    chess.play("e2-e4")
    chess.play("e7-e5")
    chess.play("g1-f3")

    chess.reset()
    expected = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    assert chess.getFen() == expected
    assert chess.getHistory() == []
    assert chess.getTurn() == "w"


def test_board_str_contains_coordinates(chess):
    board_str = str(chess)
    assert "a   b   c   d   e   f   g   h" in board_str
    assert "8 |" in board_str
    assert "1 |" in board_str
    assert "Turn:" in board_str or "White" in board_str
