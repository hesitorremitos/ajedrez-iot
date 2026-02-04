def assert_piece_at(chess, square, expected_piece):
    actual = chess.getPiece(square)
    assert actual == expected_piece


def test_pawn_single_push(chess):
    assert chess.play("e2-e3") is True
    assert_piece_at(chess, "e3", "P")
    assert_piece_at(chess, "e2", " ")


def test_pawn_double_push_from_start(chess):
    assert chess.play("e2-e4") is True
    assert_piece_at(chess, "e4", "P")


def test_black_pawn_double_push(chess):
    chess.play("e2-e4")
    assert chess.play("e7-e5") is True
    assert_piece_at(chess, "e5", "p")


def test_pawn_capture_diagonal(chess):
    chess.play("e2-e4")
    chess.play("d7-d5")
    assert chess.play("e4-d5") is True
    assert_piece_at(chess, "d5", "P")
    assert_piece_at(chess, "e4", " ")


def test_pawn_cannot_move_backward(chess):
    chess.play("e2-e4")
    chess.play("e7-e5")
    assert chess.play("e4-e3") is False


def test_pawn_cannot_move_diagonal_without_capture(chess):
    assert chess.play("e2-d3") is False


def test_knight_l_shape_move(chess):
    assert chess.play("g1-f3") is True
    assert_piece_at(chess, "f3", "N")


def test_knight_can_jump_over_pieces(chess):
    assert chess.play("b1-c3") is True
    assert_piece_at(chess, "c3", "N")


def test_black_knight_move(chess):
    chess.play("e2-e4")
    assert chess.play("b8-c6") is True
    assert_piece_at(chess, "c6", "n")


def test_knight_cannot_move_straight(chess):
    assert chess.play("g1-g3") is False


def test_bishop_diagonal_move(chess):
    chess.play("e2-e4")
    chess.play("e7-e5")
    assert chess.play("f1-c4") is True
    assert_piece_at(chess, "c4", "B")


def test_bishop_blocked_by_pawn(chess):
    assert chess.play("f1-c4") is False


def test_bishop_capture(chess):
    chess.play("e2-e4")
    chess.play("d7-d5")
    chess.play("f1-b5")
    chess.play("c7-c6")
    assert chess.play("b5-c6") is True
    assert_piece_at(chess, "c6", "B")


def test_rook_vertical_move(chess):
    chess.play("a2-a4")
    chess.play("e7-e5")
    assert chess.play("a1-a3") is True
    assert_piece_at(chess, "a3", "R")


def test_rook_horizontal_move(chess):
    chess.play("a2-a4")
    chess.play("e7-e5")
    chess.play("a1-a3")
    chess.play("d7-d5")
    assert chess.play("a3-h3") is True
    assert_piece_at(chess, "h3", "R")


def test_rook_blocked_by_pawn(chess):
    assert chess.play("a1-a5") is False


def test_queen_diagonal_move(chess):
    chess.play("e2-e4")
    chess.play("e7-e5")
    assert chess.play("d1-h5") is True
    assert_piece_at(chess, "h5", "Q")


def test_queen_straight_move(chess):
    chess.play("d2-d4")
    chess.play("e7-e5")
    assert chess.play("d1-d3") is True
    assert_piece_at(chess, "d3", "Q")


def test_king_one_square_move(chess):
    chess.play("e2-e4")
    chess.play("e7-e5")
    assert chess.play("e1-e2") is True
    assert_piece_at(chess, "e2", "K")


def test_king_cannot_move_two_squares(chess):
    chess.play("e2-e4")
    chess.play("e7-e5")
    assert chess.play("e1-e3") is False


def test_king_cannot_move_to_attacked_square(chess):
    chess.setFen("4k3/8/8/8/8/4r3/8/4K3 w - - 0 1")
    assert chess.play("e1-e2") is False


def test_turn_validation_cannot_move_opponent_piece(chess):
    assert chess.play("e7-e5") is False


def test_turn_changes_after_move(chess):
    assert chess.getTurn() == "w"
    chess.play("e2-e4")
    assert chess.getTurn() == "b"


def test_turn_alternates(chess):
    chess.play("e2-e4")
    chess.play("e7-e5")
    assert chess.getTurn() == "w"


def test_get_legal_moves_pawn_initial(chess):
    moves = chess.getLegalMoves("e2")
    assert "e2-e3" in moves
    assert "e2-e4" in moves
    assert len(moves) == 2


def test_get_legal_moves_knight_initial(chess):
    moves = chess.getLegalMoves("g1")
    assert "g1-f3" in moves
    assert "g1-h3" in moves
    assert len(moves) == 2


def test_get_legal_moves_empty_square(chess):
    assert chess.getLegalMoves("e4") == []


def test_get_legal_moves_opponent_piece(chess):
    assert chess.getLegalMoves("e7") == []


def test_get_piece_initial_positions(chess):
    assert chess.getPiece("e1") == "K"
    assert chess.getPiece("d1") == "Q"
    assert chess.getPiece("a1") == "R"
    assert chess.getPiece("b1") == "N"
    assert chess.getPiece("c1") == "B"
    assert chess.getPiece("e2") == "P"
    assert chess.getPiece("e8") == "k"
    assert chess.getPiece("e7") == "p"
    assert chess.getPiece("e4") == " "
