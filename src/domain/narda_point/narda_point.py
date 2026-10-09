"""NardaPoint aggregate root (see narda_point_intention.md)."""

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple
from uuid import UUID

from domain.electric_field_probe.services.field_measurement_statistics_service.field_measurement_statistics_service import (
    FieldMeasurementStatisticsService,
)
from domain.electric_field_probe.value_objects.field_measurement.field_measurement import FieldMeasurement
from domain.narda_point.errors.narda_point_already_acquired_error import NardaPointAlreadyAcquiredError
from domain.narda_point.errors.narda_point_incomplete_error import NardaPointIncompleteError
from domain.narda_point.events.narda_point_acquired.narda_point_acquired import NardaPointAcquired
from domain.narda_point.value_objects.narda_point_id.narda_point_id import NardaPointId
from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D


@dataclass
class NardaPoint:
    id: NardaPointId
    scan_id: UUID
    position: Position2D
    point_index: int
    expected_samples: int
    expects_baseline: bool = False
    axis_labels: Optional[Tuple[str, ...]] = None
    _field_measurement: Optional[FieldMeasurement] = None
    _baseline_field_measurement: Optional[FieldMeasurement] = None
    _domain_events: List[DomainEvent] = field(default_factory=list)

    def __post_init__(self):
        if self.expected_samples < 1:
            raise ValueError("expected_samples must be >= 1")

    @property
    def field_measurement(self) -> Optional[FieldMeasurement]:
        return self._field_measurement

    @property
    def baseline_field_measurement(self) -> Optional[FieldMeasurement]:
        return self._baseline_field_measurement

    @property
    def is_acquired(self) -> bool:
        return self._field_measurement is not None

    @property
    def domain_events(self) -> List[DomainEvent]:
        """Get and clear domain events."""
        events = list(self._domain_events)
        self._domain_events.clear()
        return events

    def record_samples(
        self,
        samples: Sequence[FieldMeasurement],
        baseline_samples: Optional[Sequence[FieldMeasurement]] = None,
    ) -> None:
        if self.is_acquired:
            raise NardaPointAlreadyAcquiredError(self.id)
        if len(samples) != self.expected_samples:
            raise NardaPointIncompleteError(self.id, self.expected_samples, len(samples))
        baseline_count = len(baseline_samples) if baseline_samples else 0
        expected_baseline = self.expected_samples if self.expects_baseline else 0
        if baseline_count != expected_baseline:
            raise NardaPointIncompleteError(self.id, expected_baseline, baseline_count, "baseline samples")
        self._field_measurement = FieldMeasurementStatisticsService.calculate_statistics(list(samples))
        if baseline_count:
            self._baseline_field_measurement = FieldMeasurementStatisticsService.calculate_statistics(
                list(baseline_samples)
            )
        self._domain_events.append(
            NardaPointAcquired(
                narda_point_id=self.id,
                scan_id=self.scan_id,
                point_index=self.point_index,
                position=self.position,
                field_measurement=self._field_measurement,
                baseline_field_measurement=self._baseline_field_measurement,
                axis_labels=self.axis_labels,
                samples_count=self.expected_samples,
            )
        )
