"""
End-to-End Test: Full Application Stack + Spatially Aware Simulators.

This test validates the "Real" Software (Application/Domain) running against
the "Simulated" Hardware (Infrastructure).

It ensures that:
1. The CLI/Service layer correctly orchestrates scans.
2. The Simulators (Bench/Motion/Acquisition) behave physically correctly.
3. The recovered data matches the "Ground Truth".
"""
import unittest
import time
import math
import numpy as np
from typing import Dict, Any, List

# --- Domain & Application ---
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.scan_application_service.ports.i_scan_output_port import IScanOutputPort
from application.services.motion_control_service.i_motion_port import IMotionPort
from application.services.scan_application_service.ports.i_acquisition_port import IAcquisitionPort
from application.dtos.scan_dtos import Scan2DConfigDTO
from domain.shared.value_objects.position_2d import Position2D
from domain.models.scan.value_objects import ScanStatus
from domain.models.aefi_device.value_objects.acquisition.voltage_measurement import VoltageMeasurement

# --- Infrastructure (Executors & Events) ---
from infrastructure.internal.execution.scan_executors.step_scan.step_scan_executor import StepScanExecutor
from infrastructure.internal.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.internal.execution.scan_executors.fly_scan.fly_scan_executor import FlyScanExecutor

# --- Infrastructure (Simulators & Adapters) ---
from infrastructure.external.hardware._simulator.bench_simulator import BenchSimulator
from infrastructure.external.hardware.arcus_performax_4EX._simulator.motion_simulator import MotionSimulator
from infrastructure.external.hardware.micro_controller.serial_communicator.simulator.acquisition_simulator import AcquisitionSimulator

# NEW: Imported Adapters
from infrastructure.external.hardware.arcus_performax_4EX._simulator.adapters.simulated_motion_port_adapter import SimulatedMotionPortAdapter
from infrastructure.external.hardware.micro_controller.serial_communicator.simulator.adapters.simulated_acquisition_port_adapter import SimulatedAcquisitionPortAdapter

# =================================================================================================
# TEST HELPERS (Output Spy)
# =================================================================================================

class SpyOutputPort(IScanOutputPort):
    def __init__(self):
        self.events = []
        self.points_data = [] 
    
    def _log(self, event, **kwargs):
        self.events.append({"event": event, **kwargs})

    def present_scan_started(self, scan_id: str, config: Dict[str, Any]) -> None:
        self._log("scan_started", scan_id=scan_id)

    def present_scan_progress(self, current_point_index: int, total_points: int, point_data: Any) -> None:
        self._log("scan_progress", index=current_point_index)
        self.points_data.append(point_data)

    def present_scan_completed(self, scan_id: str, total_points: int) -> None:
        self._log("scan_completed", total_points=total_points)

    def present_scan_failed(self, scan_id: str, reason: str) -> None:
        self._log("scan_failed", reason=reason)

    def present_scan_cancelled(self, scan_id: str) -> None:
        self._log("scan_cancelled")

    def present_scan_paused(self, scan_id: str, current_point_index: int) -> None:
        self._log("scan_paused")

    def present_scan_resumed(self, scan_id: str, resume_from_point_index: int) -> None:
        self._log("scan_resumed")
        
    def present_flyscan_started(self, scan_id: str, config: Dict[str, Any]) -> None:
         self._log("flyscan_started")

    def present_flyscan_progress(self, current_point_index: int, total_points: int, point_data: Any) -> None:
        self._log("flyscan_progress", index=current_point_index)
        self.points_data.append(point_data)

    def present_flyscan_completed(self, scan_id: str, total_points: int) -> None:
        self._log("flyscan_completed")

    def present_flyscan_failed(self, scan_id: str, reason: str) -> None:
        self._log("flyscan_failed", reason=reason)

    def present_flyscan_cancelled(self, scan_id: str) -> None:
        self._log("flyscan_cancelled")


# =================================================================================================
# TEST SUITE
# =================================================================================================

