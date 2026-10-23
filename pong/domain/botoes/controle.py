from math import isfinite


class ControleBotoes:
    """Posição percentual: subir diminui; descer aumenta."""

    def __init__(self, percentage: float, speed: float) -> None:
        if not isfinite(percentage) or not 0 <= percentage <= 100:
            raise ValueError("Posição inicial deve estar entre 0 e 100")
        if not isfinite(speed) or speed <= 0:
            raise ValueError("Velocidade deve ser finita e positiva")
        self.percentage = percentage
        self._speed = speed

    def avancar(self, subir: bool, descer: bool, segundos: float) -> float:
        if not isfinite(segundos) or segundos < 0:
            raise ValueError("Tempo decorrido deve ser finito e não negativo")
        direction = int(descer) - int(subir)
        self.percentage = min(100.0, max(0.0, self.percentage + direction * self._speed * segundos))
        return self.percentage
