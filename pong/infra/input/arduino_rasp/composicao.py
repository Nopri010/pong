from pong.domain.botoes.leitura import LeituraJogadorBotoes
from pong.domain.pong.state import PongState
from pong.infra.input.arduino_rasp.mapeamento import MapeamentoArduinoRasp
from pong.infra.input.serial.frame import SerialPotentiometerFrame


class CompositorEstadoArduinoRasp:
    def __init__(self, mapping: MapeamentoArduinoRasp) -> None:
        if mapping.potenciometro.player != 3 - mapping.button_player:
            raise ValueError("Potenciômetro deve controlar o oponente dos botões")
        self._mapping = mapping

    def compor(
        self, frame: SerialPotentiometerFrame, buttons: LeituraJogadorBotoes, timestamp: float
    ) -> PongState:
        if buttons.player != self._mapping.button_player:
            raise ValueError("Leitura dos botões pertence ao jogador errado")
        pot = self._mapping.potenciometro
        percentage = frame.channel_1_percentage if pot.player == 1 else frame.channel_2_percentage
        reading = pot.reading_from_percentage(percentage, frame.timestamp)
        if buttons.player == 1:
            return PongState(buttons, reading, timestamp)
        return PongState(reading, buttons, timestamp)
