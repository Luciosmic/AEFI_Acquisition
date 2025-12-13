from application.services.excitation_configuration_service.i_excitation_port import IExcitationPort
from domain.value_objects.excitation.excitation_parameters import ExcitationParameters

class MockExcitationPort(IExcitationPort):
    """
    Mock implementation of the Excitation Port.
    """

    def __init__(self) -> None:
        self.last_parameters: ExcitationParameters | None = None

    def apply_excitation(self, params: ExcitationParameters) -> None:
        print(f"[MockExcitationPort] Applying Excitation: Mode={params.mode.name}, Level={params.level.value}%, Freq={params.frequency}Hz")
        self.last_parameters = params
