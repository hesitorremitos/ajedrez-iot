def test_castling_kingside_white(chess):
    chess.play("e2-e4")
    chess.play("e7-e5")
    chess.play("g1-f3")
    chess.play("b8-c6")
    chess.play("f1-c4")
    chess.play("g8-f6")

    assert chess.play("O-O") is True
    assert chess.getPiece("g1") == "K"
    assert chess.getPiece("f1") == "R"
    assert chess.getPiece("e1") == " "
    assert chess.getPiece("h1") == " "


def test_castling_queenside_white(chess):
    chess.play("d2-d4")
    chess.play("d7-d5")
    chess.play("b1-c3")
    chess.play("b8-c6")
    chess.play("c1-f4")
    chess.play("c8-f5")
    chess.play("d1-d3")
    chess.play("d8-d6")

    assert chess.play("O-O-O") is True
    assert chess.getPiece("c1") == "K"
    assert chess.getPiece("d1") == "R"


def test_castling_kingside_black(chess):
    chess.play("e2-e4")
    chess.play("e7-e5")
    chess.play("g1-f3")
    chess.play("g8-f6")
    chess.play("f1-c4")
    chess.play("f8-c5")
    chess.play("d2-d3")

    assert chess.play("O-O") is True
    assert chess.getPiece("g8") == "k"
    assert chess.getPiece("f8") == "r"


def test_castling_not_allowed_in_check(chess):
    chess.setFen("r3k2r/pppppppp/8/8/1b6/8/PPP2PPP/R3K2R w KQkq - 0 1")
    assert chess.play("O-O") is False


def test_castling_not_allowed_through_check(chess):
    chess.setFen("r3k2r/pppppppp/8/8/2b5/8/PPPP1PPP/R3K2R w KQkq - 0 1")
    assert chess.play("O-O") is False


def test_castling_rights_lost_after_king_move(chess):
    chess.play("e2-e4")
    chess.play("e7-e5")
    chess.play("e1-e2")
    chess.play("g8-f6")
    chess.play("e2-e1")
    chess.play("b8-c6")
    chess.play("g1-f3")
    chess.play("f8-c5")
    chess.play("f1-c4")
    chess.play("d7-d6")

    assert chess.play("O-O") is False


def test_castling_rights_lost_after_rook_move(chess):
    chess.play("h2-h4")
    chess.play("e7-e5")
    chess.play("h1-h3")
    chess.play("d7-d5")
    chess.play("h3-h1")
    chess.play("b8-c6")
    chess.play("g1-f3")
    chess.play("f8-c5")
    chess.play("e2-e4")
    chess.play("g8-f6")
    chess.play("f1-c4")
    chess.play("a7-a6")

    assert chess.play("O-O") is False


def test_pawn_promotion(chess):
    chess.setFen("8/P7/8/8/8/8/8/4K2k w - - 0 1")
    assert chess.play("a7-a8=Q") is True
    assert chess.getPiece("a8") == "Q"

    chess.setFen("8/1P6/8/8/8/8/8/4K2k w - - 0 1")
    assert chess.play("b7-b8=R") is True
    assert chess.getPiece("b8") == "R"

    chess.setFen("8/2P5/8/8/8/8/8/4K2k w - - 0 1")
    assert chess.play("c7-c8=B") is True
    assert chess.getPiece("c8") == "B"

    chess.setFen("8/3P4/8/8/8/8/8/4K2k w - - 0 1")
    assert chess.play("d7-d8=N") is True
    assert chess.getPiece("d8") == "N"


def test_pawn_promotion_black(chess):
    chess.setFen("4K2k/8/8/8/8/8/p7/8 b - - 0 1")
    assert chess.play("a2-a1=Q") is True
    assert chess.getPiece("a1") == "q"


def test_promotion_with_capture(chess):
    chess.setFen("1r6/P7/8/8/8/8/8/4K2k w - - 0 1")
    assert chess.play("a7-b8=Q") is True
    assert chess.getPiece("b8") == "Q"


def test_promotion_required(chess):
    chess.setFen("8/P7/8/8/8/8/8/4K2k w - - 0 1")
    assert chess.play("a7-a8") is False


def test_en_passant_white(chess):
    chess.play("e2-e4")
    chess.play("a7-a6")
    chess.play("e4-e5")
    chess.play("d7-d5")

    moves = chess.getLegalMoves("e5")
    assert "e5-d6" in moves

    assert chess.play("e5-d6") is True
    assert chess.getPiece("d5") == " "
    assert chess.getPiece("d6") == "P"


def test_en_passant_black(chess):
    chess.play("a2-a3")
    chess.play("e7-e5")
    chess.play("a3-a4")
    chess.play("e5-e4")
    chess.play("d2-d4")

    assert chess.play("e4-d3") is True
    assert chess.getPiece("d4") == " "
    assert chess.getPiece("d3") == "p"


def test_en_passant_expires(chess):
    chess.play("e2-e4")
    chess.play("a7-a6")
    chess.play("e4-e5")
    chess.play("d7-d5")
    chess.play("a2-a3")
    chess.play("a6-a5")

    moves = chess.getLegalMoves("e5")
    assert "e5-d6" not in moves


def test_legal_moves_with_promotion(chess):
    chess.setFen("8/P7/8/8/8/8/8/4K2k w - - 0 1")
    moves = chess.getLegalMoves("a7")
    assert "a7-a8=Q" in moves
    assert "a7-a8=R" in moves
    assert "a7-a8=B" in moves
    assert "a7-a8=N" in moves


def test_legal_moves_includes_castling(chess):
    chess.setFen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1")
    moves = chess.getLegalMoves("e1")
    assert "O-O" in moves
    assert "O-O-O" in moves
