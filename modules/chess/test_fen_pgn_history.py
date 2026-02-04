"""
Test: FEN, PGN, Historial y Undo
Prueba funcionalidades de exportacion/importacion y gestion de historial.
"""

import sys

sys.path.insert(0, ".")

from Chess import Chess


def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_test(name, passed, details=""):
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {name}")
    if details:
        print(f"         {details}")


def test_fen_initial_position():
    """Prueba FEN de posicion inicial."""
    print_header("TEST: FEN Posicion Inicial")
    all_passed = True

    chess = Chess()
    fen = chess.getFen()
    expected = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    passed = fen == expected
    print_test("FEN inicial correcto", passed, f"Obtenido: {fen}")
    all_passed = all_passed and passed

    return all_passed


def test_fen_after_moves():
    """Prueba FEN despues de movimientos."""
    print_header("TEST: FEN Despues de Movimientos")
    all_passed = True

    chess = Chess()
    chess.play("e2-e4")
    fen = chess.getFen()

    # Verificar partes del FEN
    parts = fen.split()

    # Turno debe ser negras
    passed = parts[1] == "b"
    print_test("Turno cambia a negras en FEN", passed, f"Turno: {parts[1]}")
    all_passed = all_passed and passed

    # En passant square debe ser e3
    passed = parts[3] == "e3"
    print_test("En passant square es e3", passed, f"EP: {parts[3]}")
    all_passed = all_passed and passed

    return all_passed


def test_set_fen():
    """Prueba cargar posicion desde FEN."""
    print_header("TEST: Cargar FEN")
    all_passed = True

    chess = Chess()
    test_fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
    chess.setFen(test_fen)

    # Verificar piezas
    passed = chess.getPiece("c4") == "B"
    print_test("Alfil en c4", passed, f"c4={chess.getPiece('c4')}")
    all_passed = all_passed and passed

    passed = chess.getPiece("f3") == "N"
    print_test("Caballo en f3", passed, f"f3={chess.getPiece('f3')}")
    all_passed = all_passed and passed

    passed = chess.getPiece("c6") == "n"
    print_test("Caballo negro en c6", passed, f"c6={chess.getPiece('c6')}")
    all_passed = all_passed and passed

    passed = chess.getTurn() == "w"
    print_test("Turno blancas", passed, f"Turno: {chess.getTurn()}")
    all_passed = all_passed and passed

    return all_passed


def test_fen_roundtrip():
    """Prueba que FEN se mantiene al exportar/importar."""
    print_header("TEST: FEN Roundtrip")
    all_passed = True

    original_fen = "r3k2r/ppp2ppp/2n1b3/3qp3/3P4/2N2N2/PPP2PPP/R1BQK2R b KQkq - 0 8"
    chess = Chess()
    chess.setFen(original_fen)
    exported_fen = chess.getFen()

    passed = exported_fen == original_fen
    print_test(
        "FEN se mantiene tras import/export",
        passed,
        f"Original: {original_fen}\nExportado: {exported_fen}",
    )
    all_passed = all_passed and passed

    return all_passed


def test_pgn_basic():
    """Prueba generacion basica de PGN."""
    print_header("TEST: PGN Basico")
    all_passed = True

    chess = Chess()
    chess.play("e2-e4")
    chess.play("e7-e5")
    chess.play("g1-f3")
    chess.play("b8-c6")

    pgn = chess.getPgn()

    # Debe contener los movimientos
    passed = "1. e2-e4 e7-e5" in pgn
    print_test("PGN contiene primer turno", passed)
    all_passed = all_passed and passed

    passed = "2. g1-f3 b8-c6" in pgn
    print_test("PGN contiene segundo turno", passed)
    all_passed = all_passed and passed

    # Debe tener headers
    passed = "[Event" in pgn
    print_test("PGN tiene header Event", passed)
    all_passed = all_passed and passed

    return all_passed


