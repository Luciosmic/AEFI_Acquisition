from abc import ABC, abstractmethod
from typing import List, Optional

from application.services.source_geometry_calibration_service.dtos.source_frame_geometry_dto import (
    SourceFrameGeometryDTO,
)
from application.services.source_geometry_calibration_service.dtos.source_geometry_calibration_dto import (
    SourceGeometryCalibrationDTO,
)
from application.services.source_geometry_calibration_service.errors.source_geometry_preview_rejected import (
    SourceGeometryPreviewRejected,
)
from domain.shared_kernel.operation_result import OperationResult


class IApiSourceGeometryCalibrationService(ABC):
    """
    Responsibility:
    - Inbound API contract for SourceGeometryCalibrationService.
    - Defines what UI adapters and presenters may call on this service.

    Rationale:
    - Distinguishes inbound callers (Adapters -> Application) from outbound ports
      (Application -> Infrastructure) which use the i_ prefix.

    Design:
    - Pure ABC, no state.
    - Implemented by SourceGeometryCalibrationService.
    """

    @abstractmethod
    def record_calibration(
        self,
        sphere_diameters_m: List[float],
        pairwise_distances_ext_m: List[float],
        resolution_m: float = 0.00002,
        k: float = 2.0,
    ) -> None: ...

    @abstractmethod
    def get_latest_calibration(self) -> Optional[SourceGeometryCalibrationDTO]: ...

    @abstractmethod
    def preview_source_frame(
        self,
        sphere_diameters_m: List[float],
        pairwise_distances_ext_m: List[float],
    ) -> OperationResult[SourceFrameGeometryDTO, SourceGeometryPreviewRejected]:
        """Reconstruct the sphere positions from not-yet-recorded measurements
        (live preview while editing) — nothing is persisted or published."""
