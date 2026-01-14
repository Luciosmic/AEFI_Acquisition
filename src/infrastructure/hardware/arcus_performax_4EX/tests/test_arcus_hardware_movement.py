import unittest
import sys
import time
from pathlib import Path

# Ensure src is in path
src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from tool.diagram_friendly_test import DiagramFriendlyTest
from infrastructure.hardware.arcus_performax_4EX.composition_root_arcus import ArcusCompositionRoot
from domain.value_objects.geometric.position_2d import Position2D

class TestArcusHardwareMovement(DiagramFriendlyTest):
    def test_hardware_movement_sequence(self):
        self.log_divider("Arcus Hardware Movement Test")
        
        # 1. Initialize
        self.log_interaction("Test", "CREATE", "ArcusCompositionRoot", "Initialize Hardware")
        try:
            root = ArcusCompositionRoot()
            motion = root.motion
            lifecycle = root.lifecycle
            
            # Connect
            self.log_interaction("Test", "CALL", "ArcusLifecycle", "initialize_all()")
            lifecycle.initialize_all()
            self.log_interaction("ArcusLifecycle", "CONNECT", "ArcusController", "Connect to Hardware")
            
        except Exception as e:
            self.fail(f"Initialization failed: {e}")

        try:
            # 2. Home
            self.log_divider("Homing Sequence")
            self.log_interaction("Test", "CALL", "ArcusAdapter", "home()")
            motion.home()
            
            self.log_interaction("Test", "WAIT", "ArcusAdapter", "wait_until_stopped()")
            motion.wait_until_stopped(timeout=60.0)
            
            # Check position
            pos = motion.get_current_position()
            self.log_interaction("ArcusAdapter", "RETURN", "Test", f"Position: {pos}")

            # 3. Move to 20cm (200mm)
            self.log_divider("Move to 200mm")
            target_pos = Position2D(x=200.0, y=200.0)
            
            self.log_interaction("Test", "CALL", "ArcusAdapter", f"move_to({target_pos})")
            motion.move_to(target_pos)
            
            self.log_interaction("Test", "WAIT", "ArcusAdapter", "wait_until_stopped()")
            motion.wait_until_stopped(timeout=60.0)
            
            pos = motion.get_current_position()
            self.log_interaction("ArcusAdapter", "RETURN", "Test", f"Position: {pos}")
            
            # Optional: Wait a bit
            time.sleep(1.0)
            
            # 4. Move back to Home (0,0)
            self.log_divider("Return to Home")
            home_pos = Position2D(x=0.0, y=0.0)
            
            self.log_interaction("Test", "CALL", "ArcusAdapter", f"move_to({home_pos})")
            motion.move_to(home_pos)
            
            self.log_interaction("Test", "WAIT", "ArcusAdapter", "wait_until_stopped()")
            motion.wait_until_stopped(timeout=60.0)
            
            pos = motion.get_current_position()
            self.log_interaction("ArcusAdapter", "RETURN", "Test", f"Final Position: {pos}")
            
        except Exception as e:
            self.log_interaction("Test", "ERROR", "ArcusAdapter", str(e))
            # Emergency stop if something goes wrong
            try:
                motion.emergency_stop()
                self.log_interaction("Test", "CALL", "ArcusAdapter", "emergency_stop()")
            except:
                pass
            self.fail(f"Test failed: {e}")
            
        finally:
            # 5. Cleanup
            self.log_divider("Cleanup")
            self.log_interaction("Test", "CALL", "ArcusLifecycle", "close_all()")
            lifecycle.close_all()

if __name__ == "__main__":
    unittest.main()
