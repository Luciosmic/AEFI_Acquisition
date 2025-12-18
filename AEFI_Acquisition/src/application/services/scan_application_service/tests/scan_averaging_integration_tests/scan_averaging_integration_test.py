import unittest
import random
import math
import os
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Optional

from domain.shared.value_objects.position_2d import Position2D
from domain.models.aefi_device.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from application.services.motion_control_service.i_motion_port import IMotionPort
from src.application.services.scan_application_service.ports.i_acquisition_port import IAcquisitionPort
from src.application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.dtos.scan_dtos import Scan2DConfigDTO

# --- Mocks ---

class MockMotionPort(IMotionPort):
    def __init__(self):
        self.current_position = Position2D(0, 0)
        self.move_history = []

    def move_to(self, position: Position2D) -> None:
        self.current_position = position
        self.move_history.append(position)

    def get_current_position(self) -> Position2D:
        return self.current_position

    def is_moving(self) -> bool:
        return False

    def wait_until_stopped(self) -> None:
        pass

    def home(self) -> None:
        self.current_position = Position2D(0, 0)

    def stop(self) -> None:
        pass

class NoisyAcquisitionPort(IAcquisitionPort):
    def __init__(self, motion_port: MockMotionPort, noise_std_dev: float = 0.1):
        self.motion_port = motion_port
        self.noise_std_dev = noise_std_dev
        self.random = random.Random(42) # Fixed seed for reproducibility

    def acquire_sample(self) -> VoltageMeasurement:
        pos = self.motion_port.get_current_position()
        
        # Signal Function: f(x, y) = x + y
        true_signal = pos.x + pos.y
        
        # Variable Noise: SPATIAL dependence (Linear with spatial index)
        # This simulates a property of the sample or environment that varies with position,
        # NOT with time. This allows verifying that measurements are correctly mapped to positions.
        # Assuming 5x5 grid with integer coordinates 0..4
        # Spatial Index = y * 5 + x (Raster order equivalent)
        index = int(pos.y) * 5 + int(pos.x)
        
        # Sigma = 0.1 + 0.05 * index
        # Index 0 (0,0) -> 0.1
        # Index 24 (4,4) -> 0.1 + 1.2 = 1.3
        current_sigma = 0.1 + 0.05 * index
        
        # Add Noise
        noise = self.random.gauss(0, current_sigma)
        measured_value = true_signal + noise
        
        return VoltageMeasurement(
            voltage_x_in_phase=measured_value,
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=datetime.now()
        )

    def configure_for_uncertainty(self, max_uncertainty_volts: float) -> None:
        pass

    def is_ready(self) -> bool:
        return True

# --- Integration Test ---

class TestScanAveragingIntegration(unittest.TestCase):
    
    def test_raster_averaging(self):
        self._run_scan_test("RASTER")

    def test_serpentine_averaging(self):
        self._run_scan_test("SERPENTINE")

    def test_comb_averaging(self):
        self._run_scan_test("COMB")

    def _run_scan_test(self, pattern_name: str):
        print("\n" + "="*60)
        print(f"🔍 INTEGRATION TEST: SCAN AVERAGING & VISUALIZATION ({pattern_name})")
        print("="*60)
        
        # 1. Setup
        motion_port = MockMotionPort()
        # noise_std_dev is now dynamic in the port
        acquisition_port = NoisyAcquisitionPort(motion_port)
        service = ScanApplicationService(motion_port, acquisition_port)
        
        # 2. Configure Scan
        # 5x5 grid = 25 points
        # Averaging = 100 samples per point (to get good statistics)
        config_dto = Scan2DConfigDTO(
            x_min=0, x_max=4, x_nb_points=5,
            y_min=0, y_max=4, y_nb_points=5,
            scan_pattern=pattern_name,
            stabilization_delay_ms=0,
            averaging_per_position=1000, 
            uncertainty_volts=1e-6
        )
        
        print(f"    • Configuration: 5x5 Grid, 100 samples/point")
        print(f"    • Signal Model: V = x + y")
        print(f"    • Noise Model: Sigma = 0.1 + 0.05 * Index")
        
        # 3. Execute Scan
        print("    👉 Starting Scan...")
        success = service.execute_scan(config_dto)
        self.assertTrue(success, "Scan execution failed")
        print("    ✅ Scan Completed")
        
        # Access the scan aggregate directly (for testing purposes)
        scan = service._current_scan
        self.assertIsNotNone(scan, "Scan aggregate should not be None")
        
        # 4. Verify Results
        print("\n    📊 Verifying Statistics...")
        
        errors_mean = []
        errors_std = []
        
        for point in scan.points:
            pos = point.position
            measured = point.measurement
            
            # Calculate expected values
            index = int(pos.y) * 5 + int(pos.x)
            expected_mean = pos.x + pos.y
            expected_std = 0.1 + 0.05 * index
            
            # Check Mean (Standard Error of Mean = sigma / sqrt(N))
            # Max sigma is 1.3, N=100 -> SEM = 0.13
            # Tolerance 3*SEM ~ 0.4
            mean_error = abs(measured.voltage_x_in_phase - expected_mean)
            errors_mean.append(mean_error)
            
            # Check Std Dev
            # Std Dev estimation error is approx sigma / sqrt(2(N-1))
            # Max sigma 1.3 -> Error ~ 1.3 / 14 ~ 0.09
            # Tolerance ~ 0.3
            std_error = abs(measured.std_dev_x_in_phase - expected_std)
            errors_std.append(std_error)
            
            # Assertions
            self.assertLess(mean_error, 0.5, f"Mean error too high at {pos} (idx {index}): {mean_error:.3f}")
            self.assertLess(std_error, 0.4, f"Std Dev error too high at {pos} (idx {index}): {std_error:.3f}")
            
        print(f"    • Max Mean Error: {max(errors_mean):.4f} (Tolerance: 0.5)")
        print(f"    • Max Std Dev Error: {max(errors_std):.4f} (Tolerance: 0.4)")
        
        # 5. Plotting
        print("\n    🎨 Generating Plots...")
        self.generate_plots(scan, pattern_name)
        
    def generate_plots(self, scan, pattern_name):
        x = [p.position.x for p in scan.points]
        y = [p.position.y for p in scan.points]
        means = [p.measurement.voltage_x_in_phase for p in scan.points]
        stds = [p.measurement.std_dev_x_in_phase for p in scan.points]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Plot 1: Mean Value
        sc1 = ax1.scatter(x, y, c=means, cmap='viridis', s=100)
        fig.colorbar(sc1, ax=ax1, label='Mean Voltage (V)')
        ax1.set_title('Mean Voltage Map (Target: x + y)')
        ax1.set_xlabel('X')
        ax1.set_ylabel('Y')
        ax1.grid(True)
        
        # Plot 2: Standard Deviation
        sc2 = ax2.scatter(x, y, c=stds, cmap='magma', s=100)
        fig.colorbar(sc2, ax=ax2, label='Std Dev (V)')
        ax2.set_title(f'Standard Deviation Map (Linear Increase)')
        ax2.set_xlabel('X')
        ax2.set_ylabel('Y')
        ax2.grid(True)
        
        output_path = os.path.join(os.path.dirname(__file__), f"scan_averaging_integration_test_result_{pattern_name}.png")
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        print(f"    ✅ Plot saved to: {output_path}")

if __name__ == '__main__':
    unittest.main()
