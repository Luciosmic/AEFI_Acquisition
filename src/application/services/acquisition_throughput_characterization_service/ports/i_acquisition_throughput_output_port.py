from abc import ABC, abstractmethod

from application.services.acquisition_throughput_characterization_service.dtos.acquisition_throughput_dtos import (
    AcquisitionThroughputCharacterizationDTO,
    AcquisitionThroughputPointDTO,
)


class IAcquisitionThroughputOutputPort(ABC):
    """
    Output Port for AcquisitionThroughputCharacterizationService — see
    i_acquisition_throughput_output_port_intention.md.

    Called from the sweep's background task: implementations must be
    thread-safe (Qt signals are).

    Responsibility:
        - `present_throughput_characterization_step(message)` : étape en cours.
        - `present_throughput_point_measured(point)` : un point mesuré, affiché au fil
          de l'eau.
        - `present_throughput_characterization_succeeded(result)` : résultat complet.
        - `present_throughput_characterization_failed(reason)` : raison lisible.

    Rationale:
        Un balayage dure de quelques dizaines de secondes à quelques minutes, hors
        du thread UI. Sans port de sortie, l'opérateur ne verrait rien avant la fin
        — ni la progression, ni qu'un point est aberrant — et un échec (scan en
        cours, flux muet) se perdrait dans les logs.

    Design:
        - ABC pure, même patron que `ISensorCalibrationOutputPort` ; implémentée par
          `AcquisitionThroughputCharacterizationPresenter`, enregistrée via
          `set_output_port()`. Appelée depuis le thread de la tâche : thread-safe.
    """

    @abstractmethod
    def present_throughput_characterization_step(self, message: str) -> None: ...

    @abstractmethod
    def present_throughput_point_measured(self, point: AcquisitionThroughputPointDTO) -> None: ...

    @abstractmethod
    def present_throughput_characterization_succeeded(self, result: AcquisitionThroughputCharacterizationDTO) -> None: ...

    @abstractmethod
    def present_throughput_characterization_failed(self, reason: str) -> None: ...
