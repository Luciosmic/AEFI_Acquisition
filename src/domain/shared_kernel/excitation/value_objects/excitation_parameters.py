from dataclasses import dataclass
from domain.shared_kernel.excitation.value_objects.excitation_mode import ExcitationMode
from domain.shared_kernel.excitation.value_objects.excitation_level import ExcitationLevel

@dataclass(frozen=True)
class ExcitationParameters:
    """
    Domain definition of the excitation state.

    It describes WHAT we want to achieve (Mode and Level),
    not HOW (voltages, phases, registers).

    level_s1_s2 and level_s3_s4 are independent: two separate hardware gains,
    not one shared value. Physically, the DDS2 generator drives spheres S1/S2
    and the DDS1 generator drives S3/S4 (confirmed on oscilloscope — see
    SphereId.dds_channel — counter-intuitive relative to the channel numbers).
    """
    mode: ExcitationMode
    level_s1_s2: ExcitationLevel
    level_s3_s4: ExcitationLevel
    frequency: float

    @staticmethod
    def off() -> 'ExcitationParameters':
        # Default to X_DIR with 0% level for "Off" state
        return ExcitationParameters(
            ExcitationMode.X_DIR, ExcitationLevel.off(), ExcitationLevel.off(), frequency=0.0
        )
