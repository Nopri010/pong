import json
import logging

from pong.api.websocket.connection_manager import ConnectionManager


class FakeClient:
    def __init__(self, should_fail: bool = False) -> None:
        self.messages: list[str] = []
        self._should_fail = should_fail

    def write_message(self, payload: str) -> None:
        if self._should_fail:
            raise RuntimeError("cliente indisponível")
        self.messages.append(payload)


def test_manager_adds_and_removes_clients() -> None:
    manager = ConnectionManager()
    first = FakeClient()
    second = FakeClient()

    assert manager.add(first) == 1
    assert manager.add(second) == 2
    manager.remove(first)
    manager.remove(first)

    assert manager.client_count == 1


def test_manager_broadcasts_to_all_clients(pong_state) -> None:
    manager = ConnectionManager()
    first = FakeClient()
    second = FakeClient()
    manager.add(first)
    manager.add(second)

    manager.broadcast_state(pong_state)

    assert json.loads(first.messages[0])["type"] == "paddle_update"
    assert first.messages == second.messages


def test_manager_removes_failed_clients_and_logs(caplog, pong_state) -> None:
    manager = ConnectionManager()
    working = FakeClient()
    failing = FakeClient(should_fail=True)
    manager.add(working)
    manager.add(failing)

    with caplog.at_level(logging.ERROR, logger="pong.api.websocket.connection_manager"):
        manager.broadcast_state(pong_state)

    assert manager.client_count == 1
    assert len(working.messages) == 1
    assert "cliente indisponível" in caplog.text


def test_close_all_releases_websockets():
    class Client:
        closed = False

        def close(self):
            self.closed = True

    manager = ConnectionManager()
    client = Client()
    manager.add(client)
    manager.close_all()
    assert client.closed
    assert manager.client_count == 0
