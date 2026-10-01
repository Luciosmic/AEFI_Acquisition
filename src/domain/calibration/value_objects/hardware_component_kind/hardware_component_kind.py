"""
Hardware Component Kind Value Object

Responsibility:
- Name every kind of hardware component the bench is built from, and state,
  for each kind, the essential physical quantities that characterize it.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


@dataclass(frozen=True)
class QuantitySpec:
    """One characterizing quantity: a scalar, or — when `curve_x_label` is
    set — a curve y(x) given as (x, y) points (e.g. rate vs n_avg)."""

    key: str
    label: str
    unit: str
    curve_x_label: Optional[str] = None

    @property
    def is_curve(self) -> bool:
        return self.curve_x_label is not None


class HardwareComponentKind(Enum):
    SENSOR = "sensor"
    CONDITIONING_ELECTRONICS_BOARD = "conditioning_electronics_board"
    EXCITATION_ELECTRONICS_BOARD = "excitation_electronics_board"
    SIGNAL_GENERATION_CHIP = "signal_generation_chip"
    ADC = "adc"
    MICROCONTROLLER = "microcontroller"
    MOTORS = "motors"

    @property
    def label(self) -> str:
        return _LABELS[self]

    @property
    def quantities(self) -> Tuple[QuantitySpec, ...]:
        return _QUANTITIES[self]


_LABELS = {
    HardwareComponentKind.SENSOR: "Capteur",
    HardwareComponentKind.CONDITIONING_ELECTRONICS_BOARD: "Carte électronique de conditionnement",
    HardwareComponentKind.EXCITATION_ELECTRONICS_BOARD: "Carte électronique d'excitation",
    HardwareComponentKind.SIGNAL_GENERATION_CHIP: "Chip de génération des signaux",
    HardwareComponentKind.ADC: "ADC",
    HardwareComponentKind.MICROCONTROLLER: "Microcontrôleur",
    HardwareComponentKind.MOTORS: "Moteurs",
}

# The essential physical quantities per kind — edit here to add/remove one.
# Keys are persisted: renaming a key orphans already-recorded values.
_QUANTITIES = {
    HardwareComponentKind.SENSOR: (
        QuantitySpec("transduction_gain_v_per_v_per_m", "Gain de transduction", "V/(V/m)"),
    ),
    HardwareComponentKind.CONDITIONING_ELECTRONICS_BOARD: (
        QuantitySpec("gain", "Gain", "V/V"),
        QuantitySpec("bandwidth_hz", "Bande passante (-3 dB)", "Hz"),
        QuantitySpec("noise_density_v_per_sqrt_hz", "Niveau de bruit", "V/√Hz"),
    ),
    HardwareComponentKind.EXCITATION_ELECTRONICS_BOARD: (
        QuantitySpec("gain", "Gain", "V/V"),
        QuantitySpec("bandwidth_hz", "Bande passante (-3 dB)", "Hz"),
    ),
    HardwareComponentKind.SIGNAL_GENERATION_CHIP: (
        QuantitySpec("gain_value_per_v", "Gain", "value/V"),
        QuantitySpec("saturation_v", "Saturation", "V"),
        QuantitySpec("bandwidth_hz", "Bande passante (-3 dB)", "Hz"),
    ),
    HardwareComponentKind.ADC: (
        QuantitySpec("full_scale_v", "Pleine échelle", "V"),
        QuantitySpec("lsb_v", "Quantum", "V/LSB"),
        QuantitySpec("noise_v_rms", "Bruit", "V RMS"),
        QuantitySpec("max_sampling_rate_hz", "Fréquence d'échantillonnage max", "Hz"),
    ),
    HardwareComponentKind.MICROCONTROLLER: (
        QuantitySpec("max_acquisition_rate_per_s", "Débit d'acquisition max", "mesures/s"),
        QuantitySpec(
            "optimal_acquisition_rate_per_s", "Débit d'acquisition optimal", "mesures/s", curve_x_label="n_avg"
        ),
    ),
    HardwareComponentKind.MOTORS: (
        QuantitySpec("step_um", "Pas", "µm/pas"),
        QuantitySpec("max_speed_mm_per_s", "Vitesse max", "mm/s"),
        QuantitySpec("acceleration_mm_per_s2", "Accélération", "mm/s²"),
    ),
}
