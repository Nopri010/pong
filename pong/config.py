from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class InputMode(StrEnum):
    ARDUINO = "arduino"
    ARDUINO_RASP = "arduino_rasp"


class Settings(BaseSettings):
    """Configurações declarativas carregadas do ambiente ou de um arquivo .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="PONG_",
        extra="ignore",
        allow_inf_nan=False,
    )

    input_mode: InputMode = InputMode.ARDUINO
    button_player: int = Field(default=1, ge=1, le=2)
    button_up_pin: int | None = Field(default=None, ge=0, le=27)
    button_down_pin: int | None = Field(default=None, ge=0, le=27)
    button_poll_interval_seconds: float = Field(default=0.02, gt=0)
    button_speed_percent_per_second: float = Field(default=160.0, gt=0)
    button_debounce_seconds: float = Field(default=0.05, ge=0)
    button_initial_percentage: float = Field(default=50.0, ge=0, le=100)

    @model_validator(mode="after")
    def validate_hybrid_pins(self) -> Self:
        if self.input_mode == InputMode.ARDUINO_RASP:
            if self.button_up_pin is None or self.button_down_pin is None:
                raise ValueError("Modo híbrido exige BUTTON_UP_PIN e BUTTON_DOWN_PIN (BCM)")
            if self.button_up_pin == self.button_down_pin:
                raise ValueError("Os GPIOs de subir e descer devem ser diferentes")
        return self

    serial_port: str | None = Field(
        default=None,
        description="Porta serial USB configurada explicitamente no ambiente",
    )
    serial_baudrate: int = Field(
        default=115200,
        description="Velocidade da porta serial em bps",
        gt=0,
    )
    serial_timeout_seconds: float = Field(
        default=1.0,
        description="Tempo máximo para aguardar uma linha serial",
        gt=0.0,
    )
    serial_startup_delay_seconds: float = Field(
        default=2.0,
        description="Tempo de estabilização após abrir a porta serial",
        ge=0.0,
    )
    serial_reconnect_delay_seconds: float = Field(
        default=2.0,
        description="Intervalo entre tentativas de conexão serial",
        ge=0.0,
    )

    pot1_pin: str = Field(
        default="A0",
        description="Identificador do pino do Potenciômetro 1 (Jogador 1 - Esquerda)",
        min_length=1,
    )
    pot2_pin: str = Field(
        default="A1",
        description="Identificador do pino do Potenciômetro 2 (Jogador 2 - Direita)",
        min_length=1,
    )

    server_host: str = Field(
        default="0.0.0.0",
        description="Endereço de bind do servidor Tornado",
        min_length=1,
    )
    server_port: int = Field(
        default=8888,
        description="Porta TCP para o servidor HTTP/WebSocket",
        ge=1,
        le=65535,
    )
