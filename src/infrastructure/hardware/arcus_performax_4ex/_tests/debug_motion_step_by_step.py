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
else:
    print("Error: Could not find 'src' directory")
    sys.exit(1)

from infrastructure.hardware.arcus_performax_4EX.composition_root_arcus import ArcusCompositionRoot
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from PyQt6.QtCore import QCoreApplication

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def wait_for_user(prompt: str):
    print(f"\n>>> USER ACTION REQUIRED: {prompt}")
    print(">>> Press ENTER to continue...", end='', flush=True)
    sys.stdin.readline()

def debug_motion_interactive():
    print("==================================================")
    print("       INTERACTIVE MOTION DEBUGGER")
    print("==================================================")
    print("This script will perform moves one by one.")
    print("Please verify the physical motion of the stage.")
    print("==================================================")

    # 0. Qt App (needed for signals if used, though we might not use Presenter here)
    app = QCoreApplication(sys.argv)

    # 1. Setup
    print("\n[1] Initializing Arcus Hardware...")
    event_bus = InMemoryEventBus()
    arcus_root = ArcusCompositionRoot(event_bus=event_bus)
    
    try:
        arcus_root.lifecycle.initialize_all()
        print("    -> Connected.")
    except Exception as e:
        print(f"    -> Connection Failed: {e}")
        return

    motion_port = arcus_root.motion

    try:
        # 2. Home
        wait_for_user("Ready to HOME the device?")
        print("    -> Homing...")
        motion_port.home()
        motion_port.wait_until_stopped()
        pos = motion_port.get_current_position()
        print(f"    -> Homed. Software Position: X={pos.x:.3f}, Y={pos.y:.3f}")
        
        # 3. Move X to 10.0
        wait_for_user("Ready to MOVE X to 10.0 mm?")
        print("    -> Moving X to 10.0...")
        target = pos.__class__(x=10.0, y=0.0)
        motion_port.move_to(target)
        motion_port.wait_until_stopped()
        pos = motion_port.get_current_position()
        print(f"    -> Move Complete. Software Position: X={pos.x:.3f}, Y={pos.y:.3f}")
        
        # 4. Move X back to 0.0
        wait_for_user("Ready to MOVE X back to 0.0 mm?")
        print("    -> Moving X to 0.0...")
        target = pos.__class__(x=0.0, y=0.0)
        motion_port.move_to(target)
        motion_port.wait_until_stopped()
        pos = motion_port.get_current_position()
        print(f"    -> Move Complete. Software Position: X={pos.x:.3f}, Y={pos.y:.3f}")

        # 5. Move Y to 5.0
        wait_for_user("Ready to MOVE Y to 5.0 mm?")
        print("    -> Moving Y to 5.0...")
        target = pos.__class__(x=0.0, y=5.0)
        motion_port.move_to(target)
        motion_port.wait_until_stopped()
        pos = motion_port.get_current_position()
        print(f"    -> Move Complete. Software Position: X={pos.x:.3f}, Y={pos.y:.3f}")

        print("\n[SUCCESS] Interactive test sequence completed.")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n[Cleanup] Closing connection...")
        arcus_root.lifecycle.close_all()

if __name__ == "__main__":
    debug_motion_interactive()
