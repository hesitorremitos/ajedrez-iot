import pytest

from modules.chess import Chess
@pytest.fixture
def chess():
    return Chess()
