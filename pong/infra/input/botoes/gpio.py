from gpiozero import Button


class LeitorBotoesGPIO:
    """Botão entre GPIO BCM e GND, usando pull-up interno."""

    def __init__(self, pin: int, debounce: float) -> None:
        self._button = Button(pin, pull_up=True, bounce_time=debounce or None)

    @property
    def esta_pressionado(self) -> bool:
        # is_pressed é um alias criado dinamicamente pelo gpiozero para is_active.
        return bool(self._button.is_active)

    def fechar(self) -> None:
        self._button.close()
