import asyncio

import pytest

from pong.config import InputMode, Settings
from pong.domain.botoes.leitura import LeituraJogadorBotoes
from pong.infra.input.arduino_rasp.composicao import CompositorEstadoArduinoRasp
from pong.infra.input.arduino_rasp.mapeamento import resolver_mapeamento_arduino_rasp
from pong.infra.input.arduino_rasp.monitor_botoes import MonitorBotoes
from pong.infra.input.arduino_rasp.source import ArduinoRaspInputSource
from pong.infra.input.serial.frame import SerialPotentiometerFrame


@pytest.fixture
def hybrid_settings(settings):
    return Settings(
        **(
            settings.model_dump()
            | {
                "input_mode": InputMode.ARDUINO_RASP,
                "button_player": 2,
                "button_up_pin": 17,
                "button_down_pin": 27,
            }
        )
    )


class FakeButton:
    esta_pressionado = False
    closed = False

    def fechar(self):
        self.closed = True


class FakeSerial:
    started = False
    stopped = False

    async def start(self):
        self.started = True
        self.stopped = False

    async def stop(self):
        self.stopped = True

    async def is_connected(self):
        return self.started and not self.stopped


@pytest.mark.parametrize("player,expected", [(1, (60, 80)), (2, (20, 60))])
def test_mapping_preserves_only_complementary_channel(hybrid_settings, player, expected):
    hybrid_settings.button_player = player
    mapping = resolver_mapeamento_arduino_rasp(hybrid_settings)
    composer = CompositorEstadoArduinoRasp(mapping)
    state = composer.compor(
        SerialPotentiometerFrame(20, 80, 10), LeituraJogadorBotoes(player, 60, 11), 12
    )
    assert (state.player1_pct, state.player2_pct) == expected
    assert state.timestamp == 12
    serial_reading = state.player_2 if player == 1 else state.player_1
    assert serial_reading.timestamp == 10
    with pytest.raises(ValueError):
        composer.compor(
            SerialPotentiometerFrame(0, 0, 10), LeituraJogadorBotoes(3 - player, 60, 11), 12
        )


async def test_monitor_hold_release_idle_and_cleanup(hybrid_settings):
    up, down = FakeButton(), FakeButton()
    readers = iter([up, down])
    updates = []
    monitor = MonitorBotoes(
        hybrid_settings,
        updates.append,
        lambda error: None,
        reader_factory=lambda pin, debounce: next(readers),
    )
    await monitor.start()
    task = monitor._task
    await monitor.start()
    assert monitor._task is task
    monitor.amostrar(0.1)
    assert updates == []
    up.esta_pressionado = True
    monitor.amostrar(0.1)
    assert updates[-1].percentage == 34
    monitor.amostrar(0.1)
    assert updates[-1].percentage == 18
    up.esta_pressionado = False
    monitor.amostrar(0.1)
    assert updates[-1].percentage == 18
    count = len(updates)
    monitor.amostrar(0.1)
    assert len(updates) == count
    await monitor.stop()
    await monitor.stop()
    assert task.done() and up.closed and down.closed


async def test_monitor_partial_start_closes_first_button(hybrid_settings):
    up = FakeButton()

    def create(pin, debounce):
        if pin == 27:
            raise OSError("GPIO indisponível")
        return up

    monitor = MonitorBotoes(
        hybrid_settings, lambda state: None, lambda error: None, reader_factory=create
    )
    with pytest.raises(OSError):
        await monitor.start()
    assert up.closed
    await monitor.stop()


async def test_source_waits_for_serial_and_ignores_removed_pot(hybrid_settings):
    updates = []
    source = ArduinoRaspInputSource(hybrid_settings, updates.append, lambda error: None)
    source._serial = FakeSerial()
    buttons = [FakeButton(), FakeButton()]
    readers = iter(buttons)
    source._monitor._reader_factory = lambda pin, debounce: next(readers)
    await source.stop()
    await source.start()
    await source.start()
    assert await source.is_connected()
    source._receive_buttons(LeituraJogadorBotoes(2, 70, 1))
    assert not updates
    source._receive_serial(SerialPotentiometerFrame(25, 99, 2))
    assert (updates[-1].player1_pct, updates[-1].player2_pct) == (25, 70)
    source._receive_serial(SerialPotentiometerFrame(25, 0, 3))
    assert updates[-1].player2_pct == 70
    source._receive_buttons(LeituraJogadorBotoes(2, 60, 4, True, False))
    assert updates[-1].player2_pct == 60
    await source.stop()
    assert not await source.is_connected()
    assert all(button.closed for button in buttons)


async def test_monitor_task_failure_reports_error(hybrid_settings):
    failures = []
    monitor = MonitorBotoes(
        hybrid_settings,
        lambda state: None,
        failures.append,
        reader_factory=lambda pin, debounce: FakeButton(),
    )

    def fail(seconds):
        raise OSError("GPIO desconectado")

    monitor.amostrar = fail
    await monitor.start()
    with pytest.raises(OSError, match="GPIO desconectado"):
        await asyncio.wait_for(asyncio.shield(monitor._task), 1)
    assert str(failures[0]) == "GPIO desconectado"
    await monitor.stop()


async def test_source_partial_start_releases_gpio_and_serial(hybrid_settings):
    source = ArduinoRaspInputSource(hybrid_settings, lambda state: None, lambda error: None)
    buttons = [FakeButton(), FakeButton()]
    readers = iter(buttons)
    source._monitor._reader_factory = lambda pin, debounce: next(readers)

    class FailingSerial(FakeSerial):
        async def start(self):
            raise OSError("porta ocupada")

    serial = FailingSerial()
    source._serial = serial
    with pytest.raises(OSError):
        await source.start()
    assert serial.stopped and all(button.closed for button in buttons)


async def test_monitor_uses_elapsed_monotonic_time(hybrid_settings, monkeypatch):
    up = FakeButton()
    up.esta_pressionado = True
    readers = iter([up, FakeButton()])
    updates = []
    monitor = MonitorBotoes(
        hybrid_settings,
        updates.append,
        lambda error: None,
        reader_factory=lambda pin, debounce: next(readers),
    )
    clock = iter([10, 10.1, 10.3])
    monkeypatch.setattr(
        "pong.infra.input.arduino_rasp.monitor_botoes.monotonic", lambda: next(clock)
    )
    count = 0

    async def tick(delay):
        nonlocal count
        count += 1
        if count == 3:
            raise asyncio.CancelledError

    await monitor.start()
    monkeypatch.setattr("pong.infra.input.arduino_rasp.monitor_botoes.asyncio.sleep", tick)
    with pytest.raises(asyncio.CancelledError):
        await monitor._task
    assert [reading.percentage for reading in updates] == pytest.approx([34, 2])
    await monitor.stop()


async def test_missing_pins_and_sampling_before_start(settings):
    monitor = MonitorBotoes(settings, lambda state: None, lambda error: None)
    monitor.amostrar(1)
    with pytest.raises(ValueError):
        await monitor.start()
    await monitor.stop()
