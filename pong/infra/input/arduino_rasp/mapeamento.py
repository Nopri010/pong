from dataclasses import dataclass

from pong.config import Settings
from pong.domain.potenciometro.entity import Potenciometro


@dataclass(frozen=True, slots=True)
class MapeamentoArduinoRasp:
    button_player: int
    potenciometro: Potenciometro


def resolver_mapeamento_arduino_rasp(settings: Settings) -> MapeamentoArduinoRasp:
    player = 3 - settings.button_player
    pin = settings.pot1_pin if player == 1 else settings.pot2_pin
    return MapeamentoArduinoRasp(
        settings.button_player,
        Potenciometro.config(identifier=f"player{player}", player=player, pin=pin),
    )
