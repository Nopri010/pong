from typing import Protocol


class LeitorBotoesProtocol(Protocol):
    @property
    def esta_pressionado(self) -> bool: ...

    def fechar(self) -> None: ...
