import asyncio
from queue import Empty, SimpleQueue
from time import time

from rich.console import Console
from rich.live import Live
from rich.progress_bar import ProgressBar
from rich.table import Table

from pong.config import InputMode, Settings
from pong.domain.botoes.leitura import LeituraJogadorBotoes
from pong.domain.pong.state import PongState
from pong.infra.input.factory import make_input_source


def render_readings(state: PongState | None, connected: bool = False) -> Table:
    table = Table(
        title="Diagnóstico das entradas",
        caption=f"Serial: {'conectada' if connected else 'desconectada'}",
    )
    table.add_column("Jogador")
    table.add_column("Entrada / botões")
    table.add_column("Posição")
    table.add_column("Percentual", justify="right")
    table.add_column("Idade da leitura")

    if not state:
        for _ in range(2):
            table.add_row(
                "—",
                "—",
                "Aguardando leitura",
                "—",
                "—",
            )
        return table

    for reading in (state.player_1, state.player_2):
        origin = reading.tipo_entrada.value
        if isinstance(reading, LeituraJogadorBotoes):
            origin += f" subir={int(reading.subir)} descer={int(reading.descer)}"
        table.add_row(
            str(reading.player),
            origin,
            ProgressBar(total=100, completed=reading.percentage, width=24),
            f"{reading.percentage:.1f}%",
            f"{max(0, time() - reading.timestamp):.1f}s",
        )
    return table


async def run() -> None:
    settings = Settings()
    samples: SimpleQueue[PongState] = SimpleQueue()
    failure: BaseException | None = None

    def on_failure(error: BaseException) -> None:
        nonlocal failure
        failure = error

    source = make_input_source(
        settings,
        on_update=samples.put,
        on_failure=on_failure,
    )

    console = Console()
    if settings.input_mode == InputMode.ARDUINO_RASP:
        serial_player = 3 - settings.button_player
        serial_pin = settings.pot1_pin if serial_player == 1 else settings.pot2_pin
        console.print(
            f"Jogador {serial_player}: Arduino {serial_pin}; "
            f"jogador {settings.button_player}: "
            f"subir BCM {settings.button_up_pin}, descer BCM {settings.button_down_pin}"
        )
    else:
        console.print(f"Pinos: {settings.pot1_pin} / {settings.pot2_pin}", markup=False)
    console.print("Pressiona Ctrl+C para encerrar.", style="dim")
    try:
        await source.start()
        with Live(render_readings(None), console=console, auto_refresh=False) as live:
            latest: PongState | None = None
            while True:
                if failure is not None:
                    raise failure
                try:
                    while True:
                        latest = samples.get_nowait()
                except Empty:
                    pass
                live.update(render_readings(latest, await source.is_connected()), refresh=True)
                await asyncio.sleep(0.1)
    finally:
        await source.stop()


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        Console().print("Diagnóstico encerrado", style="green")


if __name__ == "__main__":
    main()
