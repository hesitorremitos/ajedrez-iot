"""
Script Principal de Pruebas del Modulo Chess
Ejecuta todas las pruebas y genera un resumen completo.
"""

import sys

sys.path.insert(0, ".")


def main():
    print("\n" + "=" * 70)
    print("  SUITE DE PRUEBAS COMPLETA - MODULO CHESS")
    print("  Modulo de Ajedrez para ESP32 (MicroPython)")
    print("=" * 70)

    all_results = []

    # Importar y ejecutar cada modulo de pruebas
    print("\n  Ejecutando pruebas...")

    # Test 1: Movimientos Basicos
    try:
        from test_basic_moves import run_all_tests as test_basic

        result = test_basic()
        all_results.append(("Movimientos Basicos", result))
    except Exception as e:
        print(f"  [ERROR] test_basic_moves: {e}")
        all_results.append(("Movimientos Basicos", False))

    # Test 2: Movimientos Especiales
    try:
        from test_special_moves import run_all_tests as test_special

        result = test_special()
        all_results.append(("Movimientos Especiales", result))
    except Exception as e:
        print(f"  [ERROR] test_special_moves: {e}")
        all_results.append(("Movimientos Especiales", False))

    # Test 3: Jaque y Jaque Mate
    try:
        from test_check_checkmate import run_all_tests as test_check

        result = test_check()
        all_results.append(("Jaque y Jaque Mate", result))
    except Exception as e:
        print(f"  [ERROR] test_check_checkmate: {e}")
        all_results.append(("Jaque y Jaque Mate", False))

    # Test 4: Tablas y Ahogado
    try:
        from test_stalemate_draw import run_all_tests as test_stalemate

        result = test_stalemate()
        all_results.append(("Tablas y Ahogado", result))
    except Exception as e:
        print(f"  [ERROR] test_stalemate_draw: {e}")
        all_results.append(("Tablas y Ahogado", False))

    # Test 5: FEN, PGN, Historial y Undo
    try:
        from test_fen_pgn_history import run_all_tests as test_fen

        result = test_fen()
        all_results.append(("FEN, PGN, Historial y Undo", result))
    except Exception as e:
        print(f"  [ERROR] test_fen_pgn_history: {e}")
        all_results.append(("FEN, PGN, Historial y Undo", False))

    # Resumen Final
    print("\n")
    print("=" * 70)
    print("  RESUMEN FINAL DE LA SUITE DE PRUEBAS")
    print("=" * 70)

    passed_suites = 0
    for name, passed in all_results:
        status = "PASS" if passed else "FAIL"
        icon = "[OK]" if passed else "[X]"
        print(f"  {icon} {name}: {status}")
        if passed:
            passed_suites += 1

    print("=" * 70)
    total = len(all_results)
    if passed_suites == total:
        print(f"  RESULTADO: TODAS LAS PRUEBAS PASARON ({passed_suites}/{total})")
        print("  El modulo Chess esta listo para usar!")
    else:
        print(f"  RESULTADO: {passed_suites}/{total} suites pasaron")
        print("  Revisar las pruebas que fallaron.")
    print("=" * 70)
    print()

    return passed_suites == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
