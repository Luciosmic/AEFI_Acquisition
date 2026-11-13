from abc import ABC, abstractmethod
from typing import List

from domain.test_bench_calibration.entities.source_geometry_calibration_entry.source_geometry_calibration_entry import (
    SourceGeometryCalibrationEntry,
)


class ISourceGeometryCalibrationRepository(ABC):
    """
    Interface for persisting the source geometry calibration registry
    (append-only entries). Follows the DDD Repository pattern.

    Responsibility:
        - `add(entry)`: append an entry — never overwrite or remove an existing one.
        - `find_all()`: retrieve every entry. No hardware-signature filter (unlike
          the sensor calibration repository) — there is a single physical
          bench, so `SourceGeometryCalibrationService` filters nothing beyond
          picking the most recent by `recorded_at`. The composition root also reuses
          `find_all()` to detect an empty registry and seed it from the legacy
          `aefi_device_config.json` on first boot.

    Rationale:
        Defines the persistence contract for the source geometry calibration
        registry, following the same Repository pattern as
        `ISensorCalibrationRepository`: the domain declares WHAT to persist (an
        append-only registry of entries), infrastructure decides HOW (a JSON file
        today, see `RealSourceGeometryCalibrationRepository`).

    Design:
        - **ABC placed in `domain/test_bench_calibration/repositories/`**: domain/infrastructure
          boundary for this aggregate's persistence.
        - Implemented by `RealSourceGeometryCalibrationRepository` (JSON,
          `.aefi_acquisition/calibrations/source_geometry_calibration.json`) and
          `FakeSourceGeometryCalibrationRepository` (in-memory), both in
          `infrastructure/persistence/calibration/`.
        - The domain interface knows nothing of JSON or file paths — the domain
          stays pure.
    """

    @abstractmethod
    def add(self, entry: SourceGeometryCalibrationEntry) -> None:
        """
        Append a new calibration entry to the registry.

        The registry is constructive: this must never overwrite or remove
        an existing entry — it is a pure append.

        Args:
            entry: The calibration entry to add.
        """
        pass

    @abstractmethod
    def find_all(self) -> List[SourceGeometryCalibrationEntry]:
        """
        Retrieve every recorded calibration entry, in stored order.

        No filter at the repository level — there is a single source bench
        (unlike sensor calibration, no hardware-signature dimension
        applies here). Callers pick the most recent entry themselves
        (`SourceGeometryCalibrationService`), and this same method doubles
        as the "is the registry empty yet?" check used by the composition
        root to decide whether to seed from the legacy device config JSON.

        Returns:
            List of every SourceGeometryCalibrationEntry (empty if none
            recorded yet).
        """
        pass