def test_pgn_with_headers():
    """Prueba PGN con headers personalizados."""
    print_header("TEST: PGN con Headers")
    all_passed = True

    chess = Chess()
    chess.play("e2-e4")
    chess.play("e7-e5")

    headers = {"Event": "Test Game", "White": "Player1", "Black": "Player2"}
    pgn = chess.getPgn(headers)

    passed = '[Event "Test Game"]' in pgn
    print_test("PGN tiene Event personalizado", passed)
    all_passed = all_passed and passed

    passed = '[White "Player1"]' in pgn
    print_test("PGN tiene White personalizado", passed)
    all_passed = all_passed and passed

    return all_passed


def test_pgn_checkmate_result():
    """Prueba que PGN muestra resultado de mate."""
    print_header("TEST: PGN Resultado Mate")
    all_passed = True

    chess = Chess()
    # Mate del pastor
    chess.play("e2-e4")
    chess.play("e7-e5")
    chess.play("f1-c4")
    chess.play("b8-c6")
    chess.play("d1-h5")
    chess.play("g8-f6")
    chess.play("h5-f7")

    pgn = chess.getPgn()

    passed = "1-0" in pgn  # Blancas ganan
    print_test("PGN muestra resultado 1-0", passed, f"PGN: {pgn[-50:]}")
    all_passed = all_passed and passed

    return all_passed


def test_history_basic():
    """Prueba historial basico."""
    print_header("TEST: Historial Basico")
    all_passed = True

    chess = Chess()
    chess.play("e2-e4")
    chess.play("e7-e5")
    chess.play("g1-f3")
    chess.play("b8-c6")

    history = chess.getHistory()

    passed = len(history) == 2
    print_test(
        "Historial tiene 2 turnos completos", passed, f"Longitud: {len(history)}"
    )
    all_passed = all_passed and passed

    passed = history[0] == ("e2-e4", "e7-e5")
    print_test("Primer turno correcto", passed, f"Turno 1: {history[0]}")
    all_passed = all_passed and passed

    passed = history[1] == ("g1-f3", "b8-c6")
    print_test("Segundo turno correcto", passed, f"Turno 2: {history[1]}")
    all_passed = all_passed and passed

    return all_passed


def test_history_incomplete_turn():
    """Prueba historial con turno incompleto."""
    print_header("TEST: Historial Turno Incompleto")
    all_passed = True

    chess = Chess()
    chess.play("e2-e4")
    chess.play("e7-e5")
    chess.play("g1-f3")  # Blancas mueven, negras no

    history = chess.getHistory()

    # Debe haber 2 entradas: turno 1 completo y turno 2 incompleto
    passed = len(history) == 2
    print_test("Historial tiene 2 entradas", passed, f"Longitud: {len(history)}")
    all_passed = all_passed and passed

    passed = history[1] == ("g1-f3", "")
    print_test("Turno incompleto tiene string vacio", passed, f"Turno 2: {history[1]}")
    all_passed = all_passed and passed

    return all_passed


def test_undo_single_move():
    """Prueba undo de un movimiento."""
    print_header("TEST: Undo Movimiento Simple")
    all_passed = True

    chess = Chess()
    chess.play("e2-e4")

    result = chess.undo()

    passed = result == True
    print_test("Undo retorna True", passed, f"Resultado: {result}")
    all_passed = all_passed and passed

    passed = chess.getPiece("e4") == " "
    print_test("e4 vacia despues de undo", passed, f"e4='{chess.getPiece('e4')}'")
    all_passed = all_passed and passed

    passed = chess.getPiece("e2") == "P"
    print_test("Peon vuelve a e2", passed, f"e2={chess.getPiece('e2')}")
    all_passed = all_passed and passed

    passed = chess.getTurn() == "w"
    print_test("Turno vuelve a blancas", passed, f"Turno: {chess.getTurn()}")
    all_passed = all_passed and passed

    return all_passed


