from dataclasses import dataclass
from domain.models.aefi_device.value_objects.excitation.excitation_mode import ExcitationMode
from domain.models.aefi_device.value_objects.excitation.excitation_level import ExcitationLevel

@dataclass(frozen=True)
class ExcitationParameters:
    """
    Domain definition of the excitation state.
    
    It describes WHAT we want to achieve (Mode and Level), 
    not HOW (voltages, phases, registers).
    """
    mode: ExcitationMode
    level: ExcitationLevel
    frequency: float

    @staticmethod
    def off() -> 'ExcitationParameters':
        # Default to X_DIR with 0% level for "Off" state
        return ExcitationParameters(ExcitationMode.X_DIR, ExcitationLevel.off(), frequency=0.0)
