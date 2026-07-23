import unittest
import random
import time
from datetime import datetime
from domain.step_scan.step_scan import StepScan
from domain.step_scan.services.scan_trajectory_factory.scan_trajectory_factory import ScanTrajectoryFactory
from domain.step_scan.value_objects.step_scan_config.step_scan_config import StepScanConfig
from domain.step_scan.value_objects.scan_zone.scan_zone import ScanZone
from domain.step_scan.value_objects.scan_mode.scan_mode import ScanMode
from domain.shared_kernel.value_objects.measurement_uncertainty.measurement_uncertainty import MeasurementUncertainty
from domain.step_scan.value_objects.scan_point_result.scan_point_result import ScanPointResult
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.step_scan.events.scan_started.scan_started import ScanStarted
from domain.step_scan.events.scan_point_acquired.scan_point_acquired import ScanPointAcquired
from domain.step_scan.events.scan_completed.scan_completed import ScanCompleted

class TestFullScanSimulation(unittest.TestCase):
    
    def test_simulate_full_scan(self):
        print("\n" + "="*50)
        print("ðŸš€ STARTING FULL SCAN SIMULATION")
        print("="*50)
        
        # 1. Configuration
        print("\n[1] Configuring Scan...")
        config = StepScanConfig(
            scan_zone=ScanZone(x_min=0.0, x_max=2.0, y_min=0.0, y_max=2.0),
            x_nb_points=3,
            y_nb_points=3,
            scan_pattern=ScanMode.RASTER,
            stabilization_delay_ms=10,
            averaging_per_position=1,
            measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=1e-6)
        )
        print(f"    Mode: {config.scan_pattern.name}")
        print(f"    Zone: {config.scan_zone}")
        print(f"    Grid: {config.x_nb_points}x{config.y_nb_points}")
        
        # 2. Trajectory Generation
        print("\n[2] Generating Trajectory (Factory)...")
        trajectory = ScanTrajectoryFactory.create_trajectory(config)
        print(f"    Trajectory generated with {len(trajectory)} points.")
        
        # 3. Create Aggregate
        print("\n[3] Creating StepScan Aggregate...")
        scan = StepScan()
        print(f"    Scan ID: {scan.id}")
        print(f"    Status: {scan.status.name}")
        
        # 4. Start Scan
        print("\n[4] Starting Scan...")
        scan.start(config)
        print(f"    Status: {scan.status.name}")
        
        # Check Event
        events = scan.domain_events
        if events and isinstance(events[0], ScanStarted):
            print("    âœ… EVENT EMITTED: ScanStarted")
            
        # 5. Execution Loop
        print("\n[5] Executing Scan Loop...")
        for i, position in enumerate(trajectory):
            print(f"    ðŸ“ Point {i+1}/{len(trajectory)} at ({position.x:.1f}, {position.y:.1f})")
            
            # Simulate Hardware Move (Sleep)
            # time.sleep(0.01) 
            
            # Simulate Acquisition
            voltage = random.uniform(-5.0, 5.0)
            measurement = AefiVoltageMeasurement(
                voltage_x_in_phase=voltage,
                voltage_x_quadrature=random.uniform(-0.1, 0.1),
                voltage_y_in_phase=random.uniform(-5.0, 5.0),
                voltage_y_quadrature=random.uniform(-0.1, 0.1),
                voltage_z_in_phase=random.uniform(-5.0, 5.0),
                voltage_z_quadrature=random.uniform(-0.1, 0.1),
                timestamp=datetime.now(),
                uncertainty_estimate_volts=1e-6
            )
            
            # Create Result Value Object
            result = ScanPointResult(
                position=position,
                measurement=measurement,
                point_index=i
            )
            
            # Add to Aggregate
            scan.add_point_result(result)
            
            # Check Event
            events = scan.domain_events
            if events and isinstance(events[0], ScanPointAcquired):
                print(f"       âœ… EVENT EMITTED: ScanPointAcquired (V={voltage:.3f}V)")
                
        # 6. Complete Scan
        print("\n[6] Completing Scan...")
        scan.complete()
        print(f"    Status: {scan.status.name}")
        
        # Check Event
        events = scan.domain_events
        if events and isinstance(events[0], ScanCompleted):
            print(f"    âœ… EVENT EMITTED: ScanCompleted (Total Points: {events[0].total_points})")
            
        print("\n" + "="*50)
        print("ðŸ SIMULATION COMPLETE")
        print("="*50 + "\n")

if __name__ == '__main__':
    unittest.main()