def test_undo_multiple_moves():
    """Prueba undo de multiples movimientos."""
    print_header("TEST: Undo Multiple")
    all_passed = True

    chess = Chess()
    chess.play("e2-e4")
    chess.play("e7-e5")
    chess.play("g1-f3")

    # Undo g1-f3
    chess.undo()
    passed = chess.getPiece("f3") == " " and chess.getPiece("g1") == "N"
    print_test("Undo 1: caballo vuelve a g1", passed)
    all_passed = all_passed and passed

    # Undo e7-e5
    chess.undo()
    passed = chess.getPiece("e5") == " " and chess.getPiece("e7") == "p"
    print_test("Undo 2: peon negro vuelve a e7", passed)
    all_passed = all_passed and passed

    # Undo e2-e4
    chess.undo()
    passed = chess.getPiece("e4") == " " and chess.getPiece("e2") == "P"
    print_test("Undo 3: peon blanco vuelve a e2", passed)
    all_passed = all_passed and passed

    # Verificar posicion inicial
    fen = chess.getFen()
    expected = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    passed = fen == expected
    print_test("Posicion vuelve a inicial", passed)
    all_passed = all_passed and passed

    return all_passed


def test_undo_no_moves():
    """Prueba undo cuando no hay movimientos."""
    print_header("TEST: Undo Sin Movimientos")
    all_passed = True

    chess = Chess()
    result = chess.undo()

    passed = result == False
    print_test("Undo retorna False sin movimientos", passed, f"Resultado: {result}")
    all_passed = all_passed and passed

    return all_passed


def test_undo_capture():
    """Prueba undo de captura."""
    print_header("TEST: Undo Captura")
    all_passed = True

    chess = Chess()
    chess.play("e2-e4")
    chess.play("d7-d5")
    chess.play("e4-d5")  # Captura

    chess.undo()

    passed = chess.getPiece("e4") == "P"
    print_test("Peon blanco vuelve a e4", passed, f"e4={chess.getPiece('e4')}")
    all_passed = all_passed and passed

    passed = chess.getPiece("d5") == "p"
    print_test("Peon negro restaurado en d5", passed, f"d5={chess.getPiece('d5')}")
    all_passed = all_passed and passed

    return all_passed


def test_undo_castling():
    """Prueba undo de enroque."""
    print_header("TEST: Undo Enroque")
    all_passed = True

    chess = Chess()
    chess.setFen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1")
    chess.play("O-O")  # Enroque corto

    chess.undo()

    passed = chess.getPiece("e1") == "K"
    print_test("Rey vuelve a e1", passed, f"e1={chess.getPiece('e1')}")
    all_passed = all_passed and passed

    passed = chess.getPiece("h1") == "R"
    print_test("Torre vuelve a h1", passed, f"h1={chess.getPiece('h1')}")
    all_passed = all_passed and passed

    passed = chess.getPiece("g1") == " "
    print_test("g1 vacia", passed, f"g1='{chess.getPiece('g1')}'")
    all_passed = all_passed and passed

    passed = chess.getPiece("f1") == " "
    print_test("f1 vacia", passed, f"f1='{chess.getPiece('f1')}'")
    all_passed = all_passed and passed

    return all_passed


def test_undo_en_passant():
    """Prueba undo de en passant."""
    print_header("TEST: Undo En Passant")
    all_passed = True

    chess = Chess()
    chess.play("e2-e4")
    chess.play("a7-a6")
    chess.play("e4-e5")
    chess.play("d7-d5")
    chess.play("e5-d6")  # En passant

    chess.undo()

    passed = chess.getPiece("e5") == "P"
    print_test("Peon blanco vuelve a e5", passed, f"e5={chess.getPiece('e5')}")
    all_passed = all_passed and passed

    passed = chess.getPiece("d5") == "p"
    print_test("Peon negro restaurado en d5", passed, f"d5={chess.getPiece('d5')}")
    all_passed = all_passed and passed

    passed = chess.getPiece("d6") == " "
    print_test("d6 vacia", passed, f"d6='{chess.getPiece('d6')}'")
    all_passed = all_passed and passed

    return all_passed


