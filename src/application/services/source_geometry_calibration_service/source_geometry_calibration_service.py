import logging
from uuid import UUID
from typing import List, Optional

from application.services.source_geometry_calibration_service.dtos.source_geometry_calibration_dto import (
    SourceGeometryCalibrationDTO,
)
from application.services.source_geometry_calibration_service.i_api_source_geometry_calibration_service import (
    IApiSourceGeometryCalibrationService,
)
from domain.calibration.calibration import Calibration
from domain.calibration.repositories.i_source_geometry_calibration_repository import (
    ISourceGeometryCalibrationRepository,
)
from domain.calibration.value_objects.caliper_measurement.caliper_measurement import CaliperMeasurement
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus

SOURCE_GEOMETRY_CALIBRATION_ENTRY_ADDED_TOPIC = "sourcegeometrycalibrationentryadded"

logger = logging.getLogger(__name__)


class SourceGeometryCalibrationService(IApiSourceGeometryCalibrationService):
    """
    Application Service pour la calibration de la géométrie source (4
    sphères d'excitation) — diamètres et distances extrémité-à-extrémité
    mesurés au pied à coulisse, avec incertitude GUM calculée
    automatiquement.
    """

    def __init__(
        self,
        calibration_repository: ISourceGeometryCalibrationRepository,
        event_bus: IDomainEventBus,
    ) -> None:
        self._calibration_repository = calibration_repository
        self._event_bus = event_bus

    def record_calibration(
        self,
        sphere_diameters_m: List[float],
        pairwise_distances_ext_m: List[float],
        resolution_m: float = 0.00002,
        k: float = 2.0,
    ) -> None:
        logger.info(
            "SourceGeometryCalibrationService: Command record_calibration "
            "sphere_diameters_m=%s pairwise_distances_ext_m=%s resolution_m=%s k=%s",
            sphere_diameters_m,
            pairwise_distances_ext_m,
            resolution_m,
            k,
        )
        sphere_diameters = tuple(
            CaliperMeasurement.from_resolution(v, resolution_m, k) for v in sphere_diameters_m
        )
        pairwise_distances_ext = tuple(
            CaliperMeasurement.from_resolution(v, resolution_m, k) for v in pairwise_distances_ext_m
        )
        calibration = Calibration()
        entry = calibration.record_source_geometry_calibration_entry(
            sphere_diameters, pairwise_distances_ext
        )
        self._calibration_repository.add(entry)
        for event in calibration.domain_events:
            self._event_bus.publish(type(event).__name__.lower(), event)

    def get_latest_calibration(self) -> Optional[SourceGeometryCalibrationDTO]:
        latest = self._find_latest_entry()
        if latest is None:
            return None
        return SourceGeometryCalibrationDTO(
            sphere_diameters_m=tuple(m.value_m for m in latest.sphere_diameters),
            sphere_diameters_uncertainty_m=tuple(m.uncertainty_expanded_m for m in latest.sphere_diameters),
            pairwise_distances_ext_m=tuple(m.value_m for m in latest.pairwise_distances_ext),
            pairwise_distances_ext_uncertainty_m=tuple(
                m.uncertainty_expanded_m for m in latest.pairwise_distances_ext
            ),
            k=latest.sphere_diameters[0].k,
            recorded_at=latest.recorded_at,
        )

    def get_current_entry_id(self) -> UUID:
        """Identity of the current (latest) source geometry entry — what sensor
        calibrations reference, instead of copying the geometry values."""
        latest = self._find_latest_entry()
        if latest is None:
            raise ValueError(
                "No source geometry calibration entry recorded yet — the composition root must "
                "seed the registry from the legacy device config before this can be called"
            )
        return latest.entry_id

    def _find_latest_entry(self):
        entries = self._calibration_repository.find_all()
        if not entries:
            return None
        return max(entries, key=lambda entry: entry.recorded_at)
