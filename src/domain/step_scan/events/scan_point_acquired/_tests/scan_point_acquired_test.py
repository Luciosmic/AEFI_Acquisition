from datetime import datetime
from uuid import uuid4

from domain.step_scan.events.scan_point_acquired.scan_point_acquired import ScanPointAcquired
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement


def _measurement(value: float = 0.0) -> AefiVoltageMeasurement:
    return AefiVoltageMeasurement(
        voltage_x_in_phase=value,
        voltage_x_quadrature=0.0,
        voltage_y_in_phase=0.0,
        voltage_y_quadrature=0.0,
        voltage_z_in_phase=0.0,
        voltage_z_quadrature=0.0,
        timestamp=datetime.now(),
    )


def test_baseline_measurement_defaults_to_none():
    event = ScanPointAcquired(
        scan_id=uuid4(), point_index=0, position=Position2D(0.0, 0.0), measurement=_measurement()
    )

    assert event.baseline_measurement is None


def test_baseline_measurement_can_be_attached():
    baseline = _measurement(0.1)
    event = ScanPointAcquired(
        scan_id=uuid4(),
        point_index=0,
        position=Position2D(0.0, 0.0),
        measurement=_measurement(0.5),
        baseline_measurement=baseline,
    )

    assert event.baseline_measurement is baseline
