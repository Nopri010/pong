from dataclasses import dataclass

from pong.domain.jogador import TipoEntradaJogador


@dataclass(frozen=True, slots=True)
class PotenciometroReading:
    potenciomentro_id: str
    player: int
    raw_value: float | None
    percentage: float
    timestamp: float
    tipo_entrada: TipoEntradaJogador = TipoEntradaJogador.POTENCIOMETRO
