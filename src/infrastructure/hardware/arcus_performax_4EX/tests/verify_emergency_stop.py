import sys
import time
import logging
import threading
from pathlib import Path

# Add src to sys.path
current_path = Path(__file__).resolve()
src_path = None
for parent in current_path.parents:
    if parent.name == 'src':
        src_path = parent
        break

if src_path:
    if str(src_path) not in sys.path:
        sys.path.append(str(src_path))
        print(f"Added to sys.path: {src_path}")
else:
    print("Error: Could not find 'src' directory")
    sys.exit(1)

# Import directly from packages (assuming src is root)
try:
    from infrastructure.hardware.arcus_performax_4EX.composition_root_arcus import ArcusCompositionRoot
except ImportError:
    from infrastructure.hardware.arcus_performax_4EX.arcus_composition_root import ArcusCompositionRoot

# from infrastructure.hardware.micro_controller.mcu_composition_root import MCUCompositionRoot
from infrastructure.mocks.adapter_mock_i_acquisition_port import MockAcquisitionPort
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from infrastructure.execution.step_scan_executor import StepScanExecutor
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from application.dtos.scan_dtos import Scan2DConfigDTO
from interface.ui_motion_control.presenter_motion_control import MotionControlPresenter
from application.services.motion_control_service.motion_control_service import MotionControlService
from PyQt6.QtCore import QCoreApplication

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_emergency_stop():
    print("==================================================")
    print("       VERIFYING EMERGENCY STOP (Mock Acquisition)")
    print("==================================================")
    
    # 0. Create QCoreApplication
    app = QCoreApplication(sys.argv)

    # 1. Initialize Infrastructure (Roots)
    print("\n[1] Creating Composition Roots...")
    event_bus = InMemoryEventBus()
    
    arcus_root = ArcusCompositionRoot(event_bus=event_bus)
    # mcu_root = MCUCompositionRoot(event_bus=event_bus)
    mock_acquisition = MockAcquisitionPort()

    # 2. Setup Services
    print("\n[2] Setting up Services...")
    executor = StepScanExecutor(
        motion_port=arcus_root.motion,
        acquisition_port=mock_acquisition, # Use Mock
        event_bus=event_bus
    )
    
    scan_service = ScanApplicationService(
        motion_port=arcus_root.motion,
        acquisition_port=mock_acquisition, # Use Mock
        event_bus=event_bus,
        scan_executor=executor
    )
    
    motion_service = MotionControlService(
        motion_port=arcus_root.motion,
        event_bus=event_bus
    )
    
    # Presenter
    motion_presenter = MotionControlPresenter()
    motion_presenter.set_event_bus(event_bus)
    motion_presenter.start_monitoring()
    
    # 3. Initialize Hardware
    print("\n[3] Connecting Hardware...")
    try:
        arcus_root.lifecycle.initialize_all()
        # mcu_root.lifecycle.initialize_all()
        print("    -> Hardware Connected.")
    except Exception as e:
        print(f"    -> Connection Failed: {e}")
        return

    try:
        # 4. Home
        print("\n[4] Homing...")
        arcus_root.motion.home()
        arcus_root.motion.wait_until_stopped(timeout=60.0)
        print("    -> Homed.")

        # 5. Configure Long Scan (to allow time for E-Stop)
        # User Request: 4 movements, 20cm x 20cm (200mm x 200mm)
        print("\n[5] Configuring Scan (200x200 mm, 2x2 points)...")
        config_dto = Scan2DConfigDTO(
            x_min=0.0,
            x_max=200.0,
            y_min=0.0,
            y_max=200.0,
            x_nb_points=2,
            y_nb_points=2,
            scan_pattern="RASTER",
            stabilization_delay_ms=1000, # 1s stabilization to make it slower/clearer
            averaging_per_position=1,
            uncertainty_volts=0.01
        )
        
        # 6. Trigger E-Stop in a thread after 5 seconds (Halfway)
        def trigger_estop():
            print("\n    [Thread] Waiting 5s before E-Stop (Target: Halfway)...")
            time.sleep(5.0)
            print("    [Thread] TRIGGERING EMERGENCY STOP!")
            result = motion_service.emergency_stop()
            if result.is_success:
                print("    [Thread] E-Stop Command Sent Successfully.")
            else:
                print(f"    [Thread] E-Stop Failed: {result.error}")

        estop_thread = threading.Thread(target=trigger_estop)
        estop_thread.start()
        
        # 7. Execute Scan
        print("\n[6] Executing Scan (Expect Failure)...")
        start_time = time.time()
        success = scan_service.execute_scan(config_dto)
        end_time = time.time()
        
        if not success:
            print(f"\n[7] Scan Cancelled/Failed as expected in {end_time - start_time:.2f}s.")
        else:
            print(f"\n[7] ERROR: Scan Completed Successfully! (Should have been cancelled)")
            
        estop_thread.join()

    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n[8] Cleanup...")
        # Close hardware first
        arcus_root.lifecycle.close_all()
        # mcu_root.lifecycle.close_all()
        
        if 'motion_presenter' in locals():
            motion_presenter.stop_monitoring()
            
        print("    -> Closed.")

if __name__ == "__main__":
    verify_emergency_stop()
