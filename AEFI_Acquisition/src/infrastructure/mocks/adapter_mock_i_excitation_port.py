from application.services.excitation_configuration_service.i_excitation_port import IExcitationPort
from domain.models.aefi_device.value_objects.excitation.excitation_parameters import ExcitationParameters

class MockExcitationPort(IExcitationPort):
    """
    Mock implementation of the Excitation Port.
    """

    def __init__(self) -> None:
        self.last_parameters: ExcitationParameters | None = None

    def apply_excitation(self, params: ExcitationParameters) -> None:
        print(f"[MockExcitationPort] ===== EXCITATION CHANGED ===== {params.mode.name}, Level={params.level.value}%, Freq={params.frequency}Hz")
        old_params = self.last_parameters
        self.last_parameters = params
        if old_params:
            print(f"[MockExcitationPort] Previous: {old_params.mode.name} -> New: {params.mode.name}")
        print(f"[MockExcitationPort] last_parameters updated, ready for next acquisition")
