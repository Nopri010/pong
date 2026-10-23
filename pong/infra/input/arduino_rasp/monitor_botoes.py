import asyncio
from collections.abc import Callable
from contextlib import ExitStack
from time import monotonic, time

from pong.config import Settings
from pong.domain.botoes.controle import ControleBotoes
from pong.domain.botoes.leitura import LeituraJogadorBotoes
from pong.infra.input.botoes.gpio import LeitorBotoesGPIO
from pong.protocols.leitor_botoes import LeitorBotoesProtocol


class MonitorBotoes:
    def __init__(
        self,
        settings: Settings,
        on_update: Callable[[LeituraJogadorBotoes], None],
        on_failure: Callable[[BaseException], None],
        reader_factory: Callable[[int, float], LeitorBotoesProtocol] = LeitorBotoesGPIO,
    ) -> None:
        self._settings = settings
        self._on_update = on_update
        self._on_failure = on_failure
        self._reader_factory = reader_factory
        self._control = ControleBotoes(
            settings.button_initial_percentage, settings.button_speed_percent_per_second
        )
        self.leitura = LeituraJogadorBotoes(
            settings.button_player, self._control.percentage, time()
        )
        self._up: LeitorBotoesProtocol | None = None
        self._down: LeitorBotoesProtocol | None = None
        self._task: asyncio.Task[None] | None = None
        self._resources = ExitStack()

    async def start(self) -> None:
        if self._task is not None:
            return
        up_pin, down_pin = self._settings.button_up_pin, self._settings.button_down_pin
        if up_pin is None or down_pin is None:
            raise ValueError("Configure os dois GPIOs BCM antes de iniciar")
        # ExitStack também fecha o primeiro GPIO se a criação do segundo falhar.
        with ExitStack() as resources:
            self._up = self._reader_factory(up_pin, self._settings.button_debounce_seconds)
            resources.callback(self._up.fechar)
            self._down = self._reader_factory(down_pin, self._settings.button_debounce_seconds)
            resources.callback(self._down.fechar)
            self._resources = resources.pop_all()
        self._task = asyncio.create_task(self._run(), name="MonitorBotoes")
        self._task.add_done_callback(self._finished)

    def _finished(self, task: asyncio.Task[None]) -> None:
        if not task.cancelled():
            error = task.exception()
            if error is not None:
                self._on_failure(error)

    def amostrar(self, segundos: float) -> None:
        if self._up is None or self._down is None:
            return
        up, down = self._up.esta_pressionado, self._down.esta_pressionado
        percentage = self._control.avancar(up, down, segundos)
        previous = self.leitura
        if (percentage, up, down) != (previous.percentage, previous.subir, previous.descer):
            self.leitura = LeituraJogadorBotoes(previous.player, percentage, time(), up, down)
            self._on_update(self.leitura)

    async def _run(self) -> None:
        previous = monotonic()
        while True:
            await asyncio.sleep(self._settings.button_poll_interval_seconds)
            now = monotonic()
            self.amostrar(now - previous)
            previous = now

    async def stop(self) -> None:
        task, self._task = self._task, None
        try:
            if task is not None:
                task.cancel()
                # gather recupera a falha já comunicada pelo callback sem impedir limpeza.
                await asyncio.gather(task, return_exceptions=True)
        finally:
            self._up = self._down = None
            self._resources.close()
