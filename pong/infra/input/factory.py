from collections.abc import Callable

from pong.config import InputMode, Settings
from pong.domain.pong.state import PongState
from pong.infra.input.arduino.source import ArduinoInputSource
from pong.infra.input.arduino_rasp.source import ArduinoRaspInputSource
from pong.protocols.input_source import InputSourceProtocol


def make_input_source(
    settings: Settings,
    on_update: Callable[[PongState], None],
    on_failure: Callable[[BaseException], None],
) -> InputSourceProtocol:
    if settings.input_mode == InputMode.ARDUINO:
        return ArduinoInputSource(settings, on_update)
    return ArduinoRaspInputSource(settings, on_update, on_failure)
