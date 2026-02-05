# Zulma - MicroPython ESP32 Project

## Project Overview
Modular MicroPython system for ESP32 microcontrollers. Currently implements a chess engine optimized for resource-constrained environments. Future modules will include WiFi AccessPoint for network-based gameplay.

## Critical Architecture Decisions

### Module Structure
- Each module lives in `modules/<name>/` with its own `__init__.py` for exports
- Requirements documented in `modules/<NAME>_REQUIREMENTS.md` before implementation
- Modules must be ESP32/MicroPython compatible with memory optimization as priority
- Example: `modules/chess/Chess.py` exports via `modules/chess/__init__.py`

### Naming Conventions (NON-PYTHONIC!)
**This project uses camelCase, not snake_case:**
- ✅ Methods/properties: `getLegalMoves()`, `isCheck()`, `currentTurnMove`
- ✅ Private: `_isSquareAttackedBy()`, `_board`, `_halfmoveClock`
- ✅ Constants: `INITIAL_BOARD`, `INITIAL_FEN`
- ❌ Never use: `get_legal_moves()`, `is_check()`, `current_turn_move`

This convention is project-wide and required per technical specifications.

## Chess Module Deep Dive

### Board Representation
```python
# 64-character list: index 0 = a1, index 63 = h8
# Pieces: 'P'=white pawn, 'p'=black pawn, ' '=empty
# a1=0, b1=1, ..., h1=7, a2=8, ..., h8=63
chess._board[0]   # a1
chess._board[63]  # h8
```

### Move Notation Format
```python
# Standard moves use dash separator (not concatenation)
'e2-e4'      # Normal move
'e4-d5'      # Capture (same format)
'e7-e8=Q'    # Promotion (Q/R/B/N)
'O-O'        # Kingside castling
'O-O-O'      # Queenside castling
'e5-d6'      # En passant (looks like normal move)
```

### History Storage Pattern
```python
# History is list of 2-element lists: [[white_move, black_move], ...]
# Incomplete turns have empty string for black
[['e2-e4', 'e7-e5'], ['g1-f3', 'b8-c6']]  # Two complete turns
[['e2-e4', 'e7-e5'], ['d2-d4', '']]       # White moved, black pending
```

Tracked in two places:
- `_history`: completed turn pairs
- `_currentTurnMove`: white's move waiting for black's response

### State Management for Undo
Every move saves complete state snapshot via `_saveState()`:
```python
# State includes: board, turn, castling rights, en passant, 
# halfmove clock, fullmove number, history, currentTurnMove
self._moveStack.append(state_dict)
```
See `_saveState()` and `_restoreState()` at lines 183-203.

### Callback System
Property setters register callbacks that auto-trigger after `play()`:
```python
chess.onCheck = lambda: print("Check!")
chess.onCheckmate = my_handler_function
# Triggered automatically in _triggerCallbacks() after each move
```

## Testing Patterns

### Fixture & Helper
```python
# conftest.py provides chess fixture
def test_something(chess):  # chess is fresh Chess() instance
    assert chess.play('e2-e4')
    
# Use helper for piece assertions
def assert_piece_at(chess, square, expected_piece):
    actual = chess.getPiece(square)
    assert actual == expected_piece
```

### Test Organization
- `test_basic_moves.py` - Pawn, knight, bishop, rook, queen, king moves
- `test_special_moves.py` - Castling, promotion, en passant
- `test_check_checkmate.py` - Check/checkmate detection scenarios
- `test_fen_pgn_history.py` - FEN parsing, PGN export, history tracking
- `test_stalemate_draw.py` - Stalemate, insufficient material, 50-move rule

## Memory Optimization Decisions

**Intentional omissions for ESP32 constraints:**
1. No `getAllMoves()` method - would consume too much RAM generating all legal moves
2. No Segoe Chess font rendering - eliminated from original design
3. History stored efficiently as paired moves, not individual move objects
4. Debug mode off by default to reduce print overhead

When adding features, always consider ESP32's limited RAM (~100KB typically available).

## Development Workflow

```powershell
# Run tests (pytest autodiscovery from pyproject.toml)
pytest

# Run specific test file
pytest tests/modules/chess/test_basic_moves.py

# Run with verbose output
pytest -v

# Test paths configured in pyproject.toml: testpaths = ["tests"], pythonpath = ["."]
```

### Dependencies
- **Runtime**: None (pure MicroPython)
- **Testing**: pytest>=9.0.2
- **Dev tools**: micropython-esp32-stubs (for IDE support, optional)

Uses `uv` for fast Python package management (note `uv.lock` presence).

## Adding New Modules

1. Create `modules/<NAME>_REQUIREMENTS.md` with detailed specs
2. Document API in camelCase format with parameter/return types
3. Create `modules/<name>/` directory
4. Implement in `modules/<name>/<Name>.py`
5. Export via `modules/<name>/__init__.py`
6. Add tests in `tests/modules/<name>/`
7. Update this file with module-specific patterns

See `CHESS_REQUIREMENTS.md` and `ACCESSPOINT_REQUIREMENTS.md` as templates.

## Common Patterns

### FEN/PGN Support
Most game modules should support standard notation:
- `setFen(fen_string)` - Load position from FEN
- `getFen()` - Export current state to FEN
- `getPgn(headers)` - Export game with optional PGN headers

### Debug Mode
```python
# Enable debug logging (off by default for production)
chess = Chess(debug=True)
chess.debug = True  # or toggle via property
# Uses _log() method internally: if self._debug: print(...)
```

## Key Files Reference
- [modules/chess/Chess.py](modules/chess/Chess.py) - Complete chess implementation (~1260 lines)
- [modules/CHESS_REQUIREMENTS.md](modules/CHESS_REQUIREMENTS.md) - Chess module specification
- [tests/conftest.py](tests/conftest.py) - Shared pytest fixtures
- [pyproject.toml](pyproject.toml) - Python 3.11+, pytest config, dependency management
