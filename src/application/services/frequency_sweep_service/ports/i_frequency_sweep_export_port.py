from abc import ABC, abstractmethod
from typing import Sequence, Tuple

from application.services.frequency_sweep_service.dtos.acquisition_parameters_dtos import (
    FrequencySweepAcquisitionParametersDTO,
)
from application.services.frequency_sweep_service.dtos.frequency_sweep_dtos import (
    FrequencySweepResultDTO,
    FrequencySweepSampleDTO,
)
from application.shared.acquisition_parameters.acquisition_conditions_dtos import ExportedFileDTO
from domain.shared_kernel.operation_result import OperationResult


class IFrequencySweepExportPort(ABC):
    """
    Persist one frequency sweep in its own export location: the response per
    frequency, the raw samples, and the acquisition parameters — see
    i_frequency_sweep_export_port_intention.md.

    Expected I/O failures (disk full, no permission) are failures, never raised.

    Responsibility:
        - `open_export(role, table_height_mm)` : créer le dossier du balayage au démarrage (les paramètres y sont écrits pendant qu'il tourne).
        - `export(location, result, samples)` : écrire la réponse par fréquence et les échantillons bruts ; retourner les fichiers écrits (taille, SHA-256).
        - `write_acquisition_parameters(location, parameters)` : (ré)écrire les paramètres d'acquisition.

    Rationale:
        Un fond ne sert qu'à être relu : soustrait d'une mesure objet, comparé à un autre fond, combiné en profil. Il doit donc quitter la session sous une forme qui se relit sans le logiciel, avec les conditions de son acquisition à côté.

    Design:
        - Calque `IAcquisitionThroughputExportPort`. Le port possède le format ; il reçoit des DTOs sans format.
        - Échec d'entrée/sortie attendu → `OperationResult.fail`, jamais une exception.
    """

    @abstractmethod
    def open_export(self, role: str, table_height_mm: float) -> OperationResult[str, str]:
        """Create the export location; returns it."""

    @abstractmethod
    def export(
        self, location: str, result: FrequencySweepResultDTO, samples: Sequence[FrequencySweepSampleDTO]
    ) -> OperationResult[Tuple[ExportedFileDTO, ...], str]: ...

    @abstractmethod
    def write_acquisition_parameters(
        self, location: str, parameters: FrequencySweepAcquisitionParametersDTO
    ) -> OperationResult[None, str]:
        """(Re)write the acquisition parameters of the sweep in `location`."""
