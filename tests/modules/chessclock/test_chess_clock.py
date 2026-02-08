from modules.chessclock import ChessClock


def test_timeout_latch_resets_on_set_time():
    clock = ChessClock()
    timeouts = []

    def onTimeout():
        timeouts.append("timeout")

    clock.onTimeout = onTimeout
    clock.setTime(0)
    assert timeouts == ["timeout"]

    clock.setTime(5000)
    clock.setTime(0)
    assert len(timeouts) == 2


def test_timeout_latch_resets_on_add_time():
    clock = ChessClock()
    timeouts = []

    def onTimeout():
        timeouts.append("timeout")

    clock.onTimeout = onTimeout
    clock.setTime(0)
    assert len(timeouts) == 1

    clock.addTime(2000)
    clock.addTime(-2000)
    assert len(timeouts) == 2
