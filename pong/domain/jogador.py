from enum import StrEnum
from typing import Protocol


class TipoEntradaJogador(StrEnum):
    POTENCIOMETRO = "potenciometro"
    BOTOES = "botoes"


class LeituraJogador(Protocol):
    @property
    def player(self) -> int: ...

    @property
    def percentage(self) -> float: ...

    @property
    def timestamp(self) -> float: ...

    @property
    def tipo_entrada(self) -> TipoEntradaJogador: ...
