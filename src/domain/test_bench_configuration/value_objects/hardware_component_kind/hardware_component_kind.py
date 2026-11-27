"""
Hardware Component Kind Value Object

Responsibility:
- Name every kind of hardware component the bench is built from, and state,
  for each kind, the essential physical quantities that characterize it.
- State which kinds together form one hardware assembly of the bench, in the
  language of the thesis graph (the digital-analog-signals-processing-unit).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


@dataclass(frozen=True)
class QuantitySpec:
    """One characterizing quantity: a scalar, or — when `curve_x_label` is
    set — a curve y(x) given as (x, y) points (e.g. rate vs n_avg).
    `allowed_values` set = the scalar may only take one of these values
    (e.g. a sign, -1 or +1); unset = any scalar > 0."""

    key: str
    label: str
    unit: str
    curve_x_label: Optional[str] = None
    allowed_values: Optional[Tuple[float, ...]] = None

    @property
    def is_curve(self) -> bool:
        return self.curve_x_label is not None


class HardwareAssembly(Enum):
    """A part of the bench made of several component kinds. Names follow the
    thesis graph: `digital-analog-signals-processing-unit` is its reference
    key, "unité de conversion entre signaux numériques et analogiques" its
    French name — the ADC, the DDS and the microcontroller of a detection,
    whose other part is the conditioning board."""

    DIGITAL_ANALOG_SIGNALS_PROCESSING_UNIT = "digital_analog_signals_processing_unit"

    @property
    def label(self) -> str:
        return _ASSEMBLY_LABELS[self]


_ASSEMBLY_LABELS = {
    HardwareAssembly.DIGITAL_ANALOG_SIGNALS_PROCESSING_UNIT: "Unité de conversion entre signaux numériques et analogiques",
}


class HardwareComponentKind(Enum):
    SENSOR = "sensor"
    CONDITIONING_ELECTRONICS_BOARD = "conditioning_electronics_board"
    EXCITATION_ELECTRONICS_BOARD = "excitation_electronics_board"
    SIGNAL_GENERATION_CHIP = "signal_generation_chip"
    ADC = "adc"
    MICROCONTROLLER = "microcontroller"
    MOTORS = "motors"
    STEPPER_DRIVER = "stepper_driver"

    @property
    def label(self) -> str:
        return _LABELS[self]

    @property
    def quantities(self) -> Tuple[QuantitySpec, ...]:
        return _QUANTITIES[self]

    @property
    def assembly(self) -> Optional[HardwareAssembly]:
        """The assembly this kind is part of, or None if it stands alone."""
        return _ASSEMBLIES.get(self)


_LABELS = {
    HardwareComponentKind.SENSOR: "Capteur",
    HardwareComponentKind.CONDITIONING_ELECTRONICS_BOARD: "Carte électronique de conditionnement",
    HardwareComponentKind.EXCITATION_ELECTRONICS_BOARD: "Amplification de l'excitation",
    HardwareComponentKind.SIGNAL_GENERATION_CHIP: "Génération des signaux d'excitation",
    HardwareComponentKind.ADC: "Convertisseur Analogique Numérique",
    HardwareComponentKind.MICROCONTROLLER: "Microcontrôleur",
    HardwareComponentKind.MOTORS: "Moteurs",
    HardwareComponentKind.STEPPER_DRIVER: "Driver pas à pas",
}

# Thesis graph: the unit groups the ADC, the DDS (signal generation chip) and
# the microcontroller; the conditioning board is the other part of a detection.
_ASSEMBLIES = {
    HardwareComponentKind.SIGNAL_GENERATION_CHIP: HardwareAssembly.DIGITAL_ANALOG_SIGNALS_PROCESSING_UNIT,
    HardwareComponentKind.ADC: HardwareAssembly.DIGITAL_ANALOG_SIGNALS_PROCESSING_UNIT,
    HardwareComponentKind.MICROCONTROLLER: HardwareAssembly.DIGITAL_ANALOG_SIGNALS_PROCESSING_UNIT,
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
        # -1: the board outputs its quadrature channels with P and N swapped
        # (routing without crossing), so the ADC reads -Q (found 2026-11-27).
        QuantitySpec(
            "quadrature_output_sign",
            "Signe de la voie en quadrature (+1 ou -1)",
            "±1",
            allowed_values=(-1.0, 1.0),
        ),
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
        # Measured on DRDY at the oscilloscope (Calibration -> ADC tab).
        QuantitySpec("modulator_frequency_hz", "Fréquence du modulateur f_MOD (DRDY)", "Hz"),
        QuantitySpec("output_data_rate_hz", "Cadence de sortie ODR (DRDY)", "Hz", curve_x_label="OSR"),
    ),
    HardwareComponentKind.MICROCONTROLLER: (
        QuantitySpec("max_acquisition_rate_per_s", "Débit d'acquisition max", "mesures/s"),
        QuantitySpec(
            "optimal_acquisition_rate_per_s", "Débit d'acquisition optimal", "mesures/s", curve_x_label="n_avg"
        ),
    ),
    # The motor alone: its distance per pulse depends on the whole chain
    # (driver microstepping, mechanics) and is characterized per pulse — see
    # MechanicalTransmissionCalibrationEntry.
    HardwareComponentKind.MOTORS: (
        QuantitySpec("rated_current_a", "Courant nominal", "A"),
    ),
    # Product limit only; the current actually set is part of the transmission.
    HardwareComponentKind.STEPPER_DRIVER: (
        QuantitySpec("max_current_a", "Courant max", "A"),
    ),
}
