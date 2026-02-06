def test_check_detection_initial(chess):
    assert chess.isCheck() is False


def test_check_detection_scholars_mate(chess):
    moves = ["e2-e4", "e7-e5", "d1-h5", "b8-c6", "f1-c4", "g8-f6", "h5-f7"]
    for move in moves:
        chess.play(move)

    assert chess.isCheck() is True
    assert chess.isCheckmate() is True


def test_check_by_rook(chess):
    chess.setFen("4k3/8/8/8/8/8/4R3/4K3 w - - 0 1")
    chess.play("e2-e7")
    assert chess.isCheck() is True


def test_check_by_knight(chess):
    chess.setFen("4k3/8/8/3N4/8/8/8/4K3 w - - 0 1")
    chess.play("d5-f6")
    assert chess.isCheck() is True


def test_check_by_bishop(chess):
    chess.setFen("4k3/8/8/7B/8/8/8/4K3 b - - 0 1")
    assert chess.isCheck() is True


def test_check_by_pawn(chess):
    chess.setFen("4k3/3P4/8/8/8/8/8/4K3 b - - 0 1")
    assert chess.isCheck() is True


def test_cannot_move_into_check(chess):
    chess.setFen("4k3/8/8/8/8/4r3/8/4K3 w - - 0 1")
    assert chess.play("e1-e2") is False


def test_can_move_to_safe_square(chess):
    chess.setFen("4k3/8/8/8/8/4r3/8/4K3 w - - 0 1")
    assert chess.play("e1-f1") is True


def test_must_escape_check(chess):
    chess.setFen("4k3/8/8/8/4R3/8/8/4K3 b - - 0 1")
    assert chess.isCheck() is True

    moves = chess.getLegalMoves("e8")
    assert "e8-e7" not in moves
    assert len(moves) > 0


def test_pinned_piece_cannot_move(chess):
    chess.setFen("4k3/4b3/8/8/8/8/8/4RK2 b - - 0 1")
    moves = chess.getLegalMoves("e7")
    assert moves == []


def test_checkmate_scholars_mate(chess):
    moves = ["e2-e4", "e7-e5", "f1-c4", "b8-c6", "d1-h5", "g8-f6", "h5-f7"]
    for move in moves:
        chess.play(move)

    assert chess.isCheckmate() is True
    assert chess.getLastPositionState() == "checkmate"


def test_checkmate_back_rank(chess):
    chess.setFen("6k1/5ppp/8/8/8/8/8/R3K3 w - - 0 1")
    assert chess.play("a1-a8") is True
    assert chess.isCheckmate() is True


def test_checkmate_two_rooks(chess):
    chess.setFen("k7/RR6/8/8/8/8/8/4K3 b - - 0 1")
    assert chess.isCheckmate() is True


def test_checkmate_queen_and_king(chess):
    chess.setFen("k7/8/1K6/8/8/8/8/Q7 w - - 0 1")
    assert chess.play("a1-a7") is True
    assert chess.isCheckmate() is True


def test_check_callback():
    from modules.chess import Chess

    check_called = {"value": False}

    def on_check_handler():
        check_called["value"] = True

    chess = Chess()
    chess.onCheck = on_check_handler
    chess.setFen("4k3/8/8/8/8/8/4R3/4K3 w - - 0 1")
    chess.play("e2-e7")

    assert check_called["value"] is True
    assert chess.getLastPositionState() == "check"


def test_checkmate_callback():
    from modules.chess import Chess

    checkmate_called = {"value": False}

    def on_checkmate_handler():
        checkmate_called["value"] = True

    chess = Chess()
    chess.onCheckmate = on_checkmate_handler

    moves = ["e2-e4", "e7-e5", "f1-c4", "b8-c6", "d1-h5", "g8-f6", "h5-f7"]
    for move in moves:
        chess.play(move)

    assert checkmate_called["value"] is True
