from dataclasses import dataclass

from pong.domain.jogador import LeituraJogador


@dataclass(frozen=True, slots=True)
class PongState:
    player_1: LeituraJogador
    player_2: LeituraJogador
    timestamp: float

    @property
    def player1_pos(self) -> int:
        return self.player_1.player

    @property
    def player2_pos(self) -> int:
        return self.player_2.player

    @property
    def player1_pct(self) -> float:
        return self.player_1.percentage

    @property
    def player2_pct(self) -> float:
        return self.player_2.percentage
