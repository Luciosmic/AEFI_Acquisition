"""
View model of the "Transmission" tab of the Calibration panel.

See mechanical_transmission_view_model_intention.md.
"""

from dataclasses import dataclass
from typing import Optional


def _french(value: float) -> str:
    return f"{value:g}".replace(".", ",")


@dataclass(frozen=True)
class MechanicalTransmissionViewModel:
    is_recorded: bool
    headline: str
    detail: str = ""
    warning: str = ""
    # Form prefill (None when nothing is recorded)
    microsteps: Optional[int] = None
    driver_current_a: Optional[float] = None
    driver_peak_current_a: Optional[float] = None
    microns_per_pulse: Optional[float] = None

    @staticmethod
    def recorded(
        motor_name: str,
        stepper_driver_name: str,
        microsteps: int,
        driver_current_a: float,
        driver_peak_current_a: float,
        microns_per_pulse: float,
        recorded_at_text: str,
        driver_current_warning: Optional[str],
    ) -> "MechanicalTransmissionViewModel":
        return MechanicalTransmissionViewModel(
            is_recorded=True,
            headline=f"Transmission en cours : {_french(microns_per_pulse)} µm par incrément (micro-pas 1/{microsteps})",
            detail=f"Moteur « {motor_name} », driver « {stepper_driver_name} » — enregistrée le {recorded_at_text}.",
            warning=driver_current_warning or "",
            microsteps=microsteps,
            driver_current_a=driver_current_a,
            driver_peak_current_a=driver_peak_current_a,
            microns_per_pulse=microns_per_pulse,
        )

    @staticmethod
    def missing(missing_quantity: str, where_to_enter: str) -> "MechanicalTransmissionViewModel":
        return MechanicalTransmissionViewModel(
            is_recorded=False,
            headline="Aucune transmission enregistrée : le banc ne convertit pas encore les incréments en mm.",
            detail=f"Manque : {missing_quantity}. {where_to_enter}".strip(),
        )
