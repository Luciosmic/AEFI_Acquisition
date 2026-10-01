from abc import ABC, abstractmethod

from domain.shared_kernel.excitation.value_objects.excitation_mode import ExcitationMode
from domain.shared_kernel.excitation.value_objects.excitation_parameters import ExcitationParameters


class IApiExcitationConfigurationService(ABC):
    """
    Responsibility:
    - Inbound API contract for ExcitationConfigurationService.
    - Defines what UI adapters and controllers may call on this service.

    Rationale:
    - Distinguishes inbound callers (Adapters → Application) from outbound ports
      (Application → Infrastructure) which use the i_ prefix.

    Design:
    - Pure ABC, no state.
    - Implemented by ExcitationConfigurationService.
    """

    @abstractmethod
    def set_excitation(
        self,
        mode: ExcitationMode,
        level_s1_s2_percent: float,
        level_s3_s4_percent: float,
        frequency: float,
    ) -> None: ...

    @abstractmethod
    def get_current_parameters(self) -> ExcitationParameters: ...
