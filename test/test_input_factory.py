import pytest

from pong.config import InputMode
from pong.infra.input.arduino.source import ArduinoInputSource
from pong.infra.input.arduino_rasp.source import ArduinoRaspInputSource
from pong.infra.input.botoes import gpio
from pong.infra.input.factory import make_input_source
from pong.infra.input.serial.frame import SerialPotentiometerFrame


async def test_original_source_maps_both_channels_without_gpio(settings, monkeypatch):
    updates = []
    source = make_input_source(settings, updates.append, lambda error: None)
    assert isinstance(source, ArduinoInputSource)

    async def start():
        source._serial._connected = True

    monkeypatch.setattr(source._serial, "start", start)
    await source.start()
    assert await source.is_connected()
    source._receive(SerialPotentiometerFrame(10, 90, 123))
    assert updates[0].player1_pct == 10
    assert updates[0].player2_pct == 90
    assert updates[0].timestamp == 123
    await source.stop()


def test_factory_hybrid_does_not_open_gpio_until_start(settings):
    settings.input_mode = InputMode.ARDUINO_RASP
    settings.button_up_pin, settings.button_down_pin = 27, 22
    source = make_input_source(settings, lambda state: None, lambda error: None)
    assert isinstance(source, ArduinoRaspInputSource)
    assert source._monitor._up is None


@pytest.mark.parametrize("debounce,expected", [(0, None), (0.05, 0.05)])
def test_gpio_adapter_pullup_bcm_debounce_and_cleanup(monkeypatch, debounce, expected):
    calls = []

    class Button:
        is_active = True

        def __init__(self, pin, **kwargs):
            calls.append((pin, kwargs))

        def close(self):
            calls.append("closed")

    monkeypatch.setattr(gpio, "Button", Button)
    reader = gpio.LeitorBotoesGPIO(27, debounce)
    assert reader.esta_pressionado
    reader.fechar()
    assert calls == [(27, {"pull_up": True, "bounce_time": expected}), "closed"]