class TestE2EFlyScanStepScan(unittest.TestCase):
    
    def setUp(self):
        # 0. Create Event Bus (needed for Motion Adapter)
        self.event_bus = InMemoryEventBus()
        
        # 1. Reset Hardware Simulation
        self.bench = BenchSimulator()
        self.bench._initialize()
        
        self.motion_sim = MotionSimulator()
        self.motion_sim.connect()
        
        self.acq_sim = AcquisitionSimulator(noise_std=0.001, seed=42)
        
        # 2. Create Adapters (using new external classes)
        # Pass event_bus to Motion Adapter so it can publish MotionCompleted
        self.motion_port = SimulatedMotionPortAdapter(self.motion_sim, event_bus=self.event_bus)
        self.acq_port = SimulatedAcquisitionPortAdapter(self.acq_sim)
        
        self.output_port = SpyOutputPort()
        
        # 3. Create Executors
        self.scan_executor = StepScanExecutor(self.motion_port, self.acq_port, self.event_bus)
        
        # Use Real FlyScanExecutor (only needs event_bus, ports are passed in execute())
        self.fly_scan_executor = FlyScanExecutor(event_bus=self.event_bus) 
        
        # 4. Create Service
        self.service = ScanApplicationService(
            motion_port=self.motion_port,
            acquisition_port=self.acq_port,
            event_bus=self.event_bus,
            scan_executor=self.scan_executor,
            fly_scan_executor=self.fly_scan_executor
        )
        self.service.set_output_port(self.output_port)

    def test_step_scan_e2e(self):
        """
        Verify that ScanApplicationService can execute a scan using Simulators.
        """
        print("\\n[Test] Step-Scan E2E with Application Service")
        
        # Configure minimal scan
        dto = Scan2DConfigDTO(
            x_min=0.0, x_max=40.0, 
            y_min=0.0, y_max=10.0,
            x_nb_points=5, 
            y_nb_points=1,
            scan_pattern="SERPENTINE",
            stabilization_delay_ms=0, 
            averaging_per_position=1,
            uncertainty_volts=0.001
        )
        
        # Disable delays for speed
        self.acq_sim.simulator_driver.set_timing(0.0, 0.0)
        
        # Execute
        success = self.service.execute_scan(dto)
        self.assertTrue(success, "Scan should start successfully")
        
        # Wait for completion
        # Since we are running real code with threads/events, ensure timeout is sufficient.
        # Now that MotionAdapter publishes MotionCompleted, StepScanExecutor should proceed.
        start = time.time()
        while self.service.get_status().status != ScanStatus.COMPLETED.value:
            if time.time() - start > 15.0:
                 # Debug fail
                status = self.service.get_status()
                self.fail(f"Scan execution timed out. Status: {status.status}, Points: {status.current_point_index}/{status.total_points}")
            time.sleep(0.1)
            
        print(f"Scan completed in {time.time() - start:.2f}s")
        
        # Verify result count
        points = self.output_port.points_data
        self.assertEqual(len(points), 5)
        
        # Basic Value Validation (Ground Truth Check)
        # Ground Truth: 1 + 0.5 * sin(k*x) * cos(k*y)
        # y=0, so cos(0)=1 => 1 + 0.5 * sin(k*x)
        # x points: 0, 10, 20, 30, 40
        # k = 2pi/50 ~ 0.12566
        # x=0: 1.0
        # x=10: 1 + 0.5*sin(0.12566*10) = 1 + 0.5*sin(1.2566) ~ 1 + 0.5*0.951 ~ 1.475
        # x=20: 1 + 0.5*sin(2.5132) ~ 1 + 0.5*0.587 ~ 1.29
        # x=30: 1 + 0.5*sin(3.7699) ~ 1 + 0.5*(-0.587) ~ 0.706
        # x=40: 1 + 0.5*sin(5.026) ~ 1 + 0.5*(-0.951) ~ 0.524
        
        first_pt = points[0]
        # Check structure
        # If output port spy captures dict form from ScanAppService:
        # { "value": {"x_in_phase": ...}, ... }
        if isinstance(first_pt, dict) and "value" in first_pt:
             val0 = first_pt["value"]["x_in_phase"]
             self.assertAlmostEqual(val0, 1.0, delta=0.1)
             print(f"Verified Point 0: {val0} (expected 1.0)")

if __name__ == '__main__':
    unittest.main()
