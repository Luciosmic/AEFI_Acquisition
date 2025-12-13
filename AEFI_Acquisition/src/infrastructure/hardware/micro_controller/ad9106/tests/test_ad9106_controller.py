"""
Diagram-friendly tests for AD9106Controller.

Tests the low-level DDS hardware control with structured interaction logging
for sequence diagram generation.
"""

import sys
import unittest
from pathlib import Path

# Add src to path
src_dir = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(src_dir))

# Add .cursor/skills to path for diagram_friendly_test
cursor_skills_dir = Path(__file__).resolve().parents[5] / ".cursor" / "skills"
sys.path.insert(0, str(cursor_skills_dir / "diagram_friendly_test"))

from diagram_friendly_test import DiagramFriendlyTest
from infrastructure.hardware.micro_controller.MCU_serial_communicator import MCU_SerialCommunicator
from infrastructure.hardware.micro_controller.ad9106.ad9106_controller import AD9106Controller
from domain.shared.operation_result import OperationResult


class TestAD9106Controller(DiagramFriendlyTest):
    """Test AD9106Controller with diagram-friendly logging."""
    
    def setUp(self):
        super().setUp()
        self.communicator = None
        self.controller = None
    
    def test_set_dds_frequency(self):
        """Test frequency configuration."""
        self.log_divider("Setup Phase")
        
        self.log_interaction(
            actor="TestAD9106",
            action="CREATE",
            target="MCU_SerialCommunicator",
            message="Create MCU communicator (mock/singleton)",
            data={"type": "singleton"}
        )
        self.communicator = MCU_SerialCommunicator()
        
        self.log_interaction(
            actor="TestAD9106",
            action="CREATE",
            target="AD9106Controller",
            message="Create AD9106Controller with communicator",
            data={"communicator_type": type(self.communicator).__name__}
        )
        self.controller = AD9106Controller(self.communicator)
        
        self.log_divider("Execution Phase - Set Frequency")
        
        freq_hz = 1000.0
        self.log_interaction(
            actor="TestAD9106",
            action="CALL",
            target="AD9106Controller",
            message="set_dds_frequency() - Configure DDS frequency",
            data={"frequency_hz": freq_hz}
        )
        result = self.controller.set_dds_frequency(freq_hz)
        
        self.log_interaction(
            actor="AD9106Controller",
            action="RETURN",
            target="TestAD9106",
            message="Frequency configuration result",
            data={"success": result.is_success, "error": result.error if result.is_failure else None}
        )
        
        self.log_divider("Verification Phase")
        
        self.log_interaction(
            actor="TestAD9106",
            action="ASSERT",
            target="AD9106Controller",
            message="Verify frequency set successfully",
            expect="OperationResult.is_success = True",
            got=f"OperationResult.is_success = {result.is_success}"
        )
        self.assertTrue(result.is_success, f"Frequency set failed: {result.error if result.is_failure else 'OK'}")
        
        # Verify memory state
        memory_state = self.controller.get_memory_state()
        self.log_interaction(
            actor="TestAD9106",
            action="QUERY",
            target="AD9106Controller",
            message="get_memory_state() - Retrieve current configuration",
            data={}
        )
        
        self.log_interaction(
            actor="AD9106Controller",
            action="RETURN",
            target="TestAD9106",
            message="Memory state retrieved",
            data={"frequency": memory_state["DDS"]["Frequence"]}
        )
        
        self.log_interaction(
            actor="TestAD9106",
            action="ASSERT",
            target="AD9106Controller",
            message="Verify frequency stored in memory state",
            expect=freq_hz,
            got=memory_state["DDS"]["Frequence"]
        )
        self.assertAlmostEqual(memory_state["DDS"]["Frequence"], freq_hz, places=0)
    
    def test_set_dds_gain(self):
        """Test gain configuration for a channel."""
        self.log_divider("Setup Phase")
        
        self.communicator = MCU_SerialCommunicator()
        self.controller = AD9106Controller(self.communicator)
        
        self.log_divider("Execution Phase - Set Gain")
        
        channel = 1
        gain_value = 5000
        self.log_interaction(
            actor="TestAD9106",
            action="CALL",
            target="AD9106Controller",
            message="set_dds_gain() - Configure DDS channel gain",
            data={"channel": channel, "gain": gain_value}
        )
        result = self.controller.set_dds_gain(channel, gain_value)
        
        self.log_interaction(
            actor="AD9106Controller",
            action="RETURN",
            target="TestAD9106",
            message="Gain configuration result",
            data={"success": result.is_success}
        )
        
        self.log_divider("Verification Phase")
        
        self.log_interaction(
            actor="TestAD9106",
            action="ASSERT",
            target="AD9106Controller",
            message="Verify gain set successfully",
            expect="OperationResult.is_success = True",
            got=f"OperationResult.is_success = {result.is_success}"
        )
        self.assertTrue(result.is_success)
        
        memory_state = self.controller.get_memory_state()
        self.log_interaction(
            actor="TestAD9106",
            action="ASSERT",
            target="AD9106Controller",
            message="Verify gain stored in memory state",
            expect=gain_value,
            got=memory_state["DDS"]["Gain"][channel]
        )
        self.assertEqual(memory_state["DDS"]["Gain"][channel], gain_value)
    
    def test_set_dds_modes(self):
        """Test mode configuration (AC/DC) for all channels."""
        self.log_divider("Setup Phase")
        
        self.communicator = MCU_SerialCommunicator()
        self.controller = AD9106Controller(self.communicator)
        
        self.log_divider("Execution Phase - Set Modes")
        
        self.log_interaction(
            actor="TestAD9106",
            action="CALL",
            target="AD9106Controller",
            message="set_dds_modes() - Configure AC/DC modes for all channels",
            data={"dds1_ac": True, "dds2_ac": True, "dds3_ac": True, "dds4_ac": True}
        )
        result = self.controller.set_dds_modes(
            dds1_ac=True,
            dds2_ac=True,
            dds3_ac=True,
            dds4_ac=True
        )
        
        self.log_interaction(
            actor="AD9106Controller",
            action="RETURN",
            target="TestAD9106",
            message="Mode configuration result",
            data={"success": result.is_success}
        )
        
        self.log_divider("Verification Phase")
        
        self.log_interaction(
            actor="TestAD9106",
            action="ASSERT",
            target="AD9106Controller",
            message="Verify modes set successfully",
            expect="OperationResult.is_success = True",
            got=f"OperationResult.is_success = {result.is_success}"
        )
        self.assertTrue(result.is_success)
        
        memory_state = self.controller.get_memory_state()
        self.log_interaction(
            actor="TestAD9106",
            action="ASSERT",
            target="AD9106Controller",
            message="Verify all channels in AC mode",
            expect="AC",
            got=memory_state["DDS"]["Mode"][1]
        )
        self.assertEqual(memory_state["DDS"]["Mode"][1], "AC")
        self.assertEqual(memory_state["DDS"]["Mode"][2], "AC")
        self.assertEqual(memory_state["DDS"]["Mode"][3], "AC")
        self.assertEqual(memory_state["DDS"]["Mode"][4], "AC")


if __name__ == '__main__':
    unittest.main()

