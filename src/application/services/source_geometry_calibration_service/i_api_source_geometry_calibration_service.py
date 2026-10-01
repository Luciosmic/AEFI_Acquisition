from abc import ABC, abstractmethod
from typing import List, Optional

from application.services.source_geometry_calibration_service.dtos.source_geometry_calibration_dto import (
    SourceGeometryCalibrationDTO,
)


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
