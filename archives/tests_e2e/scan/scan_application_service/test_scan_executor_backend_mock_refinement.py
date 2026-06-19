import sys
import os
import unittest
import threading
import time
from uuid import uuid4

from infrastructure.real.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.real.execution.step_scan_executor import StepScanExecutor
from infrastructure.fake.hardware.arcus_performax_4EX.fake_motion_port import FakeMotionPort
from infrastructure.fake.hardware.micro_controller.ads131a04.fake_acquisition_port import FakeAcquisitionPort
from tests_e2e.base.test_base_agent import DiagramFriendlyTest

from domain.models.scan.aggregate.scan import Scan as StepScan
from domain.models.scan.value_objects import ScanTrajectory
from domain.models.scan.value_objects import StepScanConfig
from domain.models.scan.value_objects import ScanStatus
from domain.shared.value_objects.position_2d import Position2D
from domain.models.scan.value_objects import ScanZone
from domain.models.scan.value_objects import ScanPattern
from domain.models.scan.value_objects import MeasurementUncertainty
from domain.models.motion.value_objects.motion_profile import MotionProfile

# Setup path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

class TestScanExecutorBackend(DiagramFriendlyTest):
    """
    Backend-only test for StepScanExecutor ensuring event-based synchronization.
    Generates sequence diagram traces.
    """

    def test_event_based_execution(self):
        # 1. SETUP PHASE
        self.log_divider("Setup Phase")
        
        # Create Infrastructure
        self.log_interaction("TestRunner", "CREATE", "EventBus", "Initialize InMemoryEventBus")
        event_bus = InMemoryEventBus()
        
        self.log_interaction("TestRunner", "CREATE", "MotionPort", "Initialize FakeMotionPort", {"delay_ms": 50.0})
        motion_port = FakeMotionPort(event_bus=event_bus, motion_delay_ms=50.0)
        
        self.log_interaction("TestRunner", "CREATE", "AcquisitionPort", "Initialize FakeAcquisitionPort")
        acquisition_port = FakeAcquisitionPort()
        
        self.log_interaction("TestRunner", "CREATE", "ScanExecutor", "Initialize StepScanExecutor")
        executor = StepScanExecutor(motion_port, acquisition_port, event_bus)

        # Config objects
        zone = ScanZone(x_min=0, x_max=10, y_min=0, y_max=1)
        pattern = ScanPattern.RASTER
        uncertainty = MeasurementUncertainty(max_uncertainty_volts=0.001)

        config = StepScanConfig(
            scan_zone=zone,
            x_nb_points=2,
            y_nb_points=1,
            scan_pattern=pattern,
            stabilization_delay_ms=0,
            averaging_per_position=1,
            measurement_uncertainty=uncertainty
        )

        # Create Scan Aggregate
        self.log_interaction("TestRunner", "CREATE", "StepScan", "Initialize Scan Aggregate")
        scan = StepScan(id=uuid4())
        
        # Start Scan (Domain Logic)
        self.log_interaction("TestRunner", "COMMAND", "StepScan", "Start Scan")
        scan.start(config)

        # Define Trajectory (typically comes from a service, hardcoded here for unit test)
        trajectory = [Position2D(0,0), Position2D(10,0)]

        # Events Tracking
        events_received = []
        def handler(event):
            event_name = type(event).__name__
            self.log_interaction("EventBus", "RECEIVE", "TestHandler", f"Received {event_name}", {"event": event_name})
            events_received.append(event_name)
        
        self.log_interaction("TestRunner", "SUBSCRIBE", "EventBus", "Subscribe to motion events")
        event_bus.subscribe("motionstarted", handler)
        event_bus.subscribe("motioncompleted", handler)

        # 2. EXECUTION PHASE
        self.log_divider("Execution Phase")
        
        print("Starting execution...")
        start_time = time.time()
        
        self.log_interaction("TestRunner", "CALL", "ScanExecutor", "execute(scan, trajectory)")
        success = executor.execute(scan, trajectory, config)
        
        end_time = time.time()
        print(f"Execution finished. Success: {success}. Duration: {end_time-start_time:.2f}s")
        
        # 3. VERIFICATION PHASE
        self.log_divider("Verification Phase")
        
        # Assert Success
        self.log_interaction("TestRunner", "ASSERT", "ScanExecutor", "Check execution success", expect=True, got=success)
        self.assertTrue(success)
        
        # Assert Status
        self.log_interaction("TestRunner", "ASSERT", "StepScan", "Check scan status", expect=ScanStatus.COMPLETED, got=scan.status)
        self.assertEqual(scan.status, ScanStatus.COMPLETED)
        
        # Assert Points
        self.log_interaction("TestRunner", "ASSERT", "StepScan", "Check points count", expect=2, got=len(scan.points))
        self.assertEqual(len(scan.points), 2)
        
        # Verify events presence
        event_names = [e for e in events_received]
        self.log_interaction("TestRunner", "ASSERT", "EventBus", "Check MotionStarted emitted", expect=True, got="MotionStarted" in event_names)
        self.assertTrue(any(e == "MotionStarted" for e in event_names))
        
        self.log_interaction("TestRunner", "ASSERT", "EventBus", "Check MotionCompleted emitted", expect=True, got="MotionCompleted" in event_names)
        self.assertTrue(any(e == "MotionCompleted" for e in event_names))

    def test_motion_failure_handling(self):
        """Test how executor handles motion failures using the enhanced Mock."""
        # 1. SETUP
        self.log_divider("Setup - Failure Test")
        event_bus = InMemoryEventBus()
        # Mock with small delay
        motion_port = FakeMotionPort(event_bus=event_bus, motion_delay_ms=10.0) 
        acquisition_port = FakeAcquisitionPort()
        executor = StepScanExecutor(motion_port, acquisition_port, event_bus)

        # Config
        zone = ScanZone(x_min=0, x_max=10, y_min=0, y_max=1)
        pattern = ScanPattern.RASTER
        uncertainty = MeasurementUncertainty(max_uncertainty_volts=0.001)
        config = StepScanConfig(scan_zone=zone, x_nb_points=2, y_nb_points=1, 
                                scan_pattern=pattern, stabilization_delay_ms=0, 
                                averaging_per_position=1, measurement_uncertainty=uncertainty)
        
        scan = StepScan(id=uuid4())
        scan.start(config)
        trajectory = [Position2D(0,0), Position2D(10,0)]

        # Configure failure on NEXT move (which is the first one here)
        self.log_interaction("TestRunner", "COMMAND", "MotionPort", "Inject Failure Configuration", {"reason": "Simulated Critical Error"})
        motion_port.set_failure_next_move("Simulated Critical Error")

        # Events Tracking
        self.log_interaction("TestRunner", "SUBSCRIBE", "EventBus", "Subscribe to motion events")
        failed_events = []
        def handler(event):
            event_name = type(event).__name__
            self.log_interaction("EventBus", "RECEIVE", "TestHandler", f"Received {event_name}", {"event": event_name})
            if event_name == "MotionFailed":
                failed_events.append(event)
        
        event_bus.subscribe("motionfailed", handler)

        # 2. EXECUTION
        self.log_divider("Execution - Failure Test")
        success = executor.execute(scan, trajectory, config)

        # 3. VERIFICATION
        self.log_divider("Verification - Failure Test")
        
        self.log_interaction("TestRunner", "ASSERT", "ScanExecutor", "Check execution failure", expect=False, got=success)
        self.assertFalse(success)
        
        self.log_interaction("TestRunner", "ASSERT", "StepScan", "Check scan status", expect=ScanStatus.FAILED, got=scan.status)
        self.assertEqual(scan.status, ScanStatus.FAILED)
        
        self.log_interaction("TestRunner", "ASSERT", "EventBus", "Check MotionFailed detected", expect=True, got=len(failed_events) > 0)
        self.assertTrue(len(failed_events) > 0)

    def test_physics_based_execution(self):
        """Test realistic physics simulation using MotionProfile."""
        self.log_divider("Setup - Physics Test")
        event_bus = InMemoryEventBus()
        
        # Configure Profile: Slow move
        # min=1, target=10, acc=50, dec=50
        # Distance 20cm. 
        # t_acc = 0.18s. d_acc = 0.99cm.
        # t_dec = 0.18s. d_dec = 0.99cm.
        # d_cruise = 20 - 1.98 = 18.02cm.
        # t_cruise = 18.02/10 = 1.802s.
        # Total = 0.18 + 1.802 + 0.18 = 2.162s.
        
        profile = MotionProfile(min_speed=1.0, target_speed=10.0, acceleration=50.0, deceleration=50.0)
        self.log_interaction("TestRunner", "CREATE", "MotionProfile", "Defined physics profile", {"target_speed": 10.0})
        
        motion_port = FakeMotionPort(event_bus=event_bus, motion_profile=profile)
        acquisition_port = FakeAcquisitionPort()
        executor = StepScanExecutor(motion_port, acquisition_port, event_bus)
        
        # Config
        zone = ScanZone(x_min=0, x_max=20, y_min=0, y_max=1)
        pattern = ScanPattern.RASTER
        uncertainty = MeasurementUncertainty(max_uncertainty_volts=0.001) 
        config = StepScanConfig(scan_zone=zone, x_nb_points=1, y_nb_points=1, 
                                scan_pattern=pattern, stabilization_delay_ms=0, 
                                averaging_per_position=1, measurement_uncertainty=uncertainty)
        
        scan = StepScan(id=uuid4())
        scan.start(config)
        
        # Trajectory: Move from (0,0) to (20,0)
        trajectory = [Position2D(20,0)] 

        # Capture Duration
        durations = []
        def handler(event):
            if hasattr(event, 'duration_ms'):
               durations.append(event.duration_ms)
        
        event_bus.subscribe("motioncompleted", handler)
        
        # 2. EXECUTION
        self.log_divider("Execution - Physics Test")
        start_time = time.time()
        
        self.log_interaction("TestRunner", "CALL", "ScanExecutor", "execute move (0->20cm)")
        success = executor.execute(scan, trajectory, config)
        
        elapsed = time.time() - start_time
        print(f"Physics Test Elapsed: {elapsed:.3f}s")
        
        # 3. VERIFICATION
        self.log_divider("Verification - Physics Test")
        self.assertTrue(success)
        self.assertTrue(len(durations) > 0)
        
        measured_duration_ms = durations[0]
        expected_s = 2.162
        expected_ms = expected_s * 1000.0
        
        self.log_interaction("TestRunner", "ASSERT", "MotionPort", 
                             f"Check physics duration ~{expected_ms}ms", 
                             expect=f"{expected_ms} +/- 300", got=f"{measured_duration_ms}")
                             
        delta = abs(measured_duration_ms - expected_ms)
        self.assertTrue(delta < 300.0, f"Duration {measured_duration_ms}ms differ from expected {expected_ms}ms by {delta}")

if __name__ == '__main__':
    unittest.main()
