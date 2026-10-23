from collections.abc import Callable
from time import time

from pong.config import Settings
from pong.domain.botoes.leitura import LeituraJogadorBotoes
from pong.domain.pong.state import PongState
from pong.infra.input.arduino_rasp.composicao import CompositorEstadoArduinoRasp
from pong.infra.input.arduino_rasp.mapeamento import resolver_mapeamento_arduino_rasp
from pong.infra.input.arduino_rasp.monitor_botoes import MonitorBotoes
from pong.infra.input.serial.frame import SerialPotentiometerFrame
from pong.infra.input.serial.source import SerialInputSource


class ArduinoRaspInputSource:
    def __init__(
        self,
        settings: Settings,
        on_update: Callable[[PongState], None],
        on_failure: Callable[[BaseException], None],
    ) -> None:
        self._on_update = on_update
        self._composer = CompositorEstadoArduinoRasp(resolver_mapeamento_arduino_rasp(settings))
        self._monitor = MonitorBotoes(settings, self._receive_buttons, on_failure)
        self._buttons = self._monitor.leitura
        self._frame: SerialPotentiometerFrame | None = None
        self._serial = SerialInputSource(settings, self._receive_serial)
        self._started = False

    def _receive_serial(self, frame: SerialPotentiometerFrame) -> None:
        self._frame = frame
        self._publish()

    def _receive_buttons(self, reading: LeituraJogadorBotoes) -> None:
        self._buttons = reading
        self._publish()

    def _publish(self) -> None:
        if self._frame is not None:
            self._on_update(self._composer.compor(self._frame, self._buttons, time()))

    async def start(self) -> None:
        if self._started:
            return
        ready = False
        try:
            await self._monitor.start()
            await self._serial.start()
            self._started = ready = True
        finally:
            if not ready:
                await self.stop()

    async def stop(self) -> None:
        try:
            await self._monitor.stop()
        finally:
            self._started = False
            self._frame = None
            await self._serial.stop()

    async def is_connected(self) -> bool:
        return self._started and await self._serial.is_connected()
