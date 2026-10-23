from dataclasses import dataclass

from pong.domain.jogador import TipoEntradaJogador


@dataclass(frozen=True, slots=True)
class LeituraJogadorBotoes:
    player: int
    percentage: float
    timestamp: float
    subir: bool = False
    descer: bool = False
    tipo_entrada: TipoEntradaJogador = TipoEntradaJogador.BOTOES
