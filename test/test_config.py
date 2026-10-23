import pytest
from pydantic import ValidationError

from pong.config import Settings


@pytest.mark.parametrize(
    "values",
    [
        {"input_mode": "invalid"},
        {"input_mode": "arduino_rasp"},
        {"input_mode": "arduino_rasp", "button_up_pin": 17},
        {"input_mode": "arduino_rasp", "button_up_pin": 17, "button_down_pin": 17},
        {"button_player": 3},
        {"button_up_pin": -1},
        {"button_down_pin": 28},
        {"button_poll_interval_seconds": 0},
        {"button_speed_percent_per_second": 0},
        {"button_debounce_seconds": -1},
        {"button_initial_percentage": 101},
        {"button_speed_percent_per_second": float("inf")},
    ],
)
def test_invalid_button_settings(isolated_settings_environment, values):
    with pytest.raises(ValidationError):
        Settings(**values)


def test_hybrid_settings_from_environment(isolated_settings_environment, monkeypatch):
    for key, value in {
        "INPUT_MODE": "arduino_rasp",
        "BUTTON_PLAYER": "2",
        "BUTTON_UP_PIN": "17",
        "BUTTON_DOWN_PIN": "27",
    }.items():
        monkeypatch.setenv("PONG_" + key, value)
    settings = Settings()
    assert settings.button_player == 2
    assert settings.button_up_pin == 17
    assert settings.button_down_pin == 27


def test_settings_use_declared_defaults(isolated_settings_environment: None) -> None:
    settings = Settings()

    assert settings.serial_baudrate == 115200
    assert settings.serial_timeout_seconds == 1.0
    assert settings.pot1_pin == "A0"
    assert settings.pot2_pin == "A1"
    assert settings.server_host == "0.0.0.0"
    assert settings.server_port == 8888


@pytest.mark.parametrize(
    ("environment_name", "environment_value", "attribute", "expected"),
    [
        ("PONG_SERIAL_BAUDRATE", "9600", "serial_baudrate", 9600),
        ("PONG_POT1_PIN", "A2", "pot1_pin", "A2"),
        ("PONG_SERVER_PORT", "9000", "server_port", 9000),
    ],
)
def test_settings_read_prefixed_environment(
    isolated_settings_environment: None,
    monkeypatch: pytest.MonkeyPatch,
    environment_name: str,
    environment_value: str,
    attribute: str,
    expected: object,
) -> None:
    monkeypatch.setenv(environment_name, environment_value)

    settings = Settings()

    assert getattr(settings, attribute) == expected


@pytest.mark.parametrize("field", ["server_port", "serial_baudrate"])
def test_settings_reject_non_positive_values(
    isolated_settings_environment: None,
    field: str,
) -> None:
    with pytest.raises(ValidationError):
        Settings(**{field: 0})
