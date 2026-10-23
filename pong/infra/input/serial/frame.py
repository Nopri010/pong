from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SerialPotentiometerFrame:
    channel_1_percentage: float
    channel_2_percentage: float
    timestamp: float
