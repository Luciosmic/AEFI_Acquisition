"""FrequencySweep aggregate root (see frequency_sweep_intention.md)."""

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

from domain.frequency_sweep.errors.frequency_already_acquired_error import FrequencyAlreadyAcquiredError
from domain.frequency_sweep.errors.frequency_not_in_grid_error import FrequencyNotInGridError
from domain.frequency_sweep.errors.frequency_point_incomplete_error import FrequencyPointIncompleteError
from domain.frequency_sweep.events.frequency_point_acquired.frequency_point_acquired import FrequencyPointAcquired
from domain.frequency_sweep.events.frequency_sweep_completed.frequency_sweep_completed import FrequencySweepCompleted
from domain.frequency_sweep.value_objects.frequency_grid.frequency_grid import FrequencyGrid
from domain.frequency_sweep.value_objects.frequency_sweep_id.frequency_sweep_id import FrequencySweepId
from domain.frequency_sweep.value_objects.frequency_sweep_role.frequency_sweep_role import FrequencySweepRole
from domain.frequency_sweep.value_objects.table_height.table_height import TableHeight
from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.step_scan.services.measurement_statistics_service.measurement_statistics_service import (
    MeasurementStatisticsService,
)


@dataclass
class FrequencySweep:
    id: FrequencySweepId
    role: FrequencySweepRole
    grid: FrequencyGrid
    table_height: TableHeight
    samples_per_frequency: int
    _points: Dict[float, AefiVoltageMeasurement] = field(default_factory=dict)
    _domain_events: List[DomainEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.samples_per_frequency < 1:
            raise ValueError("samples_per_frequency must be >= 1")

    @property
    def is_completed(self) -> bool:
        return len(self._points) == len(self.grid)

    @property
    def points(self) -> Tuple[Tuple[float, AefiVoltageMeasurement], ...]:
        """Acquired (frequency in Hz, averaged measurement), in grid order."""
        return tuple((f, self._points[f]) for f in self.grid.frequencies_hz if f in self._points)

    @property
    def domain_events(self) -> List[DomainEvent]:
        """Get and clear domain events."""
        events = list(self._domain_events)
        self._domain_events.clear()
        return events

    def record_frequency_point(self, frequency_hz: float, samples: Sequence[AefiVoltageMeasurement]) -> AefiVoltageMeasurement:
        """Average exactly N samples acquired at a grid frequency; returns the
        averaged measurement (mean and standard deviation per channel)."""
        if frequency_hz not in self.grid.frequencies_hz:
            raise FrequencyNotInGridError(self.id, frequency_hz)
        if frequency_hz in self._points:
            raise FrequencyAlreadyAcquiredError(self.id, frequency_hz)
        if len(samples) != self.samples_per_frequency:
            raise FrequencyPointIncompleteError(self.id, frequency_hz, self.samples_per_frequency, len(samples))
        measurement = MeasurementStatisticsService.calculate_statistics(list(samples))
        self._points[frequency_hz] = measurement
        self._domain_events.append(
            FrequencyPointAcquired(
                frequency_sweep_id=self.id,
                role=self.role.value,
                frequency_index=self.grid.index_of(frequency_hz),
                frequency_hz=frequency_hz,
                measurement=measurement,
                samples_count=self.samples_per_frequency,
                table_height_mm=self.table_height.millimetres,
            )
        )
        if self.is_completed:
            self._domain_events.append(
                FrequencySweepCompleted(frequency_sweep_id=self.id, role=self.role.value, frequency_count=len(self.grid))
            )
        return measurement
