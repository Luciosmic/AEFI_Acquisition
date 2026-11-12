from datetime import datetime, timedelta, timezone
from uuid import uuid4

from application.services.scan_export_service.column_stabilization_record.column_stabilization_record import (
    STABILIZATION_COLUMNS,
    ACCELEROMETER_COLUMNS,
    ColumnStabilizationRecord,
)
from domain.detection_devices.inertial_probe.events.inertial_probe_sample_acquired.inertial_probe_sample_acquired import (
    InertialProbeSampleAcquired,
)
from domain.scan.events.column_rest_measured.column_rest_measured import ColumnRestMeasured
from domain.scan.events.column_settled.column_settled import ColumnSettled

ORIGIN = datetime(2026, 11, 12, 21, 0, 0, tzinfo=timezone.utc)
SCAN = uuid4()


def _rest(vibration=0.002, reason=None, scan_id=SCAN):
    return ColumnRestMeasured(
        scan_id=scan_id, rest_vibration_g=vibration, sample_count=250, unavailable_reason=reason,
        rest_measurement_s=10.0, window_s=1.0, factor=1.5, timeout_s=30.0, minimum_delay_s=0.3,
    )


def _settled(method="accelerometer", point=0):
    return ColumnSettled(scan_id=SCAN, point_index=point, method=method, stopped_at=ORIGIN, waited_s=2.34567,
                         vibration_g=0.0028, threshold_g=0.003)


def test_waits_are_tabled_when_the_points_are_judged_on_the_accelerometer():
    record = ColumnStabilizationRecord(SCAN, 100.0, ORIGIN)
    assert record.rest_measured(_rest()) is True
    row = record.settled(_settled(point=3))
    assert list(row) == list(STABILIZATION_COLUMNS)
    assert (row["point_index"], row["stabilization_method"], row["stabilization_waited"]) == (3, "accelerometer", 2.3457)
    assert (row["stabilization_vibration"], row["stabilization_threshold"]) == (0.0028, 0.003)


def test_fixed_delay_scan_counts_its_waits_without_a_table():
    record = ColumnStabilizationRecord(SCAN, 100.0, ORIGIN)
    assert record.rest_measured(_rest(vibration=None, reason="accéléromètre non en acquisition")) is False
    assert record.settled(_settled(method="fixed_delay")) is None
    summary = record.summary()
    assert (summary.rest_measured, summary.rest_vibration_g, summary.unavailable_reason) == (
        True, None, "accéléromètre non en acquisition")
    assert summary.waits == (("fixed_delay", 1),)


def test_accelerometer_samples_are_dated_on_the_host_clock():
    record = ColumnStabilizationRecord(SCAN, 100.0, ORIGIN)
    row = record.accelerometer_row(InertialProbeSampleAcquired(
        acquisition_id=uuid4(), sample_index=7, timestamp_s=102.5, acceleration_g=(0.01, -0.02, 1.0)))
    assert list(row) == list(ACCELEROMETER_COLUMNS)
    assert row["accelerometer_timestamp"] == (ORIGIN + timedelta(seconds=2.5)).isoformat(timespec="milliseconds")
    assert (row["acceleration_x"], row["acceleration_y"], row["acceleration_z"]) == (0.01, -0.02, 1.0)
    assert record.accelerometer_row(InertialProbeSampleAcquired(
        acquisition_id=uuid4(), sample_index=8, timestamp_s=102.6)) is None  # accelerometer channel not streamed


def test_summary_counts_the_samples_written_and_ignores_other_scans():
    record = ColumnStabilizationRecord(SCAN, 100.0, ORIGIN)
    assert record.summary() is None
    assert record.rest_measured(_rest(scan_id=uuid4())) is False
    record.accelerometer_written()
    summary = record.summary()
    assert (summary.rest_measured, summary.accelerometer_samples_written) == (False, 1)
    record.rest_measured(_rest())
    record.settled(_settled())
    record.settled(_settled(method="timeout"))
    summary = record.summary()
    assert (summary.rest_vibration_g, summary.window_s, summary.waits) == (
        0.002, 1.0, (("accelerometer", 1), ("timeout", 1)))
