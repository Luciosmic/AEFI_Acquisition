import unittest
import sys
from pathlib import Path

src_path = Path(__file__).resolve().parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from infrastructure.hardware.hardware_composition_root import HardwareCompositionRoot
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from application.services.motion_control_service.ports.i_motion_port import IMotionPort
from application.services.scan_application_service.ports.i_acquisition_port import IAcquisitionPort
from application.services.excitation_configuration_service.ports.i_excitation_port import IExcitationPort
from application.services.electric_field_probe_service.ports.i_electric_field_probe_port import IElectricFieldProbePort


class TestHardwareCompositionRoot(unittest.TestCase):
    def test_all_mock_wiring(self):
        hw = HardwareCompositionRoot(
            hardware_config={"motion": "mock", "aefi_device": "mock", "electric_field_probe": "mock"},
            event_bus=InMemoryEventBus(),
            narda_com_port="COM_TEST",
        )

        self.assertIsInstance(hw.motion_port, IMotionPort)
        self.assertIsInstance(hw.acquisition_port, IAcquisitionPort)
        self.assertIsInstance(hw.excitation_port, IExcitationPort)
        self.assertIsInstance(hw.probe_port, IElectricFieldProbePort)
        self.assertEqual(len(hw.lifecycle_adapters), 2)


if __name__ == '__main__':
    unittest.main()
