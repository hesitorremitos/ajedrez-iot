# AGENTS Guide for Zulma

This is the default playbook for coding agents working in this repository.
Follow it for commands, architecture constraints, and style decisions.

## Rule Sources

- Not found: `.cursorrules`
- Not found: `.cursor/rules/`

If Cursor rules appear later, merge them into this file.

## Project Snapshot

- Runtime target: MicroPython on ESP32
- Local dev runtime: CPython 3.11+
- Test framework: `pytest`
- Dependency manager: `uv`
- Primary modules: `chess`, `network`, `chessclock`, `chessgame`, `chessdisplay`
- Core priority: memory-aware implementations for constrained hardware

## Environment Setup

```bash
# install dependencies
uv sync

# optional dev dependencies
uv sync --extra dev
```

Pytest config in `pyproject.toml`:
- `testpaths = ["tests"]`
- `pythonpath = ["."]`

## Build, Lint, Test Commands

There is no dedicated build command and no configured linter/formatter.
The main quality gate is tests.

```bash
# run full test suite
uv run pytest

# verbose output
uv run pytest -v

# stop on first failure
uv run pytest -x

# run one module folder
uv run pytest tests/modules/chess

# run one test file
uv run pytest tests/modules/chess/test_basic_moves.py

# run one test class
uv run pytest tests/modules/network/test_access_point.py::TestAccessPointStart

# run one test function (single test)
uv run pytest tests/modules/chess/test_basic_moves.py::test_pawn_single_push

# run tests by keyword expression
uv run pytest -k "checkmate or stalemate"
```

Fallback if `uv` is unavailable: run `pytest` with the same arguments.

## Repository Layout

```text
modules/
  <NAME>_REQUIREMENTS.md
  <module>/
    __init__.py
    <ClassName>.py

tests/
  conftest.py
  modules/<module>/test_*.py
```

## Architecture and Boundaries

- Read `modules/*_REQUIREMENTS.md` before implementing changes
- Keep modules focused and testable
- Preserve clear boundaries between game logic, clocks, rendering, and transport

## Naming Conventions (Critical)

Public APIs intentionally use camelCase. Do not convert to snake_case.

- Methods: `getLegalMoves`, `isCheckmate`, `setFen`
- Attributes: `currentTurnMove`, `castlingRights`, `clientCount`
- Private members: `_` + camelCase, e.g. `_halfmoveClock`
- Constants: `UPPER_SNAKE_CASE`, e.g. `INITIAL_FEN`, `_AP_IP`
- Tests can keep normal pytest snake_case naming

## Imports and Dependencies

- Import order: stdlib first, then local imports
- Keep imports minimal for MicroPython compatibility
- Guard hardware/platform imports in testable code paths:
  - `try: import <module>`
  - `except ImportError: <name> = None`
- Avoid heavy dependencies unless explicitly required

## Formatting and Code Style

- Follow existing style in touched files
- Use 4-space indentation
- Avoid unrelated reformatting
- Prefer explicit control flow over clever abstractions
- Add comments only when intent is non-obvious
- Preserve existing Spanish/English docstring patterns where present

## Types and API Contracts

- Runtime modules generally avoid Python type hints
- Use docstrings to clarify parameters/returns when needed
- Preserve existing return contracts
- Command-like operations often return `True`/`False`
- Do not change public signatures unless requirements demand it

## Error Handling

- Fail gracefully around hardware/external interactions
- Avoid exception-heavy control flow in hot paths
- Preserve current fallback conventions:
  - `False` for command failures
  - empty list/dict-like values for query failures when appropriate

## Memory and Performance

ESP32 memory constraints are first-order design constraints.

- Avoid precomputing large move sets
- Avoid unbounded caches
- Avoid features that materially increase resident RAM usage
- Keep allocations modest in frequently called methods

## Testing Conventions

- Write focused arrange/act/assert tests
- Reuse fixtures from `tests/conftest.py`
- Keep helper assertions small and local where practical
- Mock MicroPython-specific modules for CPython test runs
- Run single-test targets first, then broader suites

## Agent Checklist

1. Read related `modules/*_REQUIREMENTS.md`
2. Preserve camelCase API names
3. Keep exports accurate in each `__init__.py`
4. Add/update matching tests under `tests/modules/<module>/`
5. Run at least one single-test command for touched behavior
6. Run broader test scope before finishing when feasible
7. Avoid unrelated refactors and heavy dependencies
