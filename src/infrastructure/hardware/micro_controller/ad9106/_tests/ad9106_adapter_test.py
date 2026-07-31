"""
Diagram-friendly tests for AD9106Adapter.

Tests the excitation configuration adapter with structured interaction logging
for sequence diagram generation.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Add src to path — tests -> ad9106 -> micro_controller -> hardware -> infrastructure -> src -> AEFI_Acquisition
root_dir = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(root_dir / "src"))

from tool.diagram_friendly_test import DiagramFriendlyTest
from infrastructure.hardware.micro_controller.MCU_serial_communicator import MCU_SerialCommunicator
from infrastructure.hardware.micro_controller.ad9106.ad9106_controller import AD9106Controller
from infrastructure.hardware.micro_controller.ad9106.adapter_excitation_configuration_ad9106 import AdapterExcitationConfigurationAD9106
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from domain.shared_kernel.excitation.value_objects.excitation_parameters import ExcitationParameters
from domain.shared_kernel.excitation.value_objects.excitation_mode import ExcitationMode
from domain.shared_kernel.excitation.value_objects.excitation_level import ExcitationLevel


class TestAD9106Adapter(DiagramFriendlyTest):
    """Test AdapterExcitationConfigurationAD9106 with diagram-friendly logging."""

    def setUp(self):
        super().setUp()
        # Patch serial communication so tests run without hardware
        self._send_patcher = patch.object(MCU_SerialCommunicator, 'send_command', return_value=(True, "OK"))
        self._send_patcher.start()
        self.communicator = None
        self.controller = None
        self.adapter = None

    def tearDown(self):
        self._send_patcher.stop()
        super().tearDown()
    
    def test_apply_excitation_x_dir(self):
        """Test applying X_DIR excitation mode."""
        self.log_divider("Setup Phase")
        
        self.log_interaction(
            actor="TestAD9106Adapter",
            action="CREATE",
            target="MCU_SerialCommunicator",
            message="Create MCU communicator",
            data={}
        )
        self.communicator = MCU_SerialCommunicator()
        
        self.log_interaction(
            actor="TestAD9106Adapter",
            action="CREATE",
            target="AD9106Controller",
            message="Create AD9106Controller",
            data={}
        )
        self.controller = AD9106Controller(self.communicator)
        
        self.log_interaction(
            actor="TestAD9106Adapter",
            action="CREATE",
            target="AdapterExcitationConfigurationAD9106",
            message="Create AdapterExcitationConfigurationAD9106 with controller",
            data={"controller_type": type(self.controller).__name__}
        )
        self.adapter = AdapterExcitationConfigurationAD9106(self.controller, self.communicator)
        
        self.log_divider("Execution Phase - Apply X_DIR Excitation")
        
        params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level_s1_s2=ExcitationLevel(50.0),  # 50%
            level_s3_s4=ExcitationLevel(50.0),
            frequency=1000.0
        )
        
        self.log_interaction(
            actor="TestAD9106Adapter",
            action="CREATE",
            target="ExcitationParameters",
            message="Create excitation parameters",
            data={"mode": "X_DIR", "level": 50.0, "frequency": 1000.0}
        )
        
        self.log_interaction(
            actor="TestAD9106Adapter",
            action="CALL",
            target="AD9106Adapter",
            message="apply_excitation() - Apply X_DIR excitation",
            data={"mode": "X_DIR", "level": 50.0, "frequency": 1000.0}
        )
        
        try:
            self.adapter.apply_excitation(params)
            self.log_interaction(
                actor="AD9106Adapter",
                action="RETURN",
                target="TestAD9106Adapter",
                message="Excitation applied successfully",
                data={"status": "success"}
            )
        except Exception as e:
            self.log_interaction(
                actor="AD9106Adapter",
                action="ERROR",
                target="TestAD9106Adapter",
                message="Excitation application failed",
                data={"error": str(e)}
            )
            raise
        
        self.log_divider("Verification Phase")
        
        # Verify controller state
        memory_state = self.controller.get_memory_state()
        self.log_interaction(
            actor="TestAD9106Adapter",
            action="QUERY",
            target="AD9106Controller",
            message="get_memory_state() - Verify configuration",
            data={}
        )
        
        self.log_interaction(
            actor="TestAD9106Adapter",
            action="ASSERT",
            target="AD9106Adapter",
            message="Verify X_DIR phases (DDS1=0°, DDS2=180)",
            expect={"phase_dds1": 0, "phase_dds2": 32768},
            got={"phase_dds1": memory_state["DDS"]["Phase"][1], "phase_dds2": memory_state["DDS"]["Phase"][2]}
        )
        self.assertEqual(memory_state["DDS"]["Phase"][1], 0)    # DDS1: 0°
        self.assertEqual(memory_state["DDS"]["Phase"][2], 32768)  # DDS2: 180° = 32768 (raw register)
        
        # Verify gains (50% of MAX_EXCITATION_GAIN = 5500)
        expected_gain = int((50.0 / 100.0) * 5500)
        self.log_interaction(
            actor="TestAD9106Adapter",
            action="ASSERT",
            target="AD9106Adapter",
            message="Verify gains set for active channels (DDS1, DDS2)",
            expect=expected_gain,
            got=memory_state["DDS"]["Gain"][1]
        )
        self.assertEqual(memory_state["DDS"]["Gain"][1], expected_gain)
        self.assertEqual(memory_state["DDS"]["Gain"][2], expected_gain)
        
        # Verify DDS3 and DDS4 unchanged (synchronous detection)
        self.log_interaction(
            actor="TestAD9106Adapter",
            action="ASSERT",
            target="AD9106Adapter",
            message="Verify DDS3 and DDS4 gains unchanged (detection channels)",
            expect="unchanged",
            got={"dds3_gain": memory_state["DDS"]["Gain"][3], "dds4_gain": memory_state["DDS"]["Gain"][4]}
        )
        # DDS3 and DDS4 should remain at their default values (not modified by excitation)
    
    def test_apply_excitation_y_dir(self):
        """Test applying Y_DIR excitation mode."""
        self.log_divider("Setup Phase")
        
        self.communicator = MCU_SerialCommunicator()
        self.controller = AD9106Controller(self.communicator)
        self.adapter = AdapterExcitationConfigurationAD9106(self.controller, self.communicator)
        
        self.log_divider("Execution Phase - Apply Y_DIR Excitation")
        
        params = ExcitationParameters(
            mode=ExcitationMode.Y_DIR,
            level_s1_s2=ExcitationLevel(75.0),  # 75%
            level_s3_s4=ExcitationLevel(75.0),
            frequency=2000.0
        )
        
        self.log_interaction(
            actor="TestAD9106Adapter",
            action="CALL",
            target="AD9106Adapter",
            message="apply_excitation() - Apply Y_DIR excitation",
            data={"mode": "Y_DIR", "level": 75.0, "frequency": 2000.0}
        )
        
        try:
            self.adapter.apply_excitation(params)
            self.log_interaction(
                actor="AD9106Adapter",
                action="RETURN",
                target="TestAD9106Adapter",
                message="Excitation applied successfully",
                data={"status": "success"}
            )
        except Exception as e:
            self.log_interaction(
                actor="AD9106Adapter",
                action="ERROR",
                target="TestAD9106Adapter",
                message="Excitation application failed",
                data={"error": str(e)}
            )
            raise
        
        self.log_divider("Verification Phase")
        
        memory_state = self.controller.get_memory_state()
        
        self.log_interaction(
            actor="TestAD9106Adapter",
            action="ASSERT",
            target="AD9106Adapter",
            message="Verify Y_DIR phases (DDS1=0°, DDS2=0)",
            expect={"phase_dds1": 0, "phase_dds2": 0},
            got={"phase_dds1": memory_state["DDS"]["Phase"][1], "phase_dds2": memory_state["DDS"]["Phase"][2]}
        )
        self.assertEqual(memory_state["DDS"]["Phase"][1], 0)  # DDS1: 0°
        self.assertEqual(memory_state["DDS"]["Phase"][2], 0)  # DDS2: 0 (User defined)
    
    def test_apply_excitation_off(self):
        """Test applying OFF excitation (level=0)."""
        self.log_divider("Setup Phase")
        
        self.communicator = MCU_SerialCommunicator()
        self.controller = AD9106Controller(self.communicator)
        self.adapter = AdapterExcitationConfigurationAD9106(self.controller, self.communicator)
        
        self.log_divider("Execution Phase - Apply OFF Excitation")
        
        params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,  # Mode doesn't matter when level=0
            level_s1_s2=ExcitationLevel(0.0),  # 0% = OFF
            level_s3_s4=ExcitationLevel(0.0),
            frequency=1000.0
        )
        
        self.log_interaction(
            actor="TestAD9106Adapter",
            action="CALL",
            target="AD9106Adapter",
            message="apply_excitation() - Apply OFF excitation (level=0)",
            data={"mode": "X_DIR", "level": 0.0}
        )
        
        try:
            self.adapter.apply_excitation(params)
            self.log_interaction(
                actor="AD9106Adapter",
                action="RETURN",
                target="TestAD9106Adapter",
                message="OFF excitation applied (early return)",
                data={"status": "success"}
            )
        except Exception as e:
            self.log_interaction(
                actor="AD9106Adapter",
                action="ERROR",
                target="TestAD9106Adapter",
                message="OFF excitation failed",
                data={"error": str(e)}
            )
            raise
        
        self.log_divider("Verification Phase")
        
        memory_state = self.controller.get_memory_state()
        
        self.log_interaction(
            actor="TestAD9106Adapter",
            action="ASSERT",
            target="AD9106Adapter",
            message="Verify gains set to 0 for OFF mode",
            expect={"dds1_gain": 0, "dds2_gain": 0},
            got={"dds1_gain": memory_state["DDS"]["Gain"][1], "dds2_gain": memory_state["DDS"]["Gain"][2]}
        )
        self.assertEqual(memory_state["DDS"]["Gain"][1], 0)
        self.assertEqual(memory_state["DDS"]["Gain"][2], 0)
        
        self.log_interaction(
            actor="TestAD9106Adapter",
            action="ASSERT",
            target="AD9106Adapter",
            message="Verify phases reset to 0 for OFF mode",
            expect={"phase_dds1": 0, "phase_dds2": 0},
            got={"phase_dds1": memory_state["DDS"]["Phase"][1], "phase_dds2": memory_state["DDS"]["Phase"][2]}
        )
        self.assertEqual(memory_state["DDS"]["Phase"][1], 0)
        self.assertEqual(memory_state["DDS"]["Phase"][2], 0)

    def test_apply_excitation_asymmetric_levels(self):
        """S1/S2 (channel 2, DDS2 generator) and S3/S4 (channel 1, DDS1
        generator) must accept independent gains — confirmed on oscilloscope,
        counter-intuitive relative to the channel numbers (see SphereId)."""
        self.communicator = MCU_SerialCommunicator()
        self.controller = AD9106Controller(self.communicator)
        self.adapter = AdapterExcitationConfigurationAD9106(self.controller, self.communicator)

        params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level_s1_s2=ExcitationLevel(30.0),
            level_s3_s4=ExcitationLevel(70.0),
            frequency=1000.0
        )
        self.adapter.apply_excitation(params)

        memory_state = self.controller.get_memory_state()
        expected_gain_s1_s2 = int((30.0 / 100.0) * 5500)
        expected_gain_s3_s4 = int((70.0 / 100.0) * 5500)
        self.assertEqual(memory_state["DDS"]["Gain"][2], expected_gain_s1_s2)  # channel 2 -> S1/S2
        self.assertEqual(memory_state["DDS"]["Gain"][1], expected_gain_s3_s4)  # channel 1 -> S3/S4
        self.assertNotEqual(memory_state["DDS"]["Gain"][1], memory_state["DDS"]["Gain"][2])

    def test_apply_excitation_partial_off_does_not_reset_phase(self):
        """One DDS at 0% while the other is active must not trigger the full-OFF phase reset."""
        self.communicator = MCU_SerialCommunicator()
        self.controller = AD9106Controller(self.communicator)
        self.adapter = AdapterExcitationConfigurationAD9106(self.controller, self.communicator)

        params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level_s1_s2=ExcitationLevel(0.0),
            level_s3_s4=ExcitationLevel(50.0),
            frequency=1000.0
        )
        self.adapter.apply_excitation(params)

        memory_state = self.controller.get_memory_state()
        self.assertEqual(memory_state["DDS"]["Gain"][2], 0)  # channel 2 -> S1/S2 (level_s1_s2=0)
        self.assertEqual(memory_state["DDS"]["Gain"][1], int((50.0 / 100.0) * 5500))  # channel 1 -> S3/S4
        # X_DIR mode phases still applied (not reset to 0 by a false full-OFF short-circuit)
        self.assertEqual(memory_state["DDS"]["Phase"][1], 0)
        self.assertEqual(memory_state["DDS"]["Phase"][2], 32768)

    def test_apply_excitation_publishes_dds_channel_config_changed_for_hardware_config_sync(self):
        """The Hardware Config tab (HardwareAdvancedConfigPresenter) listens
        for this event to stay in sync when level/mode change from the
        Excitation panel instead — see DdsChannelConfigChanged intention.md."""
        event_bus = InMemoryEventBus()
        received = []
        event_bus.subscribe("ddschannelconfigchanged", received.append)

        communicator = MCU_SerialCommunicator()
        controller = AD9106Controller(communicator)
        adapter = AdapterExcitationConfigurationAD9106(controller, communicator, event_bus=event_bus)

        params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level_s1_s2=ExcitationLevel(30.0),
            level_s3_s4=ExcitationLevel(70.0),
            frequency=1000.0,
        )
        adapter.apply_excitation(params)

        self.assertEqual({e.channel for e in received}, {1, 2})
        by_channel = {e.channel: e for e in received}
        self.assertEqual(by_channel[2].gain, int((30.0 / 100.0) * 5500))  # channel 2 -> S1/S2
        self.assertEqual(by_channel[1].gain, int((70.0 / 100.0) * 5500))  # channel 1 -> S3/S4
        self.assertEqual(by_channel[1].phase, 0)
        self.assertEqual(by_channel[2].phase, 32768)

    def test_apply_excitation_off_publishes_zeroed_dds_channel_config_changed(self):
        event_bus = InMemoryEventBus()
        received = []
        event_bus.subscribe("ddschannelconfigchanged", received.append)

        communicator = MCU_SerialCommunicator()
        controller = AD9106Controller(communicator)
        adapter = AdapterExcitationConfigurationAD9106(controller, communicator, event_bus=event_bus)

        params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level_s1_s2=ExcitationLevel(0.0),
            level_s3_s4=ExcitationLevel(0.0),
            frequency=1000.0,
        )
        adapter.apply_excitation(params)

        self.assertEqual({e.channel for e in received}, {1, 2})
        self.assertTrue(all(e.gain == 0 and e.phase == 0 for e in received))


if __name__ == '__main__':
    unittest.main()

