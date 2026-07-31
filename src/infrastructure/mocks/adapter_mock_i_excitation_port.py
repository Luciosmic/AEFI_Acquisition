from application.services.excitation_configuration_service.ports.i_excitation_port import IExcitationPort
from domain.shared_kernel.excitation.value_objects.excitation_parameters import ExcitationParameters

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
