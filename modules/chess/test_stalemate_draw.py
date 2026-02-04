"""
Test: Tablas y Ahogado (Stalemate/Draw)
Prueba deteccion de ahogado, tablas por material insuficiente y regla de 50 movimientos.
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


def test_stalemate_basic():
    """Prueba ahogado basico."""
    print_header("TEST: Ahogado Basico")
    all_passed = True

    # Posicion de ahogado: rey negro en a8, reina blanca en b6 controla todas las casillas de escape
    # La reina en b6 no da jaque directamente a a8 (no es diagonal ni linea recta)
    # Pero cubre: a7 (diagonal), b7 (adyacente), b8 (columna)
    chess = Chess()
    chess.setFen("k7/8/1Q6/8/8/8/8/4K3 b - - 0 1")

    # El rey negro esta ahogado (no en jaque pero sin movimientos)
    passed = chess.isStalemate() == True
    print_test(
        "isStalemate() retorna True", passed, f"isStalemate: {chess.isStalemate()}"
    )
    all_passed = all_passed and passed

    passed = chess.isCheck() == False
    print_test("No esta en jaque", passed, f"isCheck: {chess.isCheck()}")
    all_passed = all_passed and passed

    passed = chess.isGameOver() == True
    print_test("Partida terminada", passed, f"isGameOver: {chess.isGameOver()}")
    all_passed = all_passed and passed

    passed = chess.isCheckmate() == False
    print_test("No es jaque mate", passed, f"isCheckmate: {chess.isCheckmate()}")
    all_passed = all_passed and passed

    return all_passed


def test_stalemate_king_only():
    """Prueba ahogado con rey solo."""
    print_header("TEST: Ahogado Rey Solo")
    all_passed = True

    # Rey blanco acorralado en esquina
    chess = Chess()
    chess.setFen("8/8/8/8/8/1k6/2q5/K7 w - - 0 1")
    # Rey blanco en a1, reina negra en c2, rey negro en b3
    # Rey blanco no tiene movimientos legales pero no esta en jaque

    passed = chess.isStalemate() == True
    print_test(
        "Rey acorralado esta ahogado", passed, f"isStalemate: {chess.isStalemate()}"
    )
    all_passed = all_passed and passed

    return all_passed


def test_stalemate_with_pawns():
    """Prueba ahogado con peones bloqueados."""
    print_header("TEST: Ahogado con Peones Bloqueados")
    all_passed = True

    # Rey y peones bloqueados
    chess = Chess()
    chess.setFen("8/8/8/6pk/5pP1/5P1K/8/8 b - - 0 1")
    # Rey negro en h5, peon en g5, peon blanco en g4 y f3
    # Rey blanco en h3, peones bloqueados
    # Negro mueve, pero esta ahogado

    # Verificamos si es ahogado
    moves_k = chess.getLegalMoves("h5")
    moves_p = chess.getLegalMoves("g5")
    all_moves = moves_k + moves_p

    if len(all_moves) == 0:
        passed = chess.isStalemate() == True
        print_test(
            "Posicion de ahogado detectada",
            passed,
            f"isStalemate: {chess.isStalemate()}",
        )
    else:
        passed = chess.isStalemate() == False
        print_test(
            "No es ahogado (hay movimientos)",
            passed,
            f"Movimientos disponibles: {all_moves}",
        )
    all_passed = all_passed and passed

    return all_passed


def test_insufficient_material_k_vs_k():
    """Prueba material insuficiente: Rey vs Rey."""
    print_header("TEST: Material Insuficiente K vs K")
    all_passed = True

    chess = Chess()
    chess.setFen("4k3/8/8/8/8/8/8/4K3 w - - 0 1")

    passed = chess.isDraw() == True
    print_test("K vs K es tablas", passed, f"isDraw: {chess.isDraw()}")
    all_passed = all_passed and passed

    passed = chess.isGameOver() == True
    print_test("Partida terminada", passed, f"isGameOver: {chess.isGameOver()}")
    all_passed = all_passed and passed

    return all_passed


def test_insufficient_material_k_vs_kb():
    """Prueba material insuficiente: Rey vs Rey + Alfil."""
    print_header("TEST: Material Insuficiente K vs K+B")
    all_passed = True

    chess = Chess()
    chess.setFen("4k3/8/8/8/8/8/8/4KB2 w - - 0 1")

    passed = chess.isDraw() == True
    print_test("K vs K+B es tablas", passed, f"isDraw: {chess.isDraw()}")
    all_passed = all_passed and passed

    return all_passed


def test_insufficient_material_k_vs_kn():
    """Prueba material insuficiente: Rey vs Rey + Caballo."""
    print_header("TEST: Material Insuficiente K vs K+N")
    all_passed = True

    chess = Chess()
    chess.setFen("4k3/8/8/8/8/8/8/4KN2 w - - 0 1")

    passed = chess.isDraw() == True
    print_test("K vs K+N es tablas", passed, f"isDraw: {chess.isDraw()}")
    all_passed = all_passed and passed

    return all_passed


def test_insufficient_material_kb_vs_kb_same_color():
    """Prueba material insuficiente: K+B vs K+B mismo color."""
    print_header("TEST: Material Insuficiente K+B vs K+B (mismo color)")
    all_passed = True

    # Ambos alfiles en casillas blancas (diagonales del mismo color)
    chess = Chess()
    chess.setFen("4k3/8/5b2/8/8/8/3B4/4K3 w - - 0 1")
    # Alfil blanco en d2 (casilla clara), alfil negro en f6 (casilla clara)
    # d2 = (3,1) -> 3+1=4 (par = casilla blanca)
    # f6 = (5,5) -> 5+5=10 (par = casilla blanca)

    passed = chess.isDraw() == True
    print_test("K+B vs K+B mismo color es tablas", passed, f"isDraw: {chess.isDraw()}")
    all_passed = all_passed and passed

    return all_passed


def test_not_insufficient_material_kb_vs_kb_different_color():
    """Prueba que NO es material insuficiente: K+B vs K+B diferente color."""
    print_header("TEST: NO Material Insuficiente K+B vs K+B (diferente color)")
    all_passed = True

    # Alfiles en casillas de diferente color - se puede hacer mate
    chess = Chess()
    chess.setFen("4k3/8/4b3/8/8/8/3B4/4K3 w - - 0 1")
    # Alfil blanco en d2 (casilla clara: 3+1=4, par)
    # Alfil negro en e6 (casilla oscura: 4+5=9, impar)

    passed = chess.isDraw() == False
    print_test(
        "K+B vs K+B diferente color NO es tablas", passed, f"isDraw: {chess.isDraw()}"
    )
    all_passed = all_passed and passed

    return all_passed


def test_not_insufficient_material_with_pawn():
    """Prueba que NO es material insuficiente si hay peones."""
    print_header("TEST: NO Material Insuficiente con Peones")
    all_passed = True

    chess = Chess()
    chess.setFen("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1")

    passed = chess.isDraw() == False
    print_test(
        "K+P vs K NO es tablas (peon puede promover)",
        passed,
        f"isDraw: {chess.isDraw()}",
    )
    all_passed = all_passed and passed

    return all_passed


def test_not_insufficient_material_with_rook():
    """Prueba que NO es material insuficiente con torre."""
    print_header("TEST: NO Material Insuficiente con Torre")
    all_passed = True

    chess = Chess()
    chess.setFen("4k3/8/8/8/8/8/8/4KR2 w - - 0 1")

    passed = chess.isDraw() == False
    print_test("K+R vs K NO es tablas", passed, f"isDraw: {chess.isDraw()}")
    all_passed = all_passed and passed

    return all_passed


def test_fifty_move_rule():
    """Prueba regla de 50 movimientos."""
    print_header("TEST: Regla de 50 Movimientos")
    all_passed = True

    # Configurar posicion con halfmove clock alto
    chess = Chess()
    chess.setFen("4k3/8/8/8/8/8/8/4KR2 w - - 99 50")
    # halfmove clock = 99, un movimiento mas sin captura/peon = tablas

    chess.play("f1-f2")  # Movimiento de torre (no peon, no captura)

    passed = chess.isDraw() == True
    print_test(
        "Tablas por regla de 50 movimientos", passed, f"isDraw: {chess.isDraw()}"
    )
    all_passed = all_passed and passed

    passed = chess.isGameOver() == True
    print_test("Partida terminada", passed, f"isGameOver: {chess.isGameOver()}")
    all_passed = all_passed and passed

    return all_passed


def test_fifty_move_resets_on_capture():
    """Prueba que el contador se reinicia al capturar."""
    print_header("TEST: 50 Movimientos - Reset al Capturar")
    all_passed = True

    chess = Chess()
    chess.setFen("4k3/8/8/8/8/5n2/8/4KR2 w - - 90 50")

    chess.play("f1-f3")  # Captura el caballo negro
    fen = chess.getFen()
    # El halfmove clock deberia ser 0 despues de captura
    halfmove = int(fen.split()[4])

    passed = halfmove == 0
    print_test(
        "Contador reiniciado a 0 tras captura", passed, f"Halfmove clock: {halfmove}"
    )
    all_passed = all_passed and passed

    return all_passed


def test_fifty_move_resets_on_pawn_move():
    """Prueba que el contador se reinicia al mover peon."""
    print_header("TEST: 50 Movimientos - Reset al Mover Peon")
    all_passed = True

    chess = Chess()
    chess.setFen("4k3/8/8/8/8/8/4P3/4K3 w - - 90 50")

    chess.play("e2-e4")  # Movimiento de peon
    fen = chess.getFen()
    halfmove = int(fen.split()[4])

    passed = halfmove == 0
    print_test(
        "Contador reiniciado a 0 tras mover peon", passed, f"Halfmove clock: {halfmove}"
    )
    all_passed = all_passed and passed

    return all_passed


def test_stalemate_callback():
    """Prueba callback onStalemate."""
    print_header("TEST: Callback onStalemate")
    all_passed = True

    stalemate_called = [False]
    gameover_called = [False]

    def on_stalemate():
        stalemate_called[0] = True

    def on_gameover():
        gameover_called[0] = True

    chess = Chess()
    chess.onStalemate = on_stalemate
    chess.onGameOver = on_gameover

    # Posicion donde un movimiento causa ahogado
    # Reina en c6 puede moverse a b6 para ahogar al rey negro en a8
    chess.setFen("k7/8/2Q5/8/8/8/8/4K3 w - - 0 1")
    chess.play("c6-b6")  # Reina a b6, causa ahogado

    passed = stalemate_called[0] == True
    print_test(
        "Callback onStalemate fue llamado", passed, f"Llamado: {stalemate_called[0]}"
    )
    all_passed = all_passed and passed

    passed = gameover_called[0] == True
    print_test(
        "Callback onGameOver fue llamado", passed, f"Llamado: {gameover_called[0]}"
    )
    all_passed = all_passed and passed

    return all_passed


def test_draw_callback():
    """Prueba callback onDraw."""
    print_header("TEST: Callback onDraw")
    all_passed = True

    draw_called = [False]
    gameover_called = [False]

    def on_draw():
        draw_called[0] = True

    def on_gameover():
        gameover_called[0] = True

    chess = Chess()
    chess.onDraw = on_draw
    chess.onGameOver = on_gameover

    # Posicion de material insuficiente
    chess.setFen("4k3/8/8/8/8/8/4N3/4K3 w - - 0 1")
    # Capturar el caballo dejaria K vs K
    # Mejor: cargar directamente K vs K
    chess.setFen("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
    # El callback deberia llamarse al detectar la condicion
    # Pero la deteccion ocurre en play(), necesitamos un movimiento

    # Usemos regla de 50 movimientos
    chess = Chess()
    chess.onDraw = on_draw
    chess.onGameOver = on_gameover
    chess.setFen("4k3/8/8/8/8/8/8/4KR2 w - - 99 50")
    chess.play("f1-f2")

    passed = draw_called[0] == True
    print_test("Callback onDraw fue llamado", passed, f"Llamado: {draw_called[0]}")
    all_passed = all_passed and passed

    return all_passed


def test_not_stalemate_if_can_move():
    """Prueba que no es ahogado si hay movimientos legales."""
    print_header("TEST: No Ahogado si Hay Movimientos")
    all_passed = True

    chess = Chess()
    chess.setFen("k7/8/1K6/8/8/8/8/Q7 w - - 0 1")
    # Antes de que la reina mueva, el negro puede moverse
    # Pero es turno de blancas...

    # Configurar turno negro con movimientos
    chess.setFen("k7/8/8/8/8/8/8/4K3 b - - 0 1")

    passed = chess.isStalemate() == False
    print_test(
        "Rey con movimientos no esta ahogado",
        passed,
        f"isStalemate: {chess.isStalemate()}",
    )
    all_passed = all_passed and passed

    moves = chess.getLegalMoves("a8")
    passed = len(moves) > 0
    print_test("Rey tiene movimientos legales", passed, f"Movimientos: {moves}")
    all_passed = all_passed and passed

    return all_passed


def run_all_tests():
    """Ejecuta todas las pruebas de tablas y ahogado."""
    print("\n" + "#" * 60)
    print("#  PRUEBAS DE TABLAS Y AHOGADO")
    print("#" * 60)

    results = []

    results.append(("Ahogado Basico", test_stalemate_basic()))
    results.append(("Ahogado Rey Solo", test_stalemate_king_only()))
    results.append(("Ahogado con Peones", test_stalemate_with_pawns()))
    results.append(("K vs K", test_insufficient_material_k_vs_k()))
    results.append(("K vs K+B", test_insufficient_material_k_vs_kb()))
    results.append(("K vs K+N", test_insufficient_material_k_vs_kn()))
    results.append(
        ("K+B vs K+B mismo color", test_insufficient_material_kb_vs_kb_same_color())
    )
    results.append(
        (
            "K+B vs K+B diferente color",
            test_not_insufficient_material_kb_vs_kb_different_color(),
        )
    )
    results.append(
        ("Con Peones no es insuficiente", test_not_insufficient_material_with_pawn())
    )
    results.append(
        ("Con Torre no es insuficiente", test_not_insufficient_material_with_rook())
    )
    results.append(("Regla 50 Movimientos", test_fifty_move_rule()))
    results.append(("Reset 50 mov al capturar", test_fifty_move_resets_on_capture()))
    results.append(
        ("Reset 50 mov al mover peon", test_fifty_move_resets_on_pawn_move())
    )
    results.append(("Callback onStalemate", test_stalemate_callback()))
    results.append(("Callback onDraw", test_draw_callback()))
    results.append(("No ahogado con movimientos", test_not_stalemate_if_can_move()))

    print("\n" + "=" * 60)
    print("  RESUMEN DE PRUEBAS DE TABLAS Y AHOGADO")
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
