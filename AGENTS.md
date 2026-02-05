# Agent Guide for Zulma Codebase

**Project**: Modular MicroPython system for ESP32 microcontrollers  
**Language**: Python 3.11+ (testing), MicroPython (runtime)  
**Package Manager**: `uv` (preferred), npm/bun (fallback)

## Build, Lint, and Test Commands

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/modules/chess/test_basic_moves.py

# Run specific test function
pytest tests/modules/chess/test_basic_moves.py::test_pawn_single_push

# Run with verbose output
pytest -v

# Run tests for specific module
pytest tests/modules/chess/
pytest tests/modules/network/
```

### Linting & Formatting
No linter/formatter configured yet. Maintain existing code style (see below).

### Dependencies
```bash
# Install all dependencies
uv sync

# Add runtime dependency
uv add <package>

# Add dev dependency
uv add --dev <package>
```

## Critical: NON-PYTHONIC Naming Convention

**This project uses camelCase, NOT snake_case. This is intentional and project-wide.**

### Correct Naming (camelCase)
- ✅ Methods: `getLegalMoves()`, `isCheck()`, `play()`, `getPiece()`
- ✅ Properties: `currentTurnMove`, `castlingRights`, `enPassantSquare`
- ✅ Private members: `_isSquareAttackedBy()`, `_board`, `_halfmoveClock`
- ✅ Constants: `INITIAL_BOARD`, `INITIAL_FEN`, `_AP_IP`
- ✅ Constructor args: `def __init__(self, debug=False)`

### Incorrect Naming (NEVER use)
- ❌ `get_legal_moves()`, `is_check()`, `get_piece()`
- ❌ `current_turn_move`, `castling_rights`, `en_passant_square`
- ❌ `_is_square_attacked_by()`, `_halfmove_clock`

**Exception**: Test files use standard Python `test_function_name` format per pytest conventions.

## Module Structure

### Directory Layout
```
modules/
├── <NAME>_REQUIREMENTS.md      # Specification BEFORE implementation
├── <name>/                     # Package directory (lowercase)
│   ├── __init__.py            # Public exports
│   └── <Name>.py              # Implementation (PascalCase)
└── ...

tests/
└── modules/
    └── <name>/                # Mirror module structure
        ├── test_*.py
        └── ...

lib/                           # MicroPython libraries for IDE autocomplete
└── *.py                       # (gitignored, local only)
```

**Note**: The `lib/` folder contains MicroPython library stubs for IDE autocomplete. It's configured in `.vscode/settings.json` under `python.analysis.extraPaths` and excluded from git.

### Creating a New Module
1. Create `modules/<NAME>_REQUIREMENTS.md` with detailed specs
2. Document API in camelCase with parameter/return types
3. Create `modules/<name>/` directory (lowercase)
4. Implement in `modules/<name>/<Name>.py` (PascalCase class)
5. Export via `modules/<name>/__init__.py`
6. Add tests in `tests/modules/<name>/`
7. Update documentation with module-specific patterns

### Module Export Pattern
```python
# modules/<name>/__init__.py
from .<Name> import <Name>

__all__ = ["<Name>"]
```

## Code Style Guidelines

### Imports
```python
# Standard library first
import sys

# Third-party libraries
try:
    import network  # MicroPython-specific
except ImportError:
    network = None  # Graceful fallback for testing

# Local imports
from modules.chess import Chess
from modules.network import AccessPoint
```

### Docstrings (Spanish or English accepted)
```python
"""
Module description.
Explain purpose and key constraints (e.g., ESP32 memory optimization).
"""

class MyClass:
    """
    Class description.
    
    Explain key architectural decisions.
    """
    
    def myMethod(self, param):
        """
        Method description.
        
        Args:
            param: Description
            
        Returns:
            Description of return value
        """
```

### Type Annotations
**NOT used** - MicroPython doesn't support type hints. Document types in docstrings.

```python
def getPiece(self, square):
    """
    Get piece at square.
    
    Args:
        square: str (e.g., 'e4')
        
    Returns:
        str: Piece character or ' ' if empty
    """
```

### Constants
```python
# Class-level constants (UPPER_SNAKE_CASE)
INITIAL_BOARD = list("RNBQKBNR...")
INITIAL_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# Private class constants
_AP_IP = "192.168.4.1"
_AP_SUBNET = "255.255.255.0"
```

### Error Handling
```python
# Return False on validation failures (NOT exceptions)
def play(self, move):
    if not self._isValidMove(move):
        return False
    # ... process move
    return True

# Catch exceptions for external dependencies
try:
    self._ap.active(True)
    return True
except Exception:
    return False  # Fail gracefully
```

### Memory Optimization for ESP32
**Critical**: ESP32 has ~100KB available RAM. Always optimize for memory:

- ✅ Generate moves on-demand, never precompute all legal moves
- ✅ Use simple lists/dicts over complex objects
- ✅ Reuse buffers when possible
- ✅ Store compact representations (e.g., 64-char list for chess board)
- ❌ Avoid large constant tables
- ❌ Avoid creating intermediate collections unnecessarily
- ❌ No heavy imports (e.g., font rendering libraries)

### Debug Mode Pattern
```python
def __init__(self, debug=False):
    self._debug = debug
    # ...

def _log(self, message):
    """Internal debug logging."""
    if self._debug:
        print(message)
```

## Testing Patterns

### Fixtures (conftest.py)
```python
import pytest
from modules.chess import Chess

@pytest.fixture
def chess():
    return Chess()
```

### Test Structure
```python
def test_feature_description(chess):  # Use fixture
    # Arrange - setup complete
    
    # Act
    result = chess.play("e2-e4")
    
    # Assert
    assert result is True
    assert_piece_at(chess, "e4", "P")

def assert_piece_at(chess, square, expected_piece):
    """Helper for common assertions."""
    actual = chess.getPiece(square)
    assert actual == expected_piece
```

### Test Organization
- `test_basic_*.py` - Core functionality
- `test_special_*.py` - Edge cases, special rules
- `test_<feature>.py` - Feature-specific tests
- Keep tests focused and descriptive

## Common Patterns

### Callback System
```python
# Property-based callbacks
@property
def onCheck(self):
    return self._onCheck

@onCheck.setter
def onCheck(self, callback):
    self._onCheck = callback

# Trigger callbacks after state changes
def _triggerCallbacks(self):
    if self._onCheck and self.isCheck():
        self._onCheck()
```

### State Management for Undo
```python
def _saveState(self):
    """Save complete state snapshot."""
    state = {
        "board": self._board[:],  # Copy list
        "turn": self._turn,
        "castlingRights": self._castlingRights,
        # ... all mutable state
    }
    self._moveStack.append(state)

def _restoreState(self):
    """Restore previous state."""
    if not self._moveStack:
        return False
    state = self._moveStack.pop()
    self._board = state["board"]
    self._turn = state["turn"]
    # ... restore all state
    return True
```

## Key Files Reference
- `modules/chess/Chess.py` - Chess engine implementation
- `modules/network/AccessPoint.py` - WiFi AP manager  
- `modules/CHESS_REQUIREMENTS.md` - Chess module specification
- `modules/ACCESSPOINT_REQUIREMENTS.md` - AccessPoint specification
- `tests/conftest.py` - Shared pytest fixtures
- `pyproject.toml` - Dependencies and pytest config
- `.github/copilot-instructions.md` - Extended architecture guide
