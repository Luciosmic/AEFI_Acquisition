from dataclasses import replace

from application.services.excitation_configuration_service.ports.i_excitation_port import IExcitationPort
from domain.shared_kernel.excitation.value_objects.excitation_parameters import ExcitationParameters
from domain.shared_kernel.excitation.value_objects.excitation_level import ExcitationLevel

class MockExcitationPort(IExcitationPort):
    """
    Mock implementation of the Excitation Port.
    """

    def __init__(self) -> None:
        self.last_parameters: ExcitationParameters | None = None

    def apply_excitation(self, params: ExcitationParameters) -> None:
        print(
            f"[MockExcitationPort] ===== EXCITATION CHANGED ===== {params.mode.name}, "
            f"Level S1-S2={params.level_s1_s2.value}%, Level S3-S4={params.level_s3_s4.value}%, Freq={params.frequency}Hz"
        )
        old_params = self.last_parameters
        self.last_parameters = params
        if old_params:
            print(f"[MockExcitationPort] Previous: {old_params.mode.name} -> New: {params.mode.name}")
        print(f"[MockExcitationPort] last_parameters updated, ready for next acquisition")

    def set_gain(self, level_s1_s2_percent: float, level_s3_s4_percent: float) -> None:
        if self.last_parameters is None:
            return
        self.last_parameters = replace(
            self.last_parameters,
            level_s1_s2=ExcitationLevel(level_s1_s2_percent),
            level_s3_s4=ExcitationLevel(level_s3_s4_percent),
        )
        print(f"[MockExcitationPort] set_gain: S1-S2={level_s1_s2_percent}%, S3-S4={level_s3_s4_percent}%")
