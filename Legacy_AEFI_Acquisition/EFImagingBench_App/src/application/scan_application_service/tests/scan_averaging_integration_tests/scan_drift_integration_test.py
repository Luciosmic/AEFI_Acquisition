import unittest
import random
import os
import matplotlib.pyplot as plt
from datetime import datetime

from domain.value_objects.geometric.position_2d import Position2D
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from application.ports.i_motion_port import IMotionPort
from application.ports.i_acquisition_port import IAcquisitionPort
from application.scan_application_service.scan_application_service import ScanApplicationService
from application.dtos.scan_dtos import Scan2DConfigDTO

# --- Mocks ---

class MockMotionPort(IMotionPort):
    def __init__(self):
        self.current_position = Position2D(0, 0)

    def move_to(self, position: Position2D) -> None:
        self.current_position = position

    def get_current_position(self) -> Position2D:
        return self.current_position

    def is_moving(self) -> bool:
        return False

    def wait_until_stopped(self) -> None:
        pass
    
    def home(self) -> None: pass
    def stop(self) -> None: pass

class DriftingAcquisitionPort(IAcquisitionPort):
    def __init__(self, drift_per_sample: float = 0.01):
        self.drift_per_sample = drift_per_sample
        self.sample_count = 0
        self.random = random.Random(42)

    def acquire_sample(self) -> VoltageMeasurement:
        # Temporal Drift: Value increases with time (sample count)
        drift_value = self.sample_count * self.drift_per_sample
        self.sample_count += 1
        
        # Base signal is 0, we only measure drift
        measured_value = drift_value + self.random.gauss(0, 0.01)
        
        return VoltageMeasurement(
            voltage_x_in_phase=measured_value,
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=datetime.now()
        )

    def configure_for_uncertainty(self, max_uncertainty_volts: float) -> None: pass
    def is_ready(self) -> bool: return True

# --- Integration Test ---

class TestScanDriftIntegration(unittest.TestCase):
    
    def test_drift_raster(self):
        self._run_drift_test("RASTER")

    def test_drift_serpentine(self):
        self._run_drift_test("SERPENTINE")

    def _run_drift_test(self, pattern_name: str):
        print("\n" + "="*60)
        print(f"⏳ INTEGRATION TEST: TEMPORAL DRIFT ({pattern_name})")
        print("="*60)
        
        # 1. Setup
        motion_port = MockMotionPort()
        drift_rate = 0.01
        acquisition_port = DriftingAcquisitionPort(drift_per_sample=drift_rate)
        service = ScanApplicationService(motion_port, acquisition_port)
        
        # 2. Configure Scan
        # 5x5 grid = 25 points
        # Averaging = 10 samples per point -> 250 total samples
        samples_per_point = 10
        config_dto = Scan2DConfigDTO(
            x_min=0, x_max=4, x_nb_points=5,
            y_min=0, y_max=4, y_nb_points=5,
            scan_pattern=pattern_name,
            stabilization_delay_ms=0,
            averaging_per_position=samples_per_point, 
            uncertainty_volts=1e-6
        )
        
        print(f"    • Configuration: 5x5 Grid, {samples_per_point} samples/point")
        print(f"    • Drift Model: +{drift_rate} V per sample")
        
        # 3. Execute Scan
        service.execute_scan(config_dto)
        scan = service._current_scan
        
        # 4. Verify Drift
        print("\n    📊 Verifying Temporal Drift...")
        
        # Collect results ordered by acquisition time (which matches the list order in scan.points)
        # Note: scan.points is a list of ScanPointResult. 
        # In StepScan, points are added sequentially.
        
        measured_values = [p.measurement.voltage_x_in_phase for p in scan.points]
        
        # Expected Drift Calculation
        # Point i (0-indexed) corresponds to samples [i*N, (i+1)*N - 1]
        # Average sample index for point i is i*N + (N-1)/2
        # Expected Value ~ (i*N + (N-1)/2) * drift_rate
        
        errors = []
        for i, val in enumerate(measured_values):
            avg_sample_index = i * samples_per_point + (samples_per_point - 1) / 2.0
            expected_val = avg_sample_index * drift_rate
            
            error = abs(val - expected_val)
            errors.append(error)
            
            # Tolerance: Random noise is small (0.01), so error should be small
            self.assertLess(error, 0.05, f"Drift error too high at point {i}: {error:.3f}")
            
        print(f"    • Max Drift Error: {max(errors):.4f}")
        
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
        
        # Annotate order
        for i, (px, py) in enumerate(zip(x, y)):
            plt.annotate(str(i), (px, py), xytext=(0, 0), textcoords='offset points', ha='center', va='center', color='white', fontsize=8)
            
        output_path = os.path.join(os.path.dirname(__file__), f"scan_drift_results_{pattern_name}.png")
        plt.savefig(output_path)
        plt.close()
        print(f"    ✅ Plot saved to: {output_path}")

if __name__ == '__main__':
    unittest.main()
