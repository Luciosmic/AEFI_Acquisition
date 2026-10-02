from abc import ABC, abstractmethod

from application.services.acquisition_throughput_characterization_service.dtos.acquisition_parameters_dtos import (
    SoftwareProvenanceDTO,
)


class ISoftwareProvenancePort(ABC):
    """
    Responsibility:
    - Identify the code that ran: name, version, commit, branch, and whether
      the working tree had uncommitted changes.

    Rationale:
    - Everything fixed in code (ADC channel -> I/Q axis mapping, codes -> volts)
      is only reproducible through the commit; a dirty tree is not.

    Design:
    - Never raises: unknown fields are None with `unknown_reason`.
    """

    @abstractmethod
    def read(self) -> SoftwareProvenanceDTO: ...
