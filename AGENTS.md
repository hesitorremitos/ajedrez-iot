# AGENTS Guide for Zulma

This playbook is for coding agents working in `C:\laragon\www\zulma`.
Follow it for commands, architecture boundaries, and style expectations.

## Rule Sources (Merged)
- Cursor rules file: not found (`.cursorrules`)
- Cursor rules directory: not found (`.cursor/rules/`)
- Copilot rules: found at `.github/copilot-instructions.md` and merged here

Merged Copilot guidance:
- Target platform is MicroPython on ESP32 with modular architecture.
- Public API naming is intentionally camelCase (non-pythonic by design).
- Prioritize memory-aware implementations for constrained hardware.
- Keep module exports explicit in each `modules/<name>/__init__.py`.

## Project Snapshot
- Runtime target: MicroPython on ESP32
- Local development runtime: CPython 3.11+
- Package/dependency tool: `uv`
- Test framework: `pytest`
- Primary modules: `chess`, `network`, `chessclock`, `chessdisplay`, `sse`
- Utility scripts: `build.py` and `deploy.py`

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
lib/                    # runtime libs for device
build/                  # generated artifacts for deployment
build.py                # `uv run build`
deploy.py               # `uv run deploy`
```

## Setup Commands
```bash
# install base dependencies
uv sync
# optional project extras
uv sync --extra dev
# dev tool group (mpy-cross, esptool, ampy)
uv sync --group dev
```

## Build, Lint, and Test Commands
There is no configured linter/formatter/type-checker in `pyproject.toml`.
Primary quality gate is automated tests.

```bash
# full suite
uv run pytest
# verbose
uv run pytest -v
# stop on first failure
uv run pytest -x
# one module folder
uv run pytest tests/modules/chess
# one file
uv run pytest tests/modules/chess/test_basic_moves.py
# one class
uv run pytest tests/modules/network/test_access_point.py::TestAccessPointStart
# one specific test (single test)
uv run pytest tests/modules/chess/test_basic_moves.py::test_pawn_single_push
# keyword filter
uv run pytest -k "checkmate or stalemate"
```

Fallback when `uv` is unavailable: run `pytest` with the same arguments.

```bash
# compile lib/*.py -> build/lib/*.mpy
uv run build
# upload build/ to board (CLI arg)
uv run deploy COM5
# upload build/ using env var
ESP32_PORT=COM5 uv run deploy
```

## Architecture and Boundaries
- Read relevant docs in `modules/*_REQUIREMENTS.md` before editing code.
- Keep each module focused on one responsibility.
- Preserve boundaries between rule engine, networking, clock, and rendering.
- Do not move orchestration concerns into pure rule modules unless required.
- Avoid heavy dependencies that reduce MicroPython compatibility.

## Naming Conventions (Critical)
Public APIs intentionally use camelCase. Do not convert to snake_case.

- Methods: `getLegalMoves`, `isCheckmate`, `setFen`, `getStatus`
- Attributes: `currentTurnMove`, `castlingRights`, `clientCount`
- Private members: `_` + camelCase, e.g. `_halfmoveClock`
- Constants: `UPPER_SNAKE_CASE`, e.g. `INITIAL_FEN`, `_AP_IP`
- Tests may keep pytest-style snake_case names

## Imports and Dependency Style
- Order imports as: stdlib, third-party, local modules.
- Keep imports minimal and explicit.
- Guard MicroPython-only imports in testable code paths:
  - `try: import network`
  - `except ImportError: network = None`
- Avoid global mutable state unless needed for runtime constraints.

## Formatting and General Style
- Follow existing style in touched files.
- Use 4-space indentation.
- Prefer explicit control flow over clever abstractions.
- Avoid unrelated reformatting and broad refactors.
- Add comments only for non-obvious intent.
- Preserve existing Spanish/English docstring patterns where present.

## Types and API Contracts
- Runtime modules generally avoid Python type hints.
- Tooling/helper scripts may use type hints when already established.
- Use docstrings for non-trivial param/return behavior.
- Preserve return contracts used by callers and tests.
- Many command methods return `True`/`False` instead of raising.
- Do not change public signatures without requirements updates.

## Error Handling Expectations
- Fail gracefully around hardware, serial, and network interactions.
- Prefer predictable fallback values over uncaught exceptions.
- Keep exception handling simple in hot paths.
- Preserve conventions:
  - action methods: return `False` on failure
  - query methods: return empty list/dict-like fallback when appropriate
- For scripts (`build.py`, `deploy.py`), return non-zero exit code on failure.

## Memory and Performance Rules (ESP32 First)
- Avoid precomputing large structures unless clearly justified.
- Avoid unbounded caches and unnecessary object churn.
- Keep allocations modest in frequently called methods.
- Prefer compact data representations.
- Keep debug/logging optional and lightweight.

## Testing Conventions
- Write focused arrange/act/assert tests.
- Reuse fixtures from `tests/conftest.py` when possible.
- Use mocks for MicroPython-specific modules under CPython tests.
- Run the most targeted single test first, then broaden scope.
- Keep tests under `tests/modules/<module>/`.

## Agent Checklist
1. Read related `modules/*_REQUIREMENTS.md` before coding.
2. Preserve camelCase API names across public/private members.
3. Keep `__init__.py` exports accurate after edits.
4. Add/update tests for behavior changes.
5. Run at least one single-test command for touched behavior.
6. Run broader pytest scope when feasible.
7. Avoid unrelated refactors and dependency creep.
8. If `.cursorrules` or `.cursor/rules/` is added later, merge into this file.
