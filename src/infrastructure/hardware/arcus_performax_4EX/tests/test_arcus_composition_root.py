import unittest
import sys
from pathlib import Path

# Ensure src is in path
src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from infrastructure.hardware.arcus_performax_4EX.composition_root_arcus import ArcusCompositionRoot
from application.services.motion_control_service.i_motion_port import IMotionPort
from application.services.system_lifecycle_service.i_hardware_initialization_port import IHardwareInitializationPort
from application.services.hardware_configuration_service.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator

class TestArcusCompositionRoot(unittest.TestCase):
    def test_instantiation_and_wiring(self):
        # Act
        root = ArcusCompositionRoot(port="COM_TEST")
        
        # Assert
        self.assertIsInstance(root.motion, IMotionPort)
        self.assertIsInstance(root.lifecycle, IHardwareInitializationPort)
        self.assertIsInstance(root.config, IHardwareAdvancedConfigurator)
        
        # Verify wiring (internal check)
        # Check if motion adapter has the driver injected
        self.assertIsNotNone(root.motion._controller)
        self.assertEqual(root.motion._controller, root._driver)
        
        # Check if config has the same driver
        self.assertEqual(root.config._controller, root._driver)

if __name__ == '__main__':
    unittest.main()
