"""
Test: Movimientos Basicos de Piezas
Prueba todos los tipos de movimientos basicos para cada pieza.
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


def test_pawn_moves():
    """Prueba movimientos de peones."""
    print_header("TEST: Movimientos de Peones")
    all_passed = True

    # Test 1: Movimiento simple de peon
    chess = Chess()
    result = chess.play("e2-e3")
    passed = (
        result == True and chess.getPiece("e3") == "P" and chess.getPiece("e2") == " "
    )
    print_test(
        "Peon avanza una casilla (e2-e3)",
        passed,
        f"Resultado: {result}, e3={chess.getPiece('e3')}",
    )
    all_passed = all_passed and passed

    # Test 2: Movimiento doble desde posicion inicial
    chess = Chess()
    result = chess.play("e2-e4")
    passed = result == True and chess.getPiece("e4") == "P"
    print_test(
        "Peon avanza dos casillas desde inicio (e2-e4)",
        passed,
        f"Resultado: {result}, e4={chess.getPiece('e4')}",
    )
    all_passed = all_passed and passed

    # Test 3: Peon negro movimiento simple
    chess = Chess()
    chess.play("e2-e4")  # Blancas
    result = chess.play("e7-e5")  # Negras
    passed = result == True and chess.getPiece("e5") == "p"
    print_test(
        "Peon negro avanza dos casillas (e7-e5)",
        passed,
        f"Resultado: {result}, e5={chess.getPiece('e5')}",
    )
    all_passed = all_passed and passed

    # Test 4: Captura diagonal
    chess = Chess()
    chess.play("e2-e4")
    chess.play("d7-d5")
    result = chess.play("e4-d5")  # Captura
    passed = (
        result == True and chess.getPiece("d5") == "P" and chess.getPiece("e4") == " "
    )
    print_test(
        "Peon captura en diagonal (e4xd5)",
        passed,
        f"Resultado: {result}, d5={chess.getPiece('d5')}",
    )
    all_passed = all_passed and passed

    # Test 5: Movimiento ilegal - peon no puede retroceder
    chess = Chess()
    chess.play("e2-e4")
    chess.play("e7-e5")
    result = chess.play("e4-e3")  # Intento de retroceder
    passed = result == False
    print_test(
        "Peon no puede retroceder (e4-e3 debe fallar)", passed, f"Resultado: {result}"
    )
    all_passed = all_passed and passed

    # Test 6: Movimiento ilegal - peon no puede moverse en diagonal sin capturar
    chess = Chess()
    result = chess.play("e2-d3")
    passed = result == False
    print_test(
        "Peon no puede moverse diagonal sin captura", passed, f"Resultado: {result}"
    )
    all_passed = all_passed and passed

    return all_passed


def test_knight_moves():
    """Prueba movimientos del caballo."""
    print_header("TEST: Movimientos del Caballo")
    all_passed = True

    # Test 1: Movimiento en L
    chess = Chess()
    result = chess.play("g1-f3")
    passed = result == True and chess.getPiece("f3") == "N"
    print_test(
        "Caballo mueve en L (g1-f3)",
        passed,
        f"Resultado: {result}, f3={chess.getPiece('f3')}",
    )
    all_passed = all_passed and passed

    # Test 2: Caballo salta sobre piezas
    chess = Chess()
    result = chess.play("b1-c3")
    passed = result == True and chess.getPiece("c3") == "N"
    print_test(
        "Caballo salta sobre peones (b1-c3)",
        passed,
        f"Resultado: {result}, c3={chess.getPiece('c3')}",
    )
    all_passed = all_passed and passed

    # Test 3: Caballo negro
    chess = Chess()
    chess.play("e2-e4")
    result = chess.play("b8-c6")
    passed = result == True and chess.getPiece("c6") == "n"
    print_test(
        "Caballo negro mueve (b8-c6)",
        passed,
        f"Resultado: {result}, c6={chess.getPiece('c6')}",
    )
    all_passed = all_passed and passed

    # Test 4: Movimiento ilegal de caballo
    chess = Chess()
    result = chess.play("g1-g3")  # No es movimiento en L
    passed = result == False
    print_test(
        "Caballo no puede moverse recto (g1-g3 debe fallar)",
        passed,
        f"Resultado: {result}",
    )
    all_passed = all_passed and passed

    return all_passed


def test_bishop_moves():
    """Prueba movimientos del alfil."""
    print_header("TEST: Movimientos del Alfil")
    all_passed = True

    # Test 1: Alfil mueve en diagonal
    chess = Chess()
    chess.play("e2-e4")  # Abrir camino
    chess.play("e7-e5")
    result = chess.play("f1-c4")
    passed = result == True and chess.getPiece("c4") == "B"
    print_test(
        "Alfil mueve en diagonal (f1-c4)",
        passed,
        f"Resultado: {result}, c4={chess.getPiece('c4')}",
    )
    all_passed = all_passed and passed

    # Test 2: Alfil no puede saltar piezas
    chess = Chess()
    result = chess.play("f1-c4")  # Bloqueado por peones
    passed = result == False
    print_test(
        "Alfil bloqueado por peones (f1-c4 debe fallar)", passed, f"Resultado: {result}"
    )
    all_passed = all_passed and passed

    # Test 3: Alfil captura
    chess = Chess()
    chess.play("e2-e4")
    chess.play("d7-d5")
    chess.play("f1-b5")  # Alfil a b5
    chess.play("c7-c6")
    result = chess.play("b5-c6")  # Captura peon
    passed = result == True and chess.getPiece("c6") == "B"
    print_test(
        "Alfil captura peon (b5xc6)",
        passed,
        f"Resultado: {result}, c6={chess.getPiece('c6')}",
    )
    all_passed = all_passed and passed

    return all_passed


def test_rook_moves():
    """Prueba movimientos de la torre."""
    print_header("TEST: Movimientos de la Torre")
    all_passed = True

    # Test 1: Torre mueve en linea recta (despues de abrir camino)
    chess = Chess()
    chess.play("a2-a4")
    chess.play("e7-e5")
    result = chess.play("a1-a3")
    passed = result == True and chess.getPiece("a3") == "R"
    print_test(
        "Torre mueve vertical (a1-a3)",
        passed,
        f"Resultado: {result}, a3={chess.getPiece('a3')}",
    )
    all_passed = all_passed and passed

    # Test 2: Torre mueve horizontal
    chess = Chess()
    chess.play("a2-a4")
    chess.play("e7-e5")
    chess.play("a1-a3")
    chess.play("d7-d5")
    result = chess.play("a3-h3")
    passed = result == True and chess.getPiece("h3") == "R"
    print_test(
        "Torre mueve horizontal (a3-h3)",
        passed,
        f"Resultado: {result}, h3={chess.getPiece('h3')}",
    )
    all_passed = all_passed and passed

    # Test 3: Torre no puede saltar piezas
    chess = Chess()
    result = chess.play("a1-a5")  # Bloqueada por peon
    passed = result == False
    print_test(
        "Torre bloqueada por peon (a1-a5 debe fallar)", passed, f"Resultado: {result}"
    )
    all_passed = all_passed and passed

    return all_passed


def test_queen_moves():
    """Prueba movimientos de la reina."""
    print_header("TEST: Movimientos de la Reina")
    all_passed = True

    # Test 1: Reina mueve en diagonal
    chess = Chess()
    chess.play("e2-e4")
    chess.play("e7-e5")
    result = chess.play("d1-h5")
    passed = result == True and chess.getPiece("h5") == "Q"
    print_test(
        "Reina mueve diagonal (d1-h5)",
        passed,
        f"Resultado: {result}, h5={chess.getPiece('h5')}",
    )
    all_passed = all_passed and passed

    # Test 2: Reina mueve recto
    chess = Chess()
    chess.play("d2-d4")
    chess.play("e7-e5")
    result = chess.play("d1-d3")
    passed = result == True and chess.getPiece("d3") == "Q"
    print_test(
        "Reina mueve recto (d1-d3)",
        passed,
        f"Resultado: {result}, d3={chess.getPiece('d3')}",
    )
    all_passed = all_passed and passed

    # Test 3: Reina captura
    chess = Chess()
    chess.play("e2-e4")
    chess.play("f7-f5")
    result = chess.play("d1-h5")  # Jaque con captura potencial
    passed = result == True and chess.getPiece("h5") == "Q"
    print_test(
        "Reina a h5 (amenazando)",
        passed,
        f"Resultado: {result}, h5={chess.getPiece('h5')}",
    )
    all_passed = all_passed and passed

    return all_passed


def test_king_moves():
    """Prueba movimientos del rey."""
    print_header("TEST: Movimientos del Rey")
    all_passed = True

    # Test 1: Rey mueve una casilla
    chess = Chess()
    chess.play("e2-e4")
    chess.play("e7-e5")
    result = chess.play("e1-e2")
    passed = result == True and chess.getPiece("e2") == "K"
    print_test(
        "Rey mueve una casilla (e1-e2)",
        passed,
        f"Resultado: {result}, e2={chess.getPiece('e2')}",
    )
    all_passed = all_passed and passed

    # Test 2: Rey no puede moverse dos casillas (excepto enroque)
    chess = Chess()
    chess.play("e2-e4")
    chess.play("e7-e5")
    result = chess.play("e1-e3")
    passed = result == False
    print_test(
        "Rey no puede moverse dos casillas (e1-e3 debe fallar)",
        passed,
        f"Resultado: {result}",
    )
    all_passed = all_passed and passed

    # Test 3: Rey no puede moverse a casilla atacada
    chess = Chess()
    # Configurar posicion donde rey no puede ir a casilla atacada
    chess.setFen("4k3/8/8/8/8/5r2/8/4K3 w - - 0 1")
    result = chess.play("e1-f1")  # f1 atacada por torre en f3
    passed = result == False
    print_test("Rey no puede ir a casilla atacada", passed, f"Resultado: {result}")
    all_passed = all_passed and passed

    return all_passed


def test_turn_validation():
    """Prueba validacion de turnos."""
    print_header("TEST: Validacion de Turnos")
    all_passed = True

    # Test 1: No se puede mover pieza del oponente
    chess = Chess()
    result = chess.play("e7-e5")  # Intentar mover negras primero
    passed = result == False
    print_test(
        "No se puede mover negras en turno de blancas", passed, f"Resultado: {result}"
    )
    all_passed = all_passed and passed

    # Test 2: Turno cambia despues de movimiento
    chess = Chess()
    chess.play("e2-e4")
    turn = chess.getTurn()
    passed = turn == "b"
    print_test(
        "Turno cambia a negras despues de mover blancas", passed, f"Turno: {turn}"
    )
    all_passed = all_passed and passed

    # Test 3: Turno vuelve a blancas
    chess = Chess()
    chess.play("e2-e4")
    chess.play("e7-e5")
    turn = chess.getTurn()
    passed = turn == "w"
    print_test("Turno vuelve a blancas", passed, f"Turno: {turn}")
    all_passed = all_passed and passed

    return all_passed


def test_get_legal_moves():
    """Prueba getLegalMoves."""
    print_header("TEST: getLegalMoves")
    all_passed = True

    # Test 1: Movimientos legales de peon en posicion inicial
    chess = Chess()
    moves = chess.getLegalMoves("e2")
    passed = "e2-e3" in moves and "e2-e4" in moves and len(moves) == 2
    print_test("Peon e2 tiene 2 movimientos (e3, e4)", passed, f"Movimientos: {moves}")
    all_passed = all_passed and passed

    # Test 2: Caballo en g1
    chess = Chess()
    moves = chess.getLegalMoves("g1")
    passed = "g1-f3" in moves and "g1-h3" in moves and len(moves) == 2
    print_test(
        "Caballo g1 tiene 2 movimientos (f3, h3)", passed, f"Movimientos: {moves}"
    )
    all_passed = all_passed and passed

    # Test 3: Casilla vacia no tiene movimientos
    chess = Chess()
    moves = chess.getLegalMoves("e4")
    passed = moves == []
    print_test("Casilla vacia no tiene movimientos", passed, f"Movimientos: {moves}")
    all_passed = all_passed and passed

    # Test 4: No retorna movimientos de piezas del oponente
    chess = Chess()
    moves = chess.getLegalMoves("e7")  # Peon negro, turno de blancas
    passed = moves == []
    print_test(
        "No retorna movimientos de pieza enemiga", passed, f"Movimientos: {moves}"
    )
    all_passed = all_passed and passed

    return all_passed


def test_get_piece():
    """Prueba getPiece."""
    print_header("TEST: getPiece")
    all_passed = True

    chess = Chess()

    # Test piezas blancas
    passed = chess.getPiece("e1") == "K"
    print_test("Rey blanco en e1", passed, f"Pieza: {chess.getPiece('e1')}")
    all_passed = all_passed and passed

    passed = chess.getPiece("d1") == "Q"
    print_test("Reina blanca en d1", passed, f"Pieza: {chess.getPiece('d1')}")
    all_passed = all_passed and passed

    passed = chess.getPiece("a1") == "R"
    print_test("Torre blanca en a1", passed, f"Pieza: {chess.getPiece('a1')}")
    all_passed = all_passed and passed

    passed = chess.getPiece("b1") == "N"
    print_test("Caballo blanco en b1", passed, f"Pieza: {chess.getPiece('b1')}")
    all_passed = all_passed and passed

    passed = chess.getPiece("c1") == "B"
    print_test("Alfil blanco en c1", passed, f"Pieza: {chess.getPiece('c1')}")
    all_passed = all_passed and passed

    passed = chess.getPiece("e2") == "P"
    print_test("Peon blanco en e2", passed, f"Pieza: {chess.getPiece('e2')}")
    all_passed = all_passed and passed

    # Test piezas negras
    passed = chess.getPiece("e8") == "k"
    print_test("Rey negro en e8", passed, f"Pieza: {chess.getPiece('e8')}")
    all_passed = all_passed and passed

    passed = chess.getPiece("e7") == "p"
    print_test("Peon negro en e7", passed, f"Pieza: {chess.getPiece('e7')}")
    all_passed = all_passed and passed

    # Test casilla vacia
    passed = chess.getPiece("e4") == " "
    print_test("Casilla vacia e4", passed, f"Pieza: '{chess.getPiece('e4')}'")
    all_passed = all_passed and passed

    return all_passed


def run_all_tests():
    """Ejecuta todas las pruebas basicas."""
    print("\n" + "#" * 60)
    print("#  PRUEBAS DE MOVIMIENTOS BASICOS")
    print("#" * 60)

    results = []

    results.append(("Movimientos de Peones", test_pawn_moves()))
    results.append(("Movimientos del Caballo", test_knight_moves()))
    results.append(("Movimientos del Alfil", test_bishop_moves()))
    results.append(("Movimientos de la Torre", test_rook_moves()))
    results.append(("Movimientos de la Reina", test_queen_moves()))
    results.append(("Movimientos del Rey", test_king_moves()))
    results.append(("Validacion de Turnos", test_turn_validation()))
    results.append(("getLegalMoves", test_get_legal_moves()))
    results.append(("getPiece", test_get_piece()))

    print("\n" + "=" * 60)
    print("  RESUMEN DE PRUEBAS BASICAS")
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
