import asyncio
from collections.abc import Iterator

import pytest

import pong.infra.input.serial.source as source_module
from pong.infra.input.serial.frame import SerialPotentiometerFrame
from pong.infra.input.serial.source import SerialInputSource


class FakeSerial:
    def __init__(self) -> None:
        self.reset_called = False

    def reset_input_buffer(self) -> None:
        self.reset_called = True


class FakeTransport:
    def __init__(self, serial: FakeSerial) -> None:
        self._serial = serial

    def get_extra_info(self, name: str) -> FakeSerial | None:
        return self._serial if name == "serial" else None


class FakeWriter:
    def __init__(self, serial: FakeSerial) -> None:
        self.transport = FakeTransport(serial)
        self.closed = False
        self.wait_closed_called = False

    def close(self) -> None:
        self.closed = True

    async def wait_closed(self) -> None:
        self.wait_closed_called = True


class FakeReader:
    def __init__(self, lines: list[bytes]) -> None:
        self._lines: Iterator[bytes] = iter(lines)

    async def readline(self) -> bytes:
        try:
            return next(self._lines)
        except StopIteration:
            raise asyncio.CancelledError from None


async def test_eof_requests_reconnection(settings):
    source = SerialInputSource(settings, lambda frame: None)
    with pytest.raises(OSError, match="EOF"):
        await source._consume_connection(FakeReader([b""]))


@pytest.mark.asyncio
async def test_start_is_idempotent_and_stop_cancels_task(
    settings,
    potentiometers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = SerialInputSource(settings, lambda _state: None)
    running = asyncio.Event()

    async def fake_run_loop() -> None:
        await running.wait()

    monkeypatch.setattr(source, "_run_loop", fake_run_loop)

    await source.start()
    first_task = source._task
    await source.start()

    assert first_task is not None
    assert source._task is first_task

    await source.stop()

    assert first_task.done()


@pytest.mark.asyncio
async def test_stop_without_start_is_safe(settings, potentiometers) -> None:
    source = SerialInputSource(settings, lambda _state: None)

    await source.stop()

    assert await source.is_connected() is False


@pytest.mark.asyncio
async def test_read_connection_consumes_serial_values_and_closes_writer(
    settings,
    potentiometers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    updates: list[SerialPotentiometerFrame] = []
    source = SerialInputSource(settings, updates.append)
    serial = FakeSerial()
    writer = FakeWriter(serial)
    reader = FakeReader([b"0\n", b";\n", b"1023\n"])

    async def fake_open_serial_connection(**_kwargs):
        return reader, writer

    monkeypatch.setattr(source_module, "open_serial_connection", fake_open_serial_connection)

    with pytest.raises(asyncio.CancelledError):
        await source._read_connection()

    assert len(updates) == 1
    assert updates[0].channel_1_percentage == 0.0
    assert updates[0].channel_2_percentage == 100.0
    assert serial.reset_called is True
    assert writer.closed is True
    assert writer.wait_closed_called is True
    assert await source.is_connected() is False


@pytest.mark.asyncio
async def test_run_loop_reconnects_after_serial_error(
    settings,
    potentiometers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = SerialInputSource(settings, lambda _state: None)
    attempts = 0

    async def fake_read_connection() -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise OSError("porta indisponível")
        raise asyncio.CancelledError

    monkeypatch.setattr(source, "_read_connection", fake_read_connection)

    with pytest.raises(asyncio.CancelledError):
        await source._run_loop()

    assert attempts == 2
    assert await source.is_connected() is False


@pytest.mark.asyncio
async def test_consume_connection_ignores_timeout_and_empty_lines(
    settings,
    potentiometers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    updates: list[SerialPotentiometerFrame] = []
    source = SerialInputSource(settings, updates.append)
    outcomes = iter([TimeoutError(), b"\n", b"0\n", b";\n", b"1023\n"])

    class FakeReader:
        async def readline(self) -> bytes:
            return b""

    async def fake_wait_for(awaitable, timeout):
        del timeout
        awaitable.close()
        try:
            outcome = next(outcomes)
        except StopIteration:
            raise asyncio.CancelledError from None
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    monkeypatch.setattr(source_module.asyncio, "wait_for", fake_wait_for)

    with pytest.raises(asyncio.CancelledError):
        await source._consume_connection(FakeReader())

    assert len(updates) == 1
    assert updates[0].channel_1_percentage == 0.0
    assert updates[0].channel_2_percentage == 100.0