def test_undo_promotion():
    """Prueba undo de promocion."""
    print_header("TEST: Undo Promocion")
    all_passed = True

    chess = Chess()
    chess.setFen("8/P7/8/8/8/8/8/4K2k w - - 0 1")
    chess.play("a7-a8=Q")

    chess.undo()

    passed = chess.getPiece("a7") == "P"
    print_test("Peon vuelve a a7", passed, f"a7={chess.getPiece('a7')}")
    all_passed = all_passed and passed

    passed = chess.getPiece("a8") == " "
    print_test("a8 vacia", passed, f"a8='{chess.getPiece('a8')}'")
    all_passed = all_passed and passed

    return all_passed


def test_reset():
    """Prueba reset de partida."""
    print_header("TEST: Reset Partida")
    all_passed = True

    chess = Chess()
    chess.play("e2-e4")
    chess.play("e7-e5")
    chess.play("g1-f3")

    chess.reset()

    fen = chess.getFen()
    expected = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    passed = fen == expected
    print_test("FEN vuelve a inicial", passed)
    all_passed = all_passed and passed

    history = chess.getHistory()
    passed = len(history) == 0
    print_test("Historial vacio", passed, f"Longitud: {len(history)}")
    all_passed = all_passed and passed

    passed = chess.getTurn() == "w"
    print_test("Turno es blancas", passed)
    all_passed = all_passed and passed

    return all_passed


def test_board_str():
    """Prueba representacion string del tablero."""
    print_header("TEST: Representacion String")
    all_passed = True

    chess = Chess()
    board_str = str(chess)

    passed = "a   b   c   d   e   f   g   h" in board_str
    print_test("Contiene coordenadas de columnas", passed)
    all_passed = all_passed and passed

    passed = "8 |" in board_str
    print_test("Contiene fila 8", passed)
    all_passed = all_passed and passed

    passed = "1 |" in board_str
    print_test("Contiene fila 1", passed)
    all_passed = all_passed and passed

    passed = "Turn:" in board_str or "White" in board_str
    print_test("Muestra turno", passed)
    all_passed = all_passed and passed

    print("\n  Vista del tablero:")
    for line in str(chess).split("\n")[:5]:
        print(f"    {line}")

    return all_passed


def run_all_tests():
    """Ejecuta todas las pruebas de FEN, PGN, historial y undo."""
    print("\n" + "#" * 60)
    print("#  PRUEBAS DE FEN, PGN, HISTORIAL Y UNDO")
    print("#" * 60)

    results = []

    results.append(("FEN Inicial", test_fen_initial_position()))
    results.append(("FEN Despues Movimientos", test_fen_after_moves()))
    results.append(("Cargar FEN", test_set_fen()))
    results.append(("FEN Roundtrip", test_fen_roundtrip()))
    results.append(("PGN Basico", test_pgn_basic()))
    results.append(("PGN con Headers", test_pgn_with_headers()))
    results.append(("PGN Resultado Mate", test_pgn_checkmate_result()))
    results.append(("Historial Basico", test_history_basic()))
    results.append(("Historial Turno Incompleto", test_history_incomplete_turn()))
    results.append(("Undo Simple", test_undo_single_move()))
    results.append(("Undo Multiple", test_undo_multiple_moves()))
    results.append(("Undo Sin Movimientos", test_undo_no_moves()))
    results.append(("Undo Captura", test_undo_capture()))
    results.append(("Undo Enroque", test_undo_castling()))
    results.append(("Undo En Passant", test_undo_en_passant()))
    results.append(("Undo Promocion", test_undo_promotion()))
    results.append(("Reset Partida", test_reset()))
    results.append(("Representacion String", test_board_str()))

    print("\n" + "=" * 60)
    print("  RESUMEN DE PRUEBAS FEN, PGN, HISTORIAL Y UNDO")
    print("=" * 60)

    total_passed = 0
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        if passed:
            total_passed += 1

    print("=" * 60)
    print(f"  Total: {total_passed}/{len(results)} pruebas pasaron")
    print("=" * 60)

    return total_passed == len(results)


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
