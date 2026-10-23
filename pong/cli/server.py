import asyncio
import logging
import signal

from pong.api.app import make_app
from pong.api.websocket.connection_manager import ConnectionManager
from pong.config import Settings
from pong.domain.pong.state import PongState
from pong.infra.input.factory import make_input_source

logger = logging.getLogger(__name__)


async def run_server() -> None:
    settings = Settings()
    connection_manager = ConnectionManager()
    stop_event = asyncio.Event()
    event_loop = asyncio.get_running_loop()

    def on_paddle_update(state: PongState) -> None:
        connection_manager.broadcast_state(state)

    failure: BaseException | None = None

    def on_failure(error: BaseException) -> None:
        nonlocal failure
        failure = error
        logger.error("Falha na entrada: %s", error)
        stop_event.set()

    input_source = make_input_source(
        settings=settings,
        on_update=on_paddle_update,
        on_failure=on_failure,
    )

    app = make_app(connection_manager=connection_manager)
    http_server = app.listen(settings.server_port, address=settings.server_host)

    logger.info("=" * 70)
    logger.info("Pong Retrô Distribuído (Arduino + Tornado WebSockets)")
    logger.info("Servidor HTTP/WebSocket: %s:%s", settings.server_host, settings.server_port)
    logger.info("Potenciômetro 1: %s | Potenciômetro 2: %s", settings.pot1_pin, settings.pot2_pin)
    logger.info("Fonte de entrada: %s", type(input_source).__name__)
    logger.info("Acesse http://localhost:%s no navegador.", settings.server_port)
    logger.info("Pressione Ctrl+C para encerrar.")
    logger.info("=" * 70)

    signals = (signal.SIGINT, signal.SIGTERM)
    installed_signals: list[signal.Signals] = []
    try:
        for sig in signals:
            event_loop.add_signal_handler(sig, stop_event.set)
            installed_signals.append(sig)
        await input_source.start()
        await stop_event.wait()
    finally:
        try:
            http_server.stop()
            await input_source.stop()
        finally:
            connection_manager.close_all()
            await http_server.close_all_connections()
            for sig in installed_signals:
                event_loop.remove_signal_handler(sig)
        logger.info("Servidor finalizado.")
    if failure is not None:
        raise failure


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
