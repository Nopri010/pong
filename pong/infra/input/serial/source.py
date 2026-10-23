import asyncio
from collections.abc import Callable
from logging import getLogger
from time import time

from serial import Serial, SerialException
from serial_asyncio import open_serial_connection

from pong.config import Settings
from pong.infra.input.serial.frame import SerialPotentiometerFrame
from pong.infra.input.serial.parser import PotStreamParser

logger = getLogger(__name__)


class SerialInputSource:
    def __init__(
        self,
        settings: Settings,
        on_update: Callable[[SerialPotentiometerFrame], None],
    ) -> None:
        self._settings = settings
        self._on_update = on_update

        self._connected = False
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._task = asyncio.create_task(self._run_loop(), name="SerialInputSourceTask")
        logger.info("Fonte serial iniciada na porta %s", self._settings.serial_port)

    async def stop(self) -> None:
        task = self._task
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        self._connected = False
        self._task = None
        logger.info("Fonte serial finalizada")

    async def is_connected(self) -> bool:
        return self._connected

    async def _run_loop(self) -> None:
        while True:
            try:
                await self._read_connection()
            except (SerialException, OSError) as err:
                logger.error("%s", err)
            finally:
                self._connected = False
            await asyncio.sleep(self._settings.serial_reconnect_delay_seconds)

    async def _read_connection(self) -> None:
        logger.info(
            "Conectado à porta serial %s a %s bps",
            self._settings.serial_port,
            self._settings.serial_baudrate,
        )
        reader, writer = await open_serial_connection(
            url=self._settings.serial_port, baudrate=self._settings.serial_baudrate
        )
        try:
            await asyncio.sleep(self._settings.serial_startup_delay_seconds)
            conn: Serial = writer.transport.get_extra_info("serial")
            conn.reset_input_buffer()
            self._connected = True
            logger.info("Conexão serial estabelecida!")
            await self._consume_connection(reader)
        finally:
            self._connected = False
            writer.close()
            await writer.wait_closed()

    async def _consume_connection(self, reader: asyncio.StreamReader) -> None:
        parser = PotStreamParser()
        while True:
            try:
                line_bytes = await asyncio.wait_for(
                    reader.readline(),
                    timeout=self._settings.serial_timeout_seconds,
                )
            except TimeoutError:
                continue

            if not line_bytes:
                raise OSError("Conexão serial encerrada (EOF)")
            line = line_bytes.decode("ascii", errors="replace").strip()
            if not line:
                continue
            percentuais = parser.feed_line(line)
            if percentuais:
                self._on_update(SerialPotentiometerFrame(*percentuais, timestamp=time()))
