"""AefiSignalCorrectionCalibration value object (see aefi_signal_correction_calibration_intention.md)."""

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass(frozen=True)
class AefiSignalCorrectionCalibration:
    """Immutable snapshot of the three signal correction stages (noise, phase,
    primary field), keyed by axis ("x"/"y"/"z"). Replaces the mutable
    ProcessingState previously held by interface/presenters/signal_processor.py."""

    # Noise offset (zero) — {axis: (in_phase, quadrature)}
    noise_offset: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    noise_correction_enabled: bool = False

    # Phase correction — {axis: radians}
    phase_angles: Dict[str, float] = field(default_factory=dict)
    phase_correction_enabled: bool = False

    # Primary field offset (tare) — {axis: (in_phase, quadrature)}
    primary_offset: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    primary_correction_enabled: bool = False
