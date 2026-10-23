import signal
from types import SimpleNamespace

import pytest

from pong.cli import server as server_module


class FakeLoop:
    def __init__(self) -> None:
        self.callbacks = {}
        self.removed_signals = []

    def add_signal_handler(self, sig, callback) -> None:
        self.callbacks[sig] = callback
        if sig == signal.SIGTERM:
            callback()

    def remove_signal_handler(self, sig) -> None:
        self.removed_signals.append(sig)


class FakeHTTPServer:
    def __init__(self) -> None:
        self.stop_called = False
        self.close_called = False

    def stop(self) -> None:
        self.stop_called = True

    async def close_all_connections(self) -> None:
        self.close_called = True


class FakeApp:
    def __init__(self, http_server: FakeHTTPServer) -> None:
        self.http_server = http_server
        self.listen_arguments = None

    def listen(self, port: int, address: str) -> FakeHTTPServer:
        self.listen_arguments = (port, address)
        return self.http_server


class FakeInputSource:
    instance = None

    def __init__(self, settings, on_update, on_failure) -> None:
        self.settings = settings
        self.on_failure = on_failure
        self.on_update = on_update
        self.start_called = False
        self.stop_called = False
        FakeInputSource.instance = self
        self.on_update = on_update

    async def start(self) -> None:
        self.start_called = True
        self.on_update(object())

    async def stop(self) -> None:
        self.stop_called = True


@pytest.mark.asyncio
@pytest.mark.parametrize("fail", [False, True])
async def test_run_server_starts_and_stops_components(
    monkeypatch: pytest.MonkeyPatch, fail: bool
) -> None:
    settings = SimpleNamespace(
        pot1_pin="A0",
        pot2_pin="A1",
        server_host="127.0.0.1",
        server_port=9999,
    )
    fake_loop = FakeLoop()
    fake_http_server = FakeHTTPServer()
    fake_app = FakeApp(fake_http_server)

    class FakeConnectionManager:
        def broadcast_state(self, _state) -> None:
            return None

        def close_all(self):
            return None

    class Source(FakeInputSource):
        async def start(self):
            await super().start()
            if fail:
                self.on_failure(OSError("falha GPIO"))

    monkeypatch.setattr(server_module, "Settings", lambda: settings)
    monkeypatch.setattr(server_module, "make_app", lambda connection_manager: fake_app)
    monkeypatch.setattr(server_module, "make_input_source", Source)
    monkeypatch.setattr(server_module, "ConnectionManager", FakeConnectionManager)
    monkeypatch.setattr(server_module.asyncio, "get_running_loop", lambda: fake_loop)

    if fail:
        with pytest.raises(OSError, match="falha GPIO"):
            await server_module.run_server()
    else:
        await server_module.run_server()

    assert fake_app.listen_arguments == (9999, "127.0.0.1")
    assert FakeInputSource.instance is not None
    assert FakeInputSource.instance.start_called is True
    assert FakeInputSource.instance.stop_called is True
    assert fake_http_server.stop_called is True
    assert fake_http_server.close_called is True
    assert fake_loop.removed_signals == [signal.SIGINT, signal.SIGTERM]


def test_main_configures_logging_and_runs_server(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    async def fake_run_server() -> None:
        return None

    def fake_asyncio_run(coroutine) -> None:
        calls.append(coroutine)
        coroutine.close()

    monkeypatch.setattr(server_module, "run_server", fake_run_server)
    monkeypatch.setattr(server_module.asyncio, "run", fake_asyncio_run)

    server_module.main()

    assert len(calls) == 1
