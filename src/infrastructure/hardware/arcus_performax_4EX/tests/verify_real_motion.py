import sys
import time
import logging
from pathlib import Path

# Add parent directory to sys.path to import composition_root_arcus directly
parent_dir = Path(__file__).resolve().parent.parent
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))
    print(f"Added to sys.path: {parent_dir}")

# Also add src to sys.path for domain objects
current_path = Path(__file__).resolve()
src_path = None
for parent in current_path.parents:
    if parent.name == 'src':
        src_path = parent
        break
if src_path and str(src_path) not in sys.path:
    sys.path.append(str(src_path))

try:
    from composition_root_arcus import ArcusCompositionRoot
except ImportError:
    try:
        from arcus_composition_root import ArcusCompositionRoot
    except ImportError:
        print("CRITICAL: Could not import ArcusCompositionRoot from either filename.")
        sys.exit(1)

from domain.value_objects.geometric.position_2d import Position2D

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_motion():
    print("==================================================")
    print("       VERIFYING REAL HARDWARE MOTION")
    print("==================================================")
    
    # 1. Initialize
    print("\n[1] Initializing Arcus Composition Root...")
    # Try to auto-detect or specify port if known (e.g., 'COM3')
    # For now, we rely on auto-detect or default
    root = ArcusCompositionRoot() 
    motion = root.motion
    lifecycle = root.lifecycle
    
    try:
        print("[2] Connecting to Hardware...")
        lifecycle.initialize_all()
        print(f"    -> Connected successfully. Controller connected: {root._driver.is_connected()}")
    except Exception as e:
        print(f"    -> CRITICAL ERROR: Connection failed: {e}")
        return

    try:
        # 2. Home
        print("\n[3] Homing Axes (This should physically move the motors)...")
        print(f"    -> Pre-Homing Status: X Homed={root._driver.is_homed('x')}, Y Homed={root._driver.is_homed('y')}")
        print("    -> Sending Home Command...")
        motion.home()
        
        print("    -> Waiting for homing to complete (timeout 60s)...")
        motion.wait_until_stopped(timeout=60.0)
        print("    -> Homing Complete.")
        print(f"    -> Post-Homing Status: X Homed={root._driver.is_homed('x')}, Y Homed={root._driver.is_homed('y')}")
        
        pos = motion.get_current_position()
        print(f"    -> Current Position: {pos} (Should be near 0,0)")

        # 3. Move to Start Position
        target_x = 10.0 # mm
        target_y = 10.0 # mm
        print(f"\n[4] Moving to Start Position ({target_x}, {target_y}) mm...")
        target_pos = Position2D(x=target_x, y=target_y)
        
        start_time = time.time()
        motion.move_to(target_pos)
        
        # Monitor motion
        while motion.is_moving():
            pos = motion.get_current_position()
            print(f"    -> Moving... Current: {pos}")
            time.sleep(0.5)
            
        motion.wait_until_stopped(timeout=10.0)
        end_time = time.time()
        print(f"    -> Move Complete in {end_time - start_time:.2f}s.")
        
        pos = motion.get_current_position()
        print(f"    -> Final Position: {pos}")
        
        # 4. Scan Sequence
        print("\n[5] Executing Scan Sequence (3 points)...")
        scan_points = [
            Position2D(x=11.0, y=10.0),
            Position2D(x=12.0, y=10.0),
            Position2D(x=13.0, y=10.0)
        ]
        
        for i, point in enumerate(scan_points):
            print(f"    -> Point {i+1}: Moving to {point}...")
            motion.move_to(point)
            motion.wait_until_stopped(timeout=5.0)
            print(f"       -> Reached. Measuring (Simulated)...")
            time.sleep(0.5) 
            
        print("\n[6] Scan Sequence Complete.")
        
        # 5. Return Home
        print("\n[7] Returning to Home (0,0)...")
        motion.move_to(Position2D(x=0.0, y=0.0))
        motion.wait_until_stopped(timeout=60.0)
        print("    -> Returned to Home.")

    except Exception as e:
        print(f"\nCRITICAL ERROR during motion: {e}")
        import traceback
        traceback.print_exc()
        
        print("    -> Attempting Emergency Stop...")
        try:
            motion.emergency_stop()
        except:
            pass
            
    finally:
        print("\n[8] Closing Connection...")
        lifecycle.close_all()
        print("    -> Closed.")
        print("==================================================")

if __name__ == "__main__":
    verify_motion()
