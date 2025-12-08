import unittest
from datetime import datetime
from ...aggregates.step_scan import StepScan
from ...value_objects.scan.step_scan_config import StepScanConfig
from ...value_objects.scan.scan_zone import ScanZone
from ...value_objects.scan.scan_pattern import ScanPattern
from ...value_objects.measurement_uncertainty import MeasurementUncertainty
from ...value_objects.scan.scan_point_result import ScanPointResult
from ...value_objects.geometric.position_2d import Position2D
from ...value_objects.acquisition.voltage_measurement import VoltageMeasurement
from ...value_objects.scan.scan_status import ScanStatus
from ...events.scan_events import ScanCompleted

from ...services.scan_trajectory_factory import ScanTrajectoryFactory

class TestStepScanCompletion(unittest.TestCase):
    
    def test_auto_completion(self):
        print("\n" + "="*60)
        print("🔍 EXTENSIVE VISUAL TEST: SCAN COMPLETION LOGIC")
        print("="*60)
        
        # 1. Setup Config
        print("\n[1] CONFIGURATION")
        config = StepScanConfig(
            scan_zone=ScanZone(x_min=0, x_max=1, y_min=0, y_max=1),
            x_nb_points=3,
            y_nb_points=3,
            scan_pattern=ScanPattern.RASTER,
            stabilization_delay_ms=0,
            averaging_per_position=1,
            measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=1e-6)
        )
        print(f"    • [StepScanConfig] Mode: {config.scan_pattern.name}")
        print(f"    • [StepScanConfig] Zone: X[{config.scan_zone.x_min}, {config.scan_zone.x_max}], Y[{config.scan_zone.y_min}, {config.scan_zone.y_max}]")
        print(f"    • [StepScanConfig] Grid: {config.x_nb_points}x{config.y_nb_points}")
        print(f"    • [StepScanConfig] Expected Points: {config.x_nb_points * config.y_nb_points}")
        
        # 2. Generate Trajectory
        print("\n[2] TRAJECTORY GENERATION")
        trajectory = ScanTrajectoryFactory.create_trajectory(config)
        print(f"    • [ScanTrajectoryFactory] Generated {len(trajectory)} points:")
        for i, p in enumerate(trajectory):
            print(f"      {i}: ({p.x:.1f}, {p.y:.1f})")

        # 3. Create and Start Scan
        print("\n[3] SCAN INITIALIZATION")
        scan = StepScan()
        scan.start(config)
        print(f"    • [StepScan] Scan ID: {scan.id}")
        print(f"    • [StepScan] Status: {scan.status.name}")
        self.assertEqual(scan.status, ScanStatus.RUNNING)
        
        # 4. Execute Scan (Add Points)
        print("\n[4] EXECUTION (Adding Points)")
        
        for i, position in enumerate(trajectory):
            print(f"    👉 Processing Point {i+1}/{len(trajectory)}...")
            
            # Create Result
            # DATA SOURCE: Synthetic/Hardcoded for this test
            # In production, this comes from IAcquisitionPort.acquire()
            simulated_voltage_x = 0.1 * i
            
            result = ScanPointResult(
                position=position,
                measurement=VoltageMeasurement(
                    voltage_x_in_phase=simulated_voltage_x, voltage_x_quadrature=0.0,
                    voltage_y_in_phase=0.2 * i, voltage_y_quadrature=0.0,
                    voltage_z_in_phase=0.0, voltage_z_quadrature=0.0,
                    timestamp=datetime.now(), uncertainty_estimate_volts=None
                ),
                point_index=i
            )
            
            print(f"       • [ScanTrajectory] Position: ({result.position.x:.1f}, {result.position.y:.1f})")
            print(f"       • [TestSimulation] Source: SYNTHETIC (0.1 * index)")
            print(f"       • [TestSimulation] Measured: {result.measurement.voltage_x_in_phase:.3f} V")
            
            scan.add_point_result(result)
            print(f"       • [StepScan] New Status: {scan.status.name}")
            
            if i < len(trajectory) - 1:
                self.assertEqual(scan.status, ScanStatus.RUNNING)
            else:
                self.assertEqual(scan.status, ScanStatus.COMPLETED)
        
        # 5. Verify Completion
        print("\n[5] COMPLETION VERIFICATION")
        self.assertEqual(scan.status, ScanStatus.COMPLETED)
        
        # Verify Event
        events = scan.domain_events
        # Last event should be ScanCompleted
        self.assertIsInstance(events[-1], ScanCompleted)
        e = events[-1]
        print(f"    ✅ [StepScan] Scan automatically completed!")
        print(f"    • [DomainEvent] Event: {type(e).__name__}")
        print(f"    • [DomainEvent] Total Points: {e.total_points}")
        
        # 6. Final Object Inspection
        print("\n[6] FINAL OBJECT INSPECTION")
        print(f"    • [StepScan] ID: {scan.id}")
        print(f"    • [StepScan] Status: {scan.status.name}")
        print(f"    • [StepScan] Total Points Collected: {len(scan.points)}")
        print("    • [StepScan] Points Summary:")
        for p in scan.points:
             print(f"      - Index {p.point_index}: Pos({p.position.x:.1f}, {p.position.y:.1f}) -> {p.measurement.voltage_x_in_phase:.3f} V")
             
        print("="*60 + "\n")
        
        # 7. Generate Image
        print("\n[7] GENERATING IMAGE")
        try:
            import matplotlib.pyplot as plt
            import os
            
            x_coords = [p.position.x for p in scan.points]
            y_coords = [p.position.y for p in scan.points]
            values = [p.measurement.voltage_x_in_phase for p in scan.points]
            
            plt.figure(figsize=(8, 6))
            sc = plt.scatter(x_coords, y_coords, c=values, cmap='viridis', s=100)
            plt.colorbar(sc, label='Voltage X (V)')
            plt.title(f'Scan Result: {config.scan_pattern.name} ({len(scan.points)} points)')
            plt.xlabel('X Position')
            plt.ylabel('Y Position')
            plt.grid(True)
            
            # Annotate order
            for i, (x, y) in enumerate(zip(x_coords, y_coords)):
                plt.annotate(str(i), (x, y), xytext=(5, 5), textcoords='offset points')
                
            output_path = os.path.join(os.path.dirname(__file__), "scan_result_plot.png")
            plt.savefig(output_path)
            plt.close()
            print(f"    ✅ Image saved to: {output_path}")
            
        except ImportError:
            print("    ⚠️ Matplotlib not installed, skipping image generation.")

if __name__ == '__main__':
    unittest.main()
