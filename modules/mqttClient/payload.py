"""Build flat JSON payloads for MQTT state/events (coordinator helper)."""


def buildStatePayload(chess, whiteClock, blackClock, gameState=None):
    """
    Build a flat dict for MQTT publish from Chess and ChessClock instances.

    Args:
        chess: Chess instance with getFen() and getTurn()
        whiteClock: ChessClock with getText()
        blackClock: ChessClock with getText()
        gameState: optional dict with move, pgn, sensores, nombresBlancas, nombresNegras

    Returns:
        dict: payload with only present keys
    """
    payload = {
        "fen": chess.getFen(),
        "turno": chess.getTurn(),
        "tiempoW": whiteClock.getText(),
        "tiempoB": blackClock.getText(),
    }

    if not gameState:
        return payload

    optionalKeys = (
        "move",
        "pgn",
        "sensores",
        "nombresBlancas",
        "nombresNegras",
    )
    for key in optionalKeys:
        value = gameState.get(key)
        if value is not None and value != "":
            payload[key] = value

    return payload
