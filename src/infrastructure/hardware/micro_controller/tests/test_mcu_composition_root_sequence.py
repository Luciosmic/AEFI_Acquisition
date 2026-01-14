import unittest
import sys
from pathlib import Path

# Ensure src is in path
src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from tool.diagram_friendly_test import DiagramFriendlyTest
from infrastructure.hardware.micro_controller.mcu_composition_root import MCUCompositionRoot
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from application.services.scan_application_service.i_acquisition_port import IAcquisitionPort
from application.services.system_lifecycle_service.i_hardware_initialization_port import IHardwareInitializationPort
from application.services.continuous_acquisition_service.i_continuous_acquisition_executor import IContinuousAcquisitionExecutor

class TestMCUCompositionRootSequence(DiagramFriendlyTest):
    def test_composition_root_wiring(self):
        self.log_divider("Composition Root Initialization")
        
        # 1. Setup Dependencies
        self.log_interaction("Test", "CREATE", "EventBus", "Initialize EventBus")
        event_bus = InMemoryEventBus()
        
        # 2. Instantiate Composition Root
        self.log_interaction("Test", "CREATE", "MCUCompositionRoot", "Initialize Root")
        root = MCUCompositionRoot(event_bus=event_bus, port="COM_TEST")
        
        # 3. Verify Ports Exposed
        self.log_interaction("Test", "VERIFY", "MCUCompositionRoot", "Check Exposed Ports")
        
        self.assertIsInstance(root.acquisition, IAcquisitionPort)
        self.log_interaction("MCUCompositionRoot", "EXPOSE", "IAcquisitionPort", "root.acquisition")
        
        self.assertIsInstance(root.lifecycle, IHardwareInitializationPort)
        self.log_interaction("MCUCompositionRoot", "EXPOSE", "IHardwareInitializationPort", "root.lifecycle")
        
        self.assertIsInstance(root.continuous, IContinuousAcquisitionExecutor)
        self.log_interaction("MCUCompositionRoot", "EXPOSE", "IContinuousAcquisitionExecutor", "root.continuous")
        
        # 4. Verify Internal Wiring (Shared Driver)
        self.log_divider("Internal Wiring Verification")
        self.log_interaction("Test", "INSPECT", "MCUCompositionRoot", "Check Shared Driver")
        
        driver = root._driver
        acquisition_driver = root.acquisition._serial
        lifecycle_driver = root.lifecycle._communicator
        
        self.assertIsNotNone(driver)
        self.assertIsNotNone(acquisition_driver)
        self.assertIsNotNone(lifecycle_driver)
        
        self.assertEqual(driver, acquisition_driver)
        self.log_interaction("MCUCompositionRoot", "WIRE", "ADS131A04Adapter", "Injected Shared Driver")
        
        self.assertEqual(driver, lifecycle_driver)
        self.log_interaction("MCUCompositionRoot", "WIRE", "MCULifecycleAdapter", "Injected Shared Driver")
        
        # 5. Verify Continuous Adapter Wiring
        self.log_interaction("Test", "INSPECT", "AdapterIContinuousAcquisitionAds131a04", "Check EventBus")
        self.assertEqual(root.continuous._event_bus, event_bus)
        self.log_interaction("MCUCompositionRoot", "WIRE", "ContinuousAdapter", "Injected EventBus")

if __name__ == '__main__':
    unittest.main()
