import sys
import time
import logging
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

from infrastructure.hardware.micro_controller.mcu_composition_root import MCUCompositionRoot
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from infrastructure.execution.step_scan_executor import StepScanExecutor
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from application.dtos.scan_dtos import Scan2DConfigDTO
from interface.ui_motion_control.presenter_motion_control import MotionControlPresenter
from PyQt6.QtCore import QCoreApplication

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_scan_motion():
    print("==================================================")
    print("       VERIFYING SCAN MOTION (UNITS: MM)")
    print("==================================================")
    
    # 0. Create QCoreApplication (Required for QObject/Signals)
    app = QCoreApplication(sys.argv)

    # 1. Initialize Infrastructure (Roots)
    print("\n[1] Creating Composition Roots...")
    event_bus = InMemoryEventBus()
    
    # Arcus Root
    arcus_root = ArcusCompositionRoot(event_bus=event_bus)
    
    # MCU Root
    mcu_root = MCUCompositionRoot(event_bus=event_bus)

    # 2. Setup Application Service
    print("\n[2] Setting up Application Service...")
    executor = StepScanExecutor(
        motion_port=arcus_root.motion,
        acquisition_port=mcu_root.acquisition,
        event_bus=event_bus
    )
    
    service = ScanApplicationService(
        motion_port=arcus_root.motion,
        acquisition_port=mcu_root.acquisition,
        event_bus=event_bus,
        scan_executor=executor
    )
    
    # 2b. Setup Motion Control Presenter (Subscriber for PositionUpdated)
    print("    -> Setting up MotionControlPresenter...")
    motion_presenter = MotionControlPresenter()
    motion_presenter.set_event_bus(event_bus)
    motion_presenter.start_monitoring()
    
    def on_presenter_position_update(x, y):
        # print(f"[Presenter] Position Updated: ({x:.3f}, {y:.3f})")
        pass 
        
    motion_presenter.position_updated.connect(on_presenter_position_update)
    
    # Subscribe to print events
    def on_point_acquired(event):
        print(f"    -> Point Acquired: Index={event.point_index}, Pos=({event.position.x:.2f}, {event.position.y:.2f}) mm")
        
    service.subscribe_to_scan_updates(on_point_acquired)

    # 3. Initialize Hardware (Now that subscribers are ready)
    print("\n[3] Connecting Hardware...")
    try:
        arcus_root.lifecycle.initialize_all()
        print("    -> Arcus Connected.")
    except Exception as e:
        print(f"    -> Arcus Connection Failed: {e}")
        return

    try:
        mcu_root.lifecycle.initialize_all()
        print("    -> MCU Connected.")
    except Exception as e:
        print(f"    -> MCU Connection Failed: {e}")
        return

    try:
        # 3. Home first
        print("\n[3] Homing...")
        arcus_root.motion.home()
        arcus_root.motion.wait_until_stopped(timeout=60.0)
        print("    -> Homed.")

        # 4. Configure Scan (Small 10x10 mm scan)
        print("\n[4] Configuring Scan (10x10 mm, 3x3 points)...")
        config_dto = Scan2DConfigDTO(
            x_min=0.0,
            x_max=10.0, # 10 mm
            y_min=0.0,
            y_max=10.0, # 10 mm
            x_nb_points=3,
            y_nb_points=3,
            scan_pattern="RASTER",
            stabilization_delay_ms=100,
            averaging_per_position=1,
            uncertainty_volts=0.01
        )
        
        # 5. Execute
        print("\n[5] Executing Scan...")
        start_time = time.time()
        success = service.execute_scan(config_dto)
        end_time = time.time()
        
        if success:
            print(f"\n[6] Scan Completed Successfully in {end_time - start_time:.2f}s.")
        else:
            print("\n[6] Scan Failed.")
            
        # 6. Return Home
        print("\n[7] Returning Home...")
        arcus_root.motion.move_to(arcus_root.motion.get_current_position().__class__(x=0.0, y=0.0))
        arcus_root.motion.wait_until_stopped()

    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n[8] Cleanup...")
        # Close hardware first to stop emitting events
        arcus_root.lifecycle.close_all()
        mcu_root.lifecycle.close_all()
        
        # Then unsubscribe
        if 'motion_presenter' in locals():
            motion_presenter.stop_monitoring()
            
        print("    -> Closed.")

if __name__ == "__main__":
    verify_scan_motion()
