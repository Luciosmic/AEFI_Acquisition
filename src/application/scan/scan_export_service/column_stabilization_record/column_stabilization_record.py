"""Column Stabilization Record (see column_stabilization_record_intention.md)."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from application.scan.scan_export_service.dtos.scan_acquisition_parameters_dtos import ColumnStabilizationDTO
from domain.inertial_probe.events.inertial_probe_sample_acquired.inertial_probe_sample_acquired import (
    InertialProbeSampleAcquired,
)
from domain.scan.events.column_rest_measured.column_rest_measured import ColumnRestMeasured
from domain.scan.events.column_settled.column_settled import ColumnSettled

# Sidecar tables of the acquisition folder (`<timestamp>_<kind>_<name>_<tag>.csv`);
# their columns are declared in acquisition-parameters.json (data.columns, "file").
ACCELEROMETER_TABLE = "accelerometer"
ACCELEROMETER_COLUMNS = (
    "accelerometer_sample_index", "accelerometer_timestamp", "acceleration_x", "acceleration_y", "acceleration_z",
)
STABILIZATION_TABLE = "column-stabilization"
STABILIZATION_COLUMNS = (
    "point_index", "stabilization_method", "stabilization_stopped_at", "stabilization_waited",
    "stabilization_vibration", "stabilization_threshold",
)


class ColumnStabilizationRecord:
    """What one scan export keeps of the column stabilization and of the accelerometer stream.

    `monotonic_origin_s` / `wall_origin`: the same instant on the monotonic clock of the
    inertial samples (perf_counter) and on the host clock, to date each sample.
    """

    def __init__(self, scan_id, monotonic_origin_s: float, wall_origin: datetime) -> None:
        self.scan_id = scan_id
        self._monotonic_origin_s = monotonic_origin_s
        self._wall_origin = wall_origin
        self._rest: Optional[ColumnRestMeasured] = None
        self._waits: Dict[str, int] = {}
        self._accelerometer_samples = 0

    @property
    def judged_on_accelerometer(self) -> bool:
        return self._rest is not None and self._rest.rest_vibration_g is not None

    def rest_measured(self, event: ColumnRestMeasured) -> bool:
        """Keep the rest level of this scan. True when the points are judged on the
        accelerometer: the stabilization table is then worth writing."""
        if event.scan_id != self.scan_id:
            return False
        self._rest = event
        return self.judged_on_accelerometer

    def settled(self, event: ColumnSettled) -> Optional[Dict[str, Any]]:
        """Count the wait; its row for the stabilization table when judged on the accelerometer."""
        if event.scan_id != self.scan_id:
            return None
        self._waits[event.method] = self._waits.get(event.method, 0) + 1
        if not self.judged_on_accelerometer:
            return None
        return {
            "point_index": event.point_index,
            "stabilization_method": event.method,
            "stabilization_stopped_at": event.stopped_at.astimezone().isoformat(timespec="milliseconds"),
            "stabilization_waited": round(event.waited_s, 4),
            "stabilization_vibration": event.vibration_g,
            "stabilization_threshold": event.threshold_g,
        }

    def accelerometer_row(self, event: InertialProbeSampleAcquired) -> Optional[Dict[str, Any]]:
        """Row of the accelerometer table; None for a sample without the accelerometer channel."""
        if event.acceleration_g is None:
            return None
        ax, ay, az = event.acceleration_g
        received = self._wall_origin + timedelta(seconds=event.timestamp_s - self._monotonic_origin_s)
        return {
            "accelerometer_sample_index": event.sample_index,
            "accelerometer_timestamp": received.isoformat(timespec="milliseconds"),
            "acceleration_x": ax, "acceleration_y": ay, "acceleration_z": az,
        }

    def accelerometer_written(self) -> None:
        self._accelerometer_samples += 1

    def summary(self) -> Optional[ColumnStabilizationDTO]:
        """None when there was neither a rest measurement nor an accelerometer sample."""
        rest = self._rest
        if rest is None and not self._accelerometer_samples:
            return None
        waits: Tuple[Tuple[str, int], ...] = tuple(self._waits.items())
        if rest is None:
            return ColumnStabilizationDTO(
                rest_measured=False, waits=waits, accelerometer_samples_written=self._accelerometer_samples,
            )
        return ColumnStabilizationDTO(
            rest_measured=True,
            rest_vibration_g=rest.rest_vibration_g,
            rest_sample_count=rest.sample_count,
            unavailable_reason=rest.unavailable_reason,
            minimum_delay_s=rest.minimum_delay_s,
            rest_measurement_s=rest.rest_measurement_s,
            window_s=rest.window_s,
            factor=rest.factor,
            timeout_s=rest.timeout_s,
            waits=waits,
            accelerometer_samples_written=self._accelerometer_samples,
        )
