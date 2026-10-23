from collections.abc import Callable

from pong.config import Settings
from pong.domain.pong.state import PongState
from pong.domain.potenciometro.entity import Potenciometro
from pong.infra.input.serial.frame import SerialPotentiometerFrame
from pong.infra.input.serial.source import SerialInputSource


class ArduinoInputSource:
    def __init__(self, settings: Settings, on_update: Callable[[PongState], None]) -> None:
        self._pots = (
            Potenciometro.config(identifier="player1", player=1, pin=settings.pot1_pin),
            Potenciometro.config(identifier="player2", player=2, pin=settings.pot2_pin),
        )
        self._on_update = on_update
        self._serial = SerialInputSource(settings, self._receive)

    def _receive(self, frame: SerialPotentiometerFrame) -> None:
        self._on_update(
            PongState(
                self._pots[0].reading_from_percentage(frame.channel_1_percentage, frame.timestamp),
                self._pots[1].reading_from_percentage(frame.channel_2_percentage, frame.timestamp),
                frame.timestamp,
            )
        )

    async def start(self) -> None:
        await self._serial.start()

    async def stop(self) -> None:
        await self._serial.stop()

    async def is_connected(self) -> bool:
        return await self._serial.is_connected()
