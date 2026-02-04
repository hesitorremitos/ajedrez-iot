def test_stalemate_basic(chess):
    chess.setFen("k7/8/1Q6/8/8/8/8/4K3 b - - 0 1")
    assert chess.isStalemate() is True
    assert chess.isCheck() is False
    assert chess.isGameOver() is True
    assert chess.isCheckmate() is False


def test_stalemate_king_only(chess):
    chess.setFen("8/8/8/8/8/1k6/2q5/K7 w - - 0 1")
    assert chess.isStalemate() is True


def test_insufficient_material_k_vs_k(chess):
    chess.setFen("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
    assert chess.isDraw() is True
    assert chess.isGameOver() is True


def test_insufficient_material_k_vs_kb(chess):
    chess.setFen("4k3/8/8/8/8/8/8/4KB2 w - - 0 1")
    assert chess.isDraw() is True


def test_insufficient_material_k_vs_kn(chess):
    chess.setFen("4k3/8/8/8/8/8/8/4KN2 w - - 0 1")
    assert chess.isDraw() is True


def test_insufficient_material_kb_vs_kb_same_color(chess):
    chess.setFen("4k3/8/5b2/8/8/8/3B4/4K3 w - - 0 1")
    assert chess.isDraw() is True


def test_not_insufficient_material_kb_vs_kb_different_color(chess):
    chess.setFen("4k3/8/4b3/8/8/8/3B4/4K3 w - - 0 1")
    assert chess.isDraw() is False


def test_not_insufficient_material_with_pawn(chess):
    chess.setFen("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1")
    assert chess.isDraw() is False


def test_not_insufficient_material_with_rook(chess):
    chess.setFen("4k3/8/8/8/8/8/8/4KR2 w - - 0 1")
    assert chess.isDraw() is False


def test_fifty_move_rule(chess):
    chess.setFen("4k3/8/8/8/8/8/8/4KR2 w - - 99 50")
    chess.play("f1-f2")
    assert chess.isDraw() is True
    assert chess.isGameOver() is True


def test_fifty_move_resets_on_capture(chess):
    chess.setFen("4k3/8/8/8/8/5n2/8/4KR2 w - - 90 50")
    chess.play("f1-f3")
    halfmove = int(chess.getFen().split()[4])
    assert halfmove == 0


def test_fifty_move_resets_on_pawn_move(chess):
    chess.setFen("4k3/8/8/8/8/8/4P3/4K3 w - - 90 50")
    chess.play("e2-e4")
    halfmove = int(chess.getFen().split()[4])
    assert halfmove == 0


def test_stalemate_callback():
    from modules.chess import Chess

    stalemate_called = {"value": False}
    gameover_called = {"value": False}

    def on_stalemate():
        stalemate_called["value"] = True

    def on_gameover():
        gameover_called["value"] = True

    chess = Chess()
    chess.onStalemate = on_stalemate
    chess.onGameOver = on_gameover
    chess.setFen("k7/8/2Q5/8/8/8/8/4K3 w - - 0 1")
    chess.play("c6-b6")

    assert stalemate_called["value"] is True
    assert gameover_called["value"] is True


def test_draw_callback():
    from modules.chess import Chess

    draw_called = {"value": False}
    gameover_called = {"value": False}

    def on_draw():
        draw_called["value"] = True

    def on_gameover():
        gameover_called["value"] = True

    chess = Chess()
    chess.onDraw = on_draw
    chess.onGameOver = on_gameover
    chess.setFen("4k3/8/8/8/8/8/8/4KR2 w - - 99 50")
    chess.play("f1-f2")

    assert draw_called["value"] is True
    assert gameover_called["value"] is True
