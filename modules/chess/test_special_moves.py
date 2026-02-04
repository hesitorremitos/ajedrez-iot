"""
Test: Movimientos Especiales
Prueba enroque, promocion y captura al paso (en passant).
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


def test_castling_kingside_white():
    """Prueba enroque corto de blancas."""
    print_header("TEST: Enroque Corto Blancas (O-O)")
    all_passed = True

    # Preparar posicion para enroque
    chess = Chess()
    chess.play("e2-e4")
    chess.play("e7-e5")
    chess.play("g1-f3")
    chess.play("b8-c6")
    chess.play("f1-c4")
    chess.play("g8-f6")

    # Ahora puede enrocar
    result = chess.play("O-O")
    passed = result == True
    print_test("Enroque corto ejecutado", passed, f"Resultado: {result}")
    all_passed = all_passed and passed

    # Verificar posiciones
    passed = chess.getPiece("g1") == "K"
    print_test("Rey en g1", passed, f"g1={chess.getPiece('g1')}")
    all_passed = all_passed and passed

    passed = chess.getPiece("f1") == "R"
    print_test("Torre en f1", passed, f"f1={chess.getPiece('f1')}")
    all_passed = all_passed and passed

    passed = chess.getPiece("e1") == " "
    print_test("e1 vacia", passed, f"e1='{chess.getPiece('e1')}'")
    all_passed = all_passed and passed

    passed = chess.getPiece("h1") == " "
    print_test("h1 vacia", passed, f"h1='{chess.getPiece('h1')}'")
    all_passed = all_passed and passed

    return all_passed


def test_castling_queenside_white():
    """Prueba enroque largo de blancas."""
    print_header("TEST: Enroque Largo Blancas (O-O-O)")
    all_passed = True

    # Preparar posicion para enroque largo
    chess = Chess()
    chess.play("d2-d4")
    chess.play("d7-d5")
    chess.play("b1-c3")
    chess.play("b8-c6")
    chess.play("c1-f4")
    chess.play("c8-f5")
    chess.play("d1-d3")
    chess.play("d8-d6")

    # Ahora puede enrocar largo
    result = chess.play("O-O-O")
    passed = result == True
    print_test("Enroque largo ejecutado", passed, f"Resultado: {result}")
    all_passed = all_passed and passed

    # Verificar posiciones
    passed = chess.getPiece("c1") == "K"
    print_test("Rey en c1", passed, f"c1={chess.getPiece('c1')}")
    all_passed = all_passed and passed

    passed = chess.getPiece("d1") == "R"
    print_test("Torre en d1", passed, f"d1={chess.getPiece('d1')}")
    all_passed = all_passed and passed

    return all_passed


def test_castling_kingside_black():
    """Prueba enroque corto de negras."""
    print_header("TEST: Enroque Corto Negras (O-O)")
    all_passed = True

    # Preparar posicion
    chess = Chess()
    chess.play("e2-e4")
    chess.play("e7-e5")
    chess.play("g1-f3")
    chess.play("g8-f6")
    chess.play("f1-c4")
    chess.play("f8-c5")
    chess.play("d2-d3")

    # Negras enrocan
    result = chess.play("O-O")
    passed = result == True
    print_test("Enroque corto negras ejecutado", passed, f"Resultado: {result}")
    all_passed = all_passed and passed

    passed = chess.getPiece("g8") == "k"
    print_test("Rey negro en g8", passed, f"g8={chess.getPiece('g8')}")
    all_passed = all_passed and passed

    passed = chess.getPiece("f8") == "r"
    print_test("Torre negra en f8", passed, f"f8={chess.getPiece('f8')}")
    all_passed = all_passed and passed

    return all_passed


def test_castling_not_allowed_in_check():
    """Prueba que no se puede enrocar estando en jaque."""
    print_header("TEST: No Enroque en Jaque")
    all_passed = True

    # Posicion con rey blanco en jaque por alfil en b4 (diagonal libre a e1)
    # Removemos el peon de d2 para que el alfil pueda dar jaque
    chess = Chess()
    chess.setFen("r3k2r/pppppppp/8/8/1b6/8/PPP2PPP/R3K2R w KQkq - 0 1")

    result = chess.play("O-O")
    passed = result == False
    print_test("No puede enrocar estando en jaque", passed, f"Resultado: {result}")
    all_passed = all_passed and passed

    return all_passed


def test_castling_not_allowed_through_check():
    """Prueba que no se puede enrocar atravesando casilla atacada."""
    print_header("TEST: No Enroque Atravesando Jaque")
    all_passed = True

    # Posicion donde f1 esta atacada por alfil en c4 (diagonal a6-f1)
    chess = Chess()
    chess.setFen("r3k2r/pppppppp/8/8/2b5/8/PPPP1PPP/R3K2R w KQkq - 0 1")

    result = chess.play("O-O")
    passed = result == False
    print_test("No puede enrocar (f1 atacada)", passed, f"Resultado: {result}")
    all_passed = all_passed and passed

    return all_passed


def test_castling_rights_lost_after_king_move():
    """Prueba que se pierden derechos de enroque al mover el rey."""
    print_header("TEST: Perder Derechos Enroque (Mover Rey)")
    all_passed = True

    chess = Chess()
    chess.play("e2-e4")
    chess.play("e7-e5")
    chess.play("e1-e2")  # Rey mueve
    chess.play("g8-f6")
    chess.play("e2-e1")  # Rey vuelve
    chess.play("b8-c6")
    chess.play("g1-f3")
    chess.play("f8-c5")
    chess.play("f1-c4")
    chess.play("d7-d6")

    # Intentar enrocar (deberia fallar)
    result = chess.play("O-O")
    passed = result == False
    print_test("No puede enrocar (rey ya movio)", passed, f"Resultado: {result}")
    all_passed = all_passed and passed

    return all_passed


def test_castling_rights_lost_after_rook_move():
    """Prueba que se pierden derechos de enroque al mover la torre."""
    print_header("TEST: Perder Derechos Enroque (Mover Torre)")
    all_passed = True

    chess = Chess()
    chess.play("h2-h4")
    chess.play("e7-e5")
    chess.play("h1-h3")  # Torre h1 mueve
    chess.play("d7-d5")
    chess.play("h3-h1")  # Torre vuelve
    chess.play("b8-c6")
    chess.play("g1-f3")
    chess.play("f8-c5")
    chess.play("e2-e4")
    chess.play("g8-f6")
    chess.play("f1-c4")
    chess.play("a7-a6")

    # Intentar enroque corto (deberia fallar)
    result = chess.play("O-O")
    passed = result == False
    print_test(
        "No puede enrocar corto (torre h1 ya movio)", passed, f"Resultado: {result}"
    )
    all_passed = all_passed and passed

    return all_passed


def test_pawn_promotion():
    """Prueba promocion de peon."""
    print_header("TEST: Promocion de Peon")
    all_passed = True

    # Posicion con peon a punto de promover
    chess = Chess()
    chess.setFen("8/P7/8/8/8/8/8/4K2k w - - 0 1")

    # Promocion a reina
    result = chess.play("a7-a8=Q")
    passed = result == True and chess.getPiece("a8") == "Q"
    print_test(
        "Peon promueve a Reina (a7-a8=Q)",
        passed,
        f"Resultado: {result}, a8={chess.getPiece('a8')}",
    )
    all_passed = all_passed and passed

    # Promocion a torre
    chess.setFen("8/1P6/8/8/8/8/8/4K2k w - - 0 1")
    result = chess.play("b7-b8=R")
    passed = result == True and chess.getPiece("b8") == "R"
    print_test(
        "Peon promueve a Torre (b7-b8=R)",
        passed,
        f"Resultado: {result}, b8={chess.getPiece('b8')}",
    )
    all_passed = all_passed and passed

    # Promocion a alfil
    chess.setFen("8/2P5/8/8/8/8/8/4K2k w - - 0 1")
    result = chess.play("c7-c8=B")
    passed = result == True and chess.getPiece("c8") == "B"
    print_test(
        "Peon promueve a Alfil (c7-c8=B)",
        passed,
        f"Resultado: {result}, c8={chess.getPiece('c8')}",
    )
    all_passed = all_passed and passed

    # Promocion a caballo
    chess.setFen("8/3P4/8/8/8/8/8/4K2k w - - 0 1")
    result = chess.play("d7-d8=N")
    passed = result == True and chess.getPiece("d8") == "N"
    print_test(
        "Peon promueve a Caballo (d7-d8=N)",
        passed,
        f"Resultado: {result}, d8={chess.getPiece('d8')}",
    )
    all_passed = all_passed and passed

    return all_passed


def test_pawn_promotion_black():
    """Prueba promocion de peon negro."""
    print_header("TEST: Promocion Peon Negro")
    all_passed = True

    chess = Chess()
    chess.setFen("4K2k/8/8/8/8/8/p7/8 b - - 0 1")

    result = chess.play("a2-a1=Q")
    passed = result == True and chess.getPiece("a1") == "q"
    print_test(
        "Peon negro promueve a reina (a2-a1=Q)",
        passed,
        f"Resultado: {result}, a1={chess.getPiece('a1')}",
    )
    all_passed = all_passed and passed

    return all_passed


def test_promotion_with_capture():
    """Prueba promocion capturando pieza."""
    print_header("TEST: Promocion con Captura")
    all_passed = True

    chess = Chess()
    chess.setFen("1r6/P7/8/8/8/8/8/4K2k w - - 0 1")

    result = chess.play("a7-b8=Q")
    passed = result == True and chess.getPiece("b8") == "Q"
    print_test(
        "Peon captura y promueve (a7xb8=Q)",
        passed,
        f"Resultado: {result}, b8={chess.getPiece('b8')}",
    )
    all_passed = all_passed and passed

    return all_passed


def test_promotion_required():
    """Prueba que la promocion es requerida al llegar a ultima fila."""
    print_header("TEST: Promocion Requerida")
    all_passed = True

    chess = Chess()
    chess.setFen("8/P7/8/8/8/8/8/4K2k w - - 0 1")

    # Sin especificar promocion deberia fallar
    result = chess.play("a7-a8")
    passed = result == False
    print_test("Movimiento sin promocion debe fallar", passed, f"Resultado: {result}")
    all_passed = all_passed and passed

    return all_passed


def test_en_passant():
    """Prueba captura al paso (en passant)."""
    print_header("TEST: En Passant")
    all_passed = True

    # Blancas capturan al paso
    chess = Chess()
    chess.play("e2-e4")
    chess.play("a7-a6")
    chess.play("e4-e5")
    chess.play("d7-d5")  # Peon negro avanza dos casillas

    # Verificar que en passant es posible
    moves = chess.getLegalMoves("e5")
    passed = "e5-d6" in moves
    print_test(
        "En passant disponible en movimientos legales", passed, f"Movimientos: {moves}"
    )
    all_passed = all_passed and passed

    # Ejecutar en passant
    result = chess.play("e5-d6")
    passed = result == True
    print_test("Captura en passant ejecutada", passed, f"Resultado: {result}")
    all_passed = all_passed and passed

    # Verificar que el peon negro fue capturado
    passed = chess.getPiece("d5") == " "
    print_test("Peon negro en d5 capturado", passed, f"d5='{chess.getPiece('d5')}'")
    all_passed = all_passed and passed

    passed = chess.getPiece("d6") == "P"
    print_test("Peon blanco en d6", passed, f"d6={chess.getPiece('d6')}")
    all_passed = all_passed and passed

    return all_passed


def test_en_passant_black():
    """Prueba en passant por negras."""
    print_header("TEST: En Passant Negras")
    all_passed = True

    chess = Chess()
    chess.play("a2-a3")
    chess.play("e7-e5")
    chess.play("a3-a4")
    chess.play("e5-e4")
    chess.play("d2-d4")  # Blancas avanzan dos casillas

    # Negras capturan al paso
    result = chess.play("e4-d3")
    passed = result == True
    print_test("En passant por negras ejecutado", passed, f"Resultado: {result}")
    all_passed = all_passed and passed

    passed = chess.getPiece("d4") == " "
    print_test("Peon blanco en d4 capturado", passed, f"d4='{chess.getPiece('d4')}'")
    all_passed = all_passed and passed

    passed = chess.getPiece("d3") == "p"
    print_test("Peon negro en d3", passed, f"d3={chess.getPiece('d3')}")
    all_passed = all_passed and passed

    return all_passed


def test_en_passant_expires():
    """Prueba que en passant expira despues de un turno."""
    print_header("TEST: En Passant Expira")
    all_passed = True

    chess = Chess()
    chess.play("e2-e4")
    chess.play("a7-a6")
    chess.play("e4-e5")
    chess.play("d7-d5")  # En passant disponible
    chess.play("a2-a3")  # Blancas hacen otro movimiento
    chess.play("a6-a5")  # Negras mueven

    # Ahora en passant ya no deberia estar disponible
    moves = chess.getLegalMoves("e5")
    passed = "e5-d6" not in moves
    print_test("En passant ya no disponible", passed, f"Movimientos de e5: {moves}")
    all_passed = all_passed and passed

    return all_passed


def test_legal_moves_with_promotion():
    """Prueba que getLegalMoves incluye opciones de promocion."""
    print_header("TEST: getLegalMoves con Promocion")
    all_passed = True

    chess = Chess()
    chess.setFen("8/P7/8/8/8/8/8/4K2k w - - 0 1")

    moves = chess.getLegalMoves("a7")
    # Debe incluir todas las opciones de promocion
    passed = (
        "a7-a8=Q" in moves
        and "a7-a8=R" in moves
        and "a7-a8=B" in moves
        and "a7-a8=N" in moves
    )
    print_test(
        "getLegalMoves incluye todas las promociones", passed, f"Movimientos: {moves}"
    )
    all_passed = all_passed and passed

    return all_passed


def test_legal_moves_includes_castling():
    """Prueba que getLegalMoves incluye enroque cuando es posible."""
    print_header("TEST: getLegalMoves con Enroque")
    all_passed = True

    # Posicion lista para enrocar
    chess = Chess()
    chess.setFen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1")

    moves = chess.getLegalMoves("e1")
    passed = "O-O" in moves and "O-O-O" in moves
    print_test(
        "getLegalMoves incluye ambos enroques", passed, f"Movimientos del rey: {moves}"
    )
    all_passed = all_passed and passed

    return all_passed


def run_all_tests():
    """Ejecuta todas las pruebas de movimientos especiales."""
    print("\n" + "#" * 60)
    print("#  PRUEBAS DE MOVIMIENTOS ESPECIALES")
    print("#" * 60)

    results = []

    results.append(("Enroque Corto Blancas", test_castling_kingside_white()))
    results.append(("Enroque Largo Blancas", test_castling_queenside_white()))
    results.append(("Enroque Corto Negras", test_castling_kingside_black()))
    results.append(("No Enroque en Jaque", test_castling_not_allowed_in_check()))
    results.append(
        ("No Enroque Atravesando Jaque", test_castling_not_allowed_through_check())
    )
    results.append(
        ("Perder Derechos (Mover Rey)", test_castling_rights_lost_after_king_move())
    )
    results.append(
        ("Perder Derechos (Mover Torre)", test_castling_rights_lost_after_rook_move())
    )
    results.append(("Promocion de Peon", test_pawn_promotion()))
    results.append(("Promocion Peon Negro", test_pawn_promotion_black()))
    results.append(("Promocion con Captura", test_promotion_with_capture()))
    results.append(("Promocion Requerida", test_promotion_required()))
    results.append(("En Passant", test_en_passant()))
    results.append(("En Passant Negras", test_en_passant_black()))
    results.append(("En Passant Expira", test_en_passant_expires()))
    results.append(("getLegalMoves con Promocion", test_legal_moves_with_promotion()))
    results.append(("getLegalMoves con Enroque", test_legal_moves_includes_castling()))

    print("\n" + "=" * 60)
    print("  RESUMEN DE PRUEBAS DE MOVIMIENTOS ESPECIALES")
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
