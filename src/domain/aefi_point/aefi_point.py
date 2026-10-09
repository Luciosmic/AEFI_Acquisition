"""AefiPoint aggregate root (see aefi_point_intention.md)."""

from dataclasses import dataclass, field
from typing import List, Optional, Sequence
from uuid import UUID

from domain.aefi_point.errors.aefi_point_already_acquired_error import AefiPointAlreadyAcquiredError
from domain.aefi_point.errors.aefi_point_incomplete_error import AefiPointIncompleteError
from domain.aefi_point.events.aefi_point_acquired.aefi_point_acquired import AefiPointAcquired
from domain.aefi_point.value_objects.aefi_point_id.aefi_point_id import AefiPointId
from domain.aefi_point.value_objects.sample.sample import Sample
from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.step_scan.services.measurement_statistics_service.measurement_statistics_service import (
    MeasurementStatisticsService,
)


@dataclass
class AefiPoint:
    id: AefiPointId
    scan_id: UUID
    position: Position2D
    expected_samples: int
    _measurement: Optional[AefiVoltageMeasurement] = None
    _domain_events: List[DomainEvent] = field(default_factory=list)

    def __post_init__(self):
        if self.expected_samples < 1:
            raise ValueError("expected_samples must be >= 1")

    @property
    def measurement(self) -> Optional[AefiVoltageMeasurement]:
        return self._measurement

    @property
    def is_acquired(self) -> bool:
        return self._measurement is not None

    @property
    def domain_events(self) -> List[DomainEvent]:
        """Get and clear domain events."""
        events = list(self._domain_events)
        self._domain_events.clear()
        return events

    def record_samples(self, samples: Sequence[Sample]) -> None:
        if self.is_acquired:
            raise AefiPointAlreadyAcquiredError(self.id)
        if len(samples) != self.expected_samples:
            raise AefiPointIncompleteError(self.id, self.expected_samples, len(samples))
        self._measurement = MeasurementStatisticsService.calculate_statistics([s.measurement for s in samples])
        self._domain_events.append(
            AefiPointAcquired(
                aefi_point_id=self.id,
                scan_id=self.scan_id,
                position=self.position,
                measurement=self._measurement,
                samples_count=self.expected_samples,
            )
        )
