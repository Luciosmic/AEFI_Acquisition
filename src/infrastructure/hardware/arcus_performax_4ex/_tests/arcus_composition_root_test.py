import unittest
import sys
from pathlib import Path

src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from infrastructure.hardware.arcus_performax_4EX.composition_root_arcus import ArcusCompositionRoot
from application.services.motion_control_service.ports.i_motion_port import IMotionPort
from application.services.system_lifecycle_service.ports.i_hardware_initialization_port import IHardwareInitializationPort
from application.services.hardware_configuration_service.ports.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator

class TestArcusCompositionRoot(unittest.TestCase):
    def test_instantiation_and_wiring(self):
        root = ArcusCompositionRoot(port="COM_TEST")

        self.assertIsInstance(root.motion, IMotionPort)
        self.assertIsInstance(root.lifecycle, IHardwareInitializationPort)
        self.assertIsInstance(root.config, IHardwareAdvancedConfigurator)

if __name__ == '__main__':
    unittest.main()
