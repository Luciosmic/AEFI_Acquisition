import threading
import unittest
import random
import os
import matplotlib.pyplot as plt
from datetime import datetime

from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from application.services.scan_application_service.ports.i_acquisition_port import IAcquisitionPort
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.scan_application_service.dtos.scan_dtos import Scan2DConfigDTO
from application.services.aefi_acquisition_service.aefi_acquisition_service import AefiAcquisitionService
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.thread_pool_task_runner import ThreadPoolTaskRunner
from infrastructure.execution.event_bus_motion_synchronizer import EventBusMotionSynchronizer
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.mocks.adapter_mock_i_aefi_acquisition_executor import MockAefiAcquisitionExecutor


class DriftingAcquisitionPort(IAcquisitionPort):
    def __init__(self, drift_per_sample: float = 0.01):
        self.drift_per_sample = drift_per_sample
        self.sample_count = 0
        self.random = random.Random(42)

    def acquire_sample(self) -> AefiVoltageMeasurement:
        drift_value = self.sample_count * self.drift_per_sample
        self.sample_count += 1
        measured_value = drift_value + self.random.gauss(0, 0.01)

        return AefiVoltageMeasurement(
            voltage_x_in_phase=measured_value,
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=datetime.now(),
        )

    def configure_for_uncertainty(self, max_uncertainty_volts: float) -> None:
        pass

    def is_ready(self) -> bool:
        return True


class TestScanDriftIntegration(unittest.TestCase):
    """
    Retired: this test's drift model is "+drift_per_sample per call to
    acquire_sample()", which assumed the scan pulled the driver directly in
    a tight per-point loop (exactly averaging_per_position calls per point,
    none between points). Since ScanApplicationService now consumes a
    continuous background stream (see [[scan_application_service]] /
    the acquisition-streaming refactor), acquire_sample() runs flat out for
    the whole scan duration — call count per point is no longer
    deterministic, so "drift = f(call count)" is not a coherent model
    anymore. Coverage for per-point averaging correctness under this
    architecture is provided by scan_averaging_integration_test.py instead
    (its signal model depends on physical position, not call count, so it
    stays valid under streaming).
    """

    @unittest.skip("drift-vs-call-count model incompatible with continuous streaming acquisition — see class docstring")
    def test_drift_raster(self):
        self._run_drift_test("RASTER")

    @unittest.skip("drift-vs-call-count model incompatible with continuous streaming acquisition — see class docstring")
    def test_drift_serpentine(self):
        self._run_drift_test("SERPENTINE")

    def _run_drift_test(self, pattern_name: str):
        print("\n" + "="*60)
        print(f"INTEGRATION TEST: TEMPORAL DRIFT ({pattern_name})")
        print("="*60)

        # 1. Setup
        event_bus = InMemoryEventBus()
        motion_port = MockMotionPort(event_bus=event_bus, motion_delay_ms=1)
        drift_rate = 0.01
        acquisition_port = DriftingAcquisitionPort(drift_per_sample=drift_rate)
        continuous_service = AefiAcquisitionService(
            MockAefiAcquisitionExecutor(event_bus), acquisition_port
        )
        task_runner = ThreadPoolTaskRunner()
        motion_sync = EventBusMotionSynchronizer(event_bus)
        service = ScanApplicationService(
            motion_port, continuous_service, event_bus,
            task_runner=task_runner,
            motion_sync=motion_sync,
        )

        done = threading.Event()
        event_bus.subscribe("scancompleted", lambda e: done.set())

        # 2. Configure Scan — 5×5 grid, 10 samples/point
        samples_per_point = 10
        config_dto = Scan2DConfigDTO(
            x_min=0, x_max=4, x_nb_points=5,
            y_min=0, y_max=4, y_nb_points=5,
            scan_pattern=pattern_name,
            stabilization_delay_ms=0,
            averaging_per_position=samples_per_point,
            uncertainty_volts=1e-6,
        )

        print(f"    Configuration: 5x5 Grid, {samples_per_point} samples/point")
        print(f"    Drift Model: +{drift_rate} V per sample")

        # 3. Execute Scan (non-blocking — wait below)
        service.execute_scan(config_dto)
        self.assertTrue(done.wait(timeout=30.0), "Scan did not complete within timeout")

        scan = service._current_scan

        # 4. Verify Drift
        print("\n    Verifying Temporal Drift...")

        measured_values = [p.measurement.voltage_x_in_phase for p in scan.points]

        errors = []
        for i, val in enumerate(measured_values):
            avg_sample_index = i * samples_per_point + (samples_per_point - 1) / 2.0
            expected_val = avg_sample_index * drift_rate

            error = abs(val - expected_val)
            errors.append(error)

            self.assertLess(error, 0.05, f"Drift error too high at point {i}: {error:.3f}")

        print(f"    Max Drift Error: {max(errors):.4f}")

        # 5. Plotting
        self.generate_plots(scan, pattern_name)

    def generate_plots(self, scan, pattern_name):
        x = [p.position.x for p in scan.points]
        y = [p.position.y for p in scan.points]
        values = [p.measurement.voltage_x_in_phase for p in scan.points]

        plt.figure(figsize=(8, 6))
        sc = plt.scatter(x, y, c=values, cmap='plasma', s=100)
        plt.colorbar(sc, label='Measured Voltage (V)')
        plt.title(f'Temporal Drift Map ({pattern_name})\n(Should follow scan path)')
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.grid(True)

        for i, (px, py) in enumerate(zip(x, y)):
            plt.annotate(str(i), (px, py), xytext=(0, 0), textcoords='offset points',
                         ha='center', va='center', color='white', fontsize=8)

        output_path = os.path.join(os.path.dirname(__file__), f"scan_drift_results_{pattern_name}.png")
        plt.savefig(output_path)
        plt.close()
        print(f"    Plot saved to: {output_path}")


if __name__ == '__main__':
    unittest.main()
