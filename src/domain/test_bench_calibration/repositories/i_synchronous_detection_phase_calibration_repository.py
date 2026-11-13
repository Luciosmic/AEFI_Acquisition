from abc import ABC, abstractmethod
from typing import List

from domain.test_bench_calibration.entities.synchronous_detection_phase_calibration_entry.synchronous_detection_phase_calibration_entry import (
    SynchronousDetectionPhaseCalibrationEntry,
)
from domain.test_bench_configuration.value_objects.hardware_signature.hardware_signature import HardwareSignature


class ISynchronousDetectionPhaseCalibrationRepository(ABC):
    """
    Interface for persisting the synchronous detection phase calibration
    registry (append-only entries) and the compensation-enabled flag.
    Follows the DDD Repository pattern.

    Responsibility:
        - `add(entry)` : ajouter une entrée au registre — **jamais** d'écrasement
          ni de suppression d'une entrée existante (registre constructif,
          append-only, décision actée avec l'utilisateur).
        - `find_by_hardware_signature(signature)` : retrouver toutes les entrées
          enregistrées pour une signature matérielle donnée.
        - `load_compensation_enabled()` : lire l'état persisté du flag de
          compensation — retourne `False` par défaut si aucun état n'a encore été
          sauvegardé.
        - `save_compensation_enabled(enabled)` : persister le nouvel état du flag
          de compensation.

    Rationale:
        Définir le contrat de persistance du registre de calibration de phase de
        détection synchrone, suivant le pattern Repository DDD. Le domain déclare
        QUOI persister (un registre append-only d'entrées, plus un flag de
        compensation), l'infrastructure décide COMMENT (fichier JSON aujourd'hui,
        cf. `RealSynchronousDetectionPhaseCalibrationRepository`).

    Design:
        - **ABC placée dans `domain/test_bench_calibration/repositories/`** : frontière
          domain/infrastructure pour la persistance de cet agrégat.
        - Implémentée par `RealSynchronousDetectionPhaseCalibrationRepository`
          (JSON, `.aefi_acquisition/calibrations/synchronous_detection_phase_calibration.json`)
          et par `FakeSynchronousDetectionPhaseCalibrationRepository` (en mémoire)
          dans `infrastructure/persistence/calibration/`.
        - L'interface domain ne connaît ni JSON ni chemin de fichier — le domain
          reste pur.
    """

    @abstractmethod
    def add(self, entry: SynchronousDetectionPhaseCalibrationEntry) -> None:
        """
        Append a new calibration entry to the registry.

        The registry is constructive: this must never overwrite or remove
        an existing entry, regardless of hardware signature — it is a
        pure append.

        Args:
            entry: The calibration entry to add.
        """
        pass

    @abstractmethod
    def find_by_hardware_signature(
        self, signature: HardwareSignature
    ) -> List[SynchronousDetectionPhaseCalibrationEntry]:
        """
        Retrieve all calibration entries recorded for a given hardware
        signature.

        Args:
            signature: The hardware setup to filter entries by.

        Returns:
            List of matching SynchronousDetectionPhaseCalibrationEntry
            objects (empty if none recorded yet).
        """
        pass

    @abstractmethod
    def load_compensation_enabled(self) -> bool:
        """
        Read the persisted synchronous detection compensation flag.

        Returns:
            The persisted state, or False if none has been saved yet.
        """
        pass

    @abstractmethod
    def save_compensation_enabled(self, enabled: bool) -> None:
        """
        Persist the synchronous detection compensation flag.

        Args:
            enabled: The new state to persist.
        """
        pass
