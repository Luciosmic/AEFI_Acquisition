"""
End-to-End test for SensorFrameAutocalibrationApiService using simulation infrastructure.

Rationale (global context)
    Validate the full orchestration path (API -> use-case -> infrastructure optimizer -> transformation state)
    using deterministic, analytic synthetic data.

Responsibility (local context, promise theory)
    This test asserts that for a known extrinsic 'XYZ' rotation, the calibration recovers angles close to the truth
    and that the TransformationService is updated accordingly.

Design (tactical choices)
    - Use `ScipySensorFrameCalibrationOptimizer` (infrastructure adapter) as the source of truth.
    - Generate probe-frame measurements analytically from bench-frame vectors using R.inv() with 'XYZ' extrinsic.
    - Use only in-phase components (quadrature=0) for deterministic prediction.
"""

import unittest
from datetime import datetime

import numpy as np
from scipy.spatial.transform import Rotation as R

from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from application.services.transformation_service.transformation_service import TransformationService
from application.services.sensor_frame_autocalibration_service.sensor_frame_autocalibration_service import (
    SensorFrameAutocalibrationService,
)
from application.services.sensor_frame_autocalibration_service.sensor_frame_autocalibration_api_service import (
    SensorFrameAutocalibrationApiService,
)
from infrastructure.calibration.scipy_sensor_frame_calibration_optimizer import (
    ScipySensorFrameCalibrationOptimizer,
)


class TestSensorFrameAutocalibrationApiServiceE2E(unittest.TestCase):
    def test_e2e_recovers_known_extrinsic_XYZ_angles(self):
        # Ground truth angles (degrees), extrinsic 'XYZ'
        true_angles = (12.0, -17.0, 6.5)
        rotation = R.from_euler("XYZ", list(true_angles), degrees=True)

        # Ideal bench-frame excitation vectors
        v_bench_x = np.array([1.0, 0.0, 0.0])
        v_bench_y = np.array([0.0, 1.0, 0.0])

        # Generate probe-frame vectors analytically: v_probe = R.inv() * v_bench
        v_probe_x = rotation.inv().apply(v_bench_x)
        v_probe_y = rotation.inv().apply(v_bench_y)

        ts = datetime.now()

        def to_vm(v: np.ndarray) -> VoltageMeasurement:
            return VoltageMeasurement(
                voltage_x_in_phase=float(v[0]),
                voltage_x_quadrature=0.0,
                voltage_y_in_phase=float(v[1]),
                voltage_y_quadrature=0.0,
                voltage_z_in_phase=float(v[2]),
                voltage_z_quadrature=0.0,
                timestamp=ts,
            )

        # Multiple identical measurements (deterministic)
        x_measurements = [to_vm(v_probe_x) for _ in range(10)]
        y_measurements = [to_vm(v_probe_y) for _ in range(10)]

        transformation_service = TransformationService()
        optimizer = ScipySensorFrameCalibrationOptimizer()
        use_case = SensorFrameAutocalibrationService(
            transformation_service=transformation_service,
            optimizer=optimizer,
            event_bus=None,
        )
        api = SensorFrameAutocalibrationApiService(use_case=use_case)

        estimated = api.calibrate_from_measurements(
            x_measurements=x_measurements,
            y_measurements=y_measurements,
            initial_angles=(0.0, 0.0, 0.0),
        )

        # Angles should match within tight tolerance for analytic case
        for est, truth in zip(estimated, true_angles):
            self.assertAlmostEqual(est, truth, places=6)

        # TransformationService updated
        self.assertEqual(transformation_service.get_rotation_angles(), estimated)


if __name__ == "__main__":
    unittest.main()

