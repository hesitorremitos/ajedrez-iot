"""Tests for buildStatePayload helper."""

from modules.chess import Chess
from modules.chessclock import ChessClock
from modules.mqttClient.payload import buildStatePayload


def test_buildStatePayload_minimal():
    chess = Chess()
    whiteClock = ChessClock()
    blackClock = ChessClock()
    whiteClock.reset(600000)
    blackClock.reset(600000)

    payload = buildStatePayload(chess, whiteClock, blackClock)

    assert "fen" in payload
    assert payload["turno"] == "w"
    assert payload["tiempoW"] == "10:00"
    assert payload["tiempoB"] == "10:00"


def test_buildStatePayload_with_game_state():
    chess = Chess()
    chess.play("e2-e4")
    whiteClock = ChessClock()
    blackClock = ChessClock()
    whiteClock.reset(300000)
    blackClock.reset(300000)

    payload = buildStatePayload(
        chess,
        whiteClock,
        blackClock,
        gameState={
            "move": "e2-e4",
            "pgn": "1. e4",
            "sensores": 12,
            "nombresBlancas": "Alice",
            "nombresNegras": "Bob",
        },
    )

    assert payload["move"] == "e2-e4"
    assert payload["pgn"] == "1. e4"
    assert payload["sensores"] == 12
    assert payload["nombresBlancas"] == "Alice"
    assert payload["nombresNegras"] == "Bob"
    assert payload["turno"] == "b"


def test_buildStatePayload_omits_empty_optional_fields():
    chess = Chess()
    whiteClock = ChessClock()
    blackClock = ChessClock()

    payload = buildStatePayload(
        chess,
        whiteClock,
        blackClock,
        gameState={"move": "", "pgn": None},
    )

    assert "move" not in payload
    assert "pgn" not in payload
