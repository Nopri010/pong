import math

import pytest

from pong.domain.botoes.controle import ControleBotoes


@pytest.mark.parametrize(
    ("up", "down", "expected"),
    [(True, False, 30), (False, True, 70), (True, True, 50), (False, False, 50)],
)
def test_direction_and_elapsed_time(up, down, expected):
    control = ControleBotoes(50, 100)
    assert control.avancar(up, down, 0.2) == expected


def test_hold_release_and_limits():
    control = ControleBotoes(50, 100)
    assert control.avancar(True, False, 0.1) == 40
    assert control.avancar(True, False, 0.1) == 30
    assert control.avancar(False, False, 1) == 30
    assert control.avancar(True, False, 1) == 0
    assert control.avancar(False, True, 2) == 100


@pytest.mark.parametrize(
    "initial,speed", [(-1, 10), (101, 10), (math.nan, 10), (50, 0), (50, -1), (50, math.inf)]
)
def test_invalid_control(initial, speed):
    with pytest.raises(ValueError):
        ControleBotoes(initial, speed)


@pytest.mark.parametrize("elapsed", [-1, math.nan, math.inf])
def test_invalid_elapsed(elapsed):
    with pytest.raises(ValueError):
        ControleBotoes(50, 100).avancar(True, False, elapsed)


def test_speed_independent_of_poll_count():
    fast = ControleBotoes(0, 20)
    slow = ControleBotoes(0, 20)
    for _ in range(100):
        fast.avancar(False, True, 0.01)
    assert fast.percentage == pytest.approx(slow.avancar(False, True, 1))
