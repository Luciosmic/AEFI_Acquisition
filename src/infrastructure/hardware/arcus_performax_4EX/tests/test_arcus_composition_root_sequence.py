import unittest
import sys
from pathlib import Path

# Ensure src is in path
src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from tool.diagram_friendly_test import DiagramFriendlyTest
from infrastructure.hardware.arcus_performax_4EX.composition_root_arcus import ArcusCompositionRoot
from application.services.motion_control_service.i_motion_port import IMotionPort
from application.services.system_lifecycle_service.i_hardware_initialization_port import IHardwareInitializationPort
from application.services.hardware_configuration_service.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator

class TestArcusCompositionRootSequence(DiagramFriendlyTest):
    def test_composition_root_wiring(self):
        self.log_divider("Composition Root Initialization")
        
        # 1. Instantiate Composition Root
        self.log_interaction("Test", "CREATE", "ArcusCompositionRoot", "Initialize Root")
        root = ArcusCompositionRoot(port="COM_TEST")
        
        # 2. Verify Ports Exposed
        self.log_interaction("Test", "VERIFY", "ArcusCompositionRoot", "Check Exposed Ports")
        
        self.assertIsInstance(root.motion, IMotionPort)
        self.log_interaction("ArcusCompositionRoot", "EXPOSE", "IMotionPort", "root.motion")
        
        self.assertIsInstance(root.lifecycle, IHardwareInitializationPort)
        self.log_interaction("ArcusCompositionRoot", "EXPOSE", "IHardwareInitializationPort", "root.lifecycle")
        
        self.assertIsInstance(root.config, IHardwareAdvancedConfigurator)
        self.log_interaction("ArcusCompositionRoot", "EXPOSE", "IHardwareAdvancedConfigurator", "root.config")
        
        # 3. Verify Internal Wiring (Shared Driver)
        self.log_divider("Internal Wiring Verification")
        self.log_interaction("Test", "INSPECT", "ArcusCompositionRoot", "Check Shared Driver")
        
        driver = root._driver
        motion_controller = root.motion._controller
        config_controller = root.config._controller
        
        self.assertIsNotNone(driver)
        self.assertIsNotNone(motion_controller)
        self.assertIsNotNone(config_controller)
        
        self.assertEqual(driver, motion_controller)
        self.log_interaction("ArcusCompositionRoot", "WIRE", "ArcusAdapter", "Injected Shared Driver")
        
        self.assertEqual(driver, config_controller)
        self.log_interaction("ArcusCompositionRoot", "WIRE", "ArcusConfigurator", "Injected Shared Driver")

if __name__ == '__main__':
    unittest.main()
