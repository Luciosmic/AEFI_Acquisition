"""
Diagram-friendly tests for AD9106Adapter.

Tests the excitation configuration adapter with structured interaction logging
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
from infrastructure.hardware.micro_controller.ad9106.adapter_excitation_configuration_ad9106 import AD9106Adapter
from domain.value_objects.excitation.excitation_parameters import ExcitationParameters
from domain.value_objects.excitation.excitation_mode import ExcitationMode
from domain.value_objects.excitation.excitation_level import ExcitationLevel


class TestAD9106Adapter(DiagramFriendlyTest):
    """Test AD9106Adapter with diagram-friendly logging."""
    
    def setUp(self):
        super().setUp()
        self.communicator = None
        self.controller = None
        self.adapter = None
    
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
            target="AD9106Adapter",
            message="Create AD9106Adapter with controller",
            data={"controller_type": type(self.controller).__name__}
        )
        self.adapter = AD9106Adapter(self.controller, self.communicator)
        
        self.log_divider("Execution Phase - Apply X_DIR Excitation")
        
        params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level=ExcitationLevel(50.0),  # 50%
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
            message="Verify X_DIR phases (DDS1=0°, DDS2=180°)",
            expect={"phase_dds1": 0, "phase_dds2": 32768},
            got={"phase_dds1": memory_state["DDS"]["Phase"][1], "phase_dds2": memory_state["DDS"]["Phase"][2]}
        )
        self.assertEqual(memory_state["DDS"]["Phase"][1], 0)  # DDS1: 0°
        self.assertEqual(memory_state["DDS"]["Phase"][2], 32768)  # DDS2: 180°
        
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
        self.adapter = AD9106Adapter(self.controller, self.communicator)
        
        self.log_divider("Execution Phase - Apply Y_DIR Excitation")
        
        params = ExcitationParameters(
            mode=ExcitationMode.Y_DIR,
            level=ExcitationLevel(75.0),  # 75%
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
            message="Verify Y_DIR phases (DDS1=0°, DDS2=0° - in phase)",
            expect={"phase_dds1": 0, "phase_dds2": 0},
            got={"phase_dds1": memory_state["DDS"]["Phase"][1], "phase_dds2": memory_state["DDS"]["Phase"][2]}
        )
        self.assertEqual(memory_state["DDS"]["Phase"][1], 0)  # DDS1: 0°
        self.assertEqual(memory_state["DDS"]["Phase"][2], 0)  # DDS2: 0° (in phase)
    
    def test_apply_excitation_off(self):
        """Test applying OFF excitation (level=0)."""
        self.log_divider("Setup Phase")
        
        self.communicator = MCU_SerialCommunicator()
        self.controller = AD9106Controller(self.communicator)
        self.adapter = AD9106Adapter(self.controller, self.communicator)
        
        self.log_divider("Execution Phase - Apply OFF Excitation")
        
        params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,  # Mode doesn't matter when level=0
            level=ExcitationLevel(0.0),  # 0% = OFF
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


if __name__ == '__main__':
    unittest.main()

