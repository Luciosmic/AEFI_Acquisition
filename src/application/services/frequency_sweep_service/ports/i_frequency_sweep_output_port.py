from abc import ABC, abstractmethod

from application.services.frequency_sweep_service.dtos.frequency_sweep_dtos import (
    FrequencyPointDTO,
    FrequencySweepResultDTO,
)


class IFrequencySweepOutputPort(ABC):
    """
    Output Port for FrequencySweepService — see
    i_frequency_sweep_output_port_intention.md.

    Called from the sweep's background task: implementations must be
    thread-safe (Qt signals are).

    Responsibility:
        - `present_frequency_sweep_step` : l'étape en cours, en clair.
        - `present_frequency_point_measured` : une fréquence acquise, pour le tracé en direct.
        - `present_frequency_sweep_ended` : fin normale ou arrêt demandé, avec ce qui a été acquis et le dossier d'export.
        - `present_frequency_sweep_failed` : refus au démarrage ou échec en cours, avec la raison.

    Rationale:
        Un balayage au banc dure plusieurs minutes : l'opérateur doit voir chaque fréquence arriver, et non un résultat final après un silence. Le service ne connaît pas Qt.

    Design:
        - Appelé depuis la tâche de fond : l'implémentation doit être sûre entre threads (signaux Qt).
    """

    @abstractmethod
    def present_frequency_sweep_step(self, message: str) -> None: ...

    @abstractmethod
    def present_frequency_point_measured(self, point: FrequencyPointDTO) -> None: ...

    @abstractmethod
    def present_frequency_sweep_ended(self, result: FrequencySweepResultDTO) -> None:
        """Completed or cancelled: what was acquired, and where it was exported."""

    @abstractmethod
    def present_frequency_sweep_failed(self, reason: str) -> None: ...
