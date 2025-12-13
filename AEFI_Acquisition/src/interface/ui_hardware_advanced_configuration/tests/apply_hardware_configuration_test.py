"""
Diagram-friendly integration test:
UI (GenericHardwareConfigTab) → HardwareConfigurationService → MockHardwareConfigProvider.

Responsibility:
- Verify that changing a UI control (HS spinbox) propagates a speed parameter (HS)
  through the application layer to a mock hardware provider implementing
  IHardwareConfigProvider, while producing a JSON trace for sequence diagrams.
"""

import sys
import unittest
from pathlib import Path
from typing import List

from PyQt6.QtWidgets import QApplication

# Ensure src is on sys.path (we're in src/interface/ui_hardware_configuration/tests/)
# File layout: src/interface/ui_hardware_configuration/tests/...
# parents[4] == <project_root>/src
SRC = Path(__file__).parents[4]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from interface.ui_hardware_configuration.widget_generic_hardware_config import (
    GenericHardwareConfigTab,
)
from interface.ui_hardware_configuration.parameter_spec import ParameterSpec
from application.hardware_configuration_service.hardware_configuration_service import (
    HardwareConfigurationService,
)
from infrastructure.tests.mock_ports import MockHardwareConfigProvider
from infrastructure.tests.diagram_friendly_test import DiagramFriendlyTest


class TestApplyHardwareConfiguration(DiagramFriendlyTest):
    """
    Diagram-friendly test for hardware configuration application from UI.
    """

    @classmethod
    def setUpClass(cls):
        # Create a single QApplication instance for all tests in this class
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self):
        super().setUp()

        # Arrange: mock hardware provider + application service
        self.log_interaction(
            "TestApplyHardwareConfiguration",
            "CREATE",
            "MockHardwareConfigProvider",
            "Instantiate mock hardware config provider",
        )
        self.provider = MockHardwareConfigProvider(hardware_id="mock_hardware")

        self.log_interaction(
            "TestApplyHardwareConfiguration",
            "CREATE",
            "HardwareConfigurationService",
            "Create service with mock provider",
            data={"providers": ["mock_hardware"]},
        )
        self.service = HardwareConfigurationService([self.provider])

        # Minimal UI spec for a single high-speed parameter
        specs: List[ParameterSpec] = [
            ParameterSpec(
                name="hs",
                label="High Speed",
                type="spinbox",
                default=1500,
                range=(10, 10000),
                unit="Hz",
            )
        ]

        self.log_interaction(
            "TestApplyHardwareConfiguration",
            "CREATE",
            "GenericHardwareConfigTab",
            "Create UI tab for mock hardware speed config",
        )
        self.tab = GenericHardwareConfigTab(
            title="Mock Hardware Config",
            param_specs=specs,
        )

        # When UI config changes, route through application service
        def on_config_changed(cfg: dict) -> None:
            hs_value = cfg.get("hs")
            self.log_interaction(
                "UI",
                "CALL",
                "HardwareConfigurationService",
                "apply_config(hardware_id='mock_hardware')",
                data={"hs": hs_value},
            )
            self.service.apply_config("mock_hardware", {"hs": hs_value})
            self.log_interaction(
                "HardwareConfigurationService",
                "RETURN",
                "UI",
                "Configuration applied",
                data={"applied_hs": self.provider.applied_hs},
            )

        self.log_interaction(
            "UI",
            "SUBSCRIBE",
            "GenericHardwareConfigTab",
            "Subscribe to config_changed signal",
        )
        self.tab.config_changed.connect(on_config_changed)

    def test_hardware_configuration_flow(self):
        """
        End-to-end flow:
        UI spinbox 'hs' -> GenericHardwareConfigTab -> config_changed signal
        -> HardwareConfigurationService.apply_config
        -> MockHardwareConfigProvider.apply_config (captures hs).
        """
        new_hs = 2000

        self.log_interaction(
            "TestApplyHardwareConfiguration",
            "CALL",
            "UI",
            "User sets HS spinbox",
            data={"hs": new_hs},
        )
        self.tab._widgets["hs"].setValue(new_hs)

        self.log_interaction(
            "TestApplyHardwareConfiguration",
            "ASSERT",
            "MockHardwareConfigProvider",
            "Verify HS applied via provider",
            expect=float(new_hs),
            got=self.provider.applied_hs,
        )
        self.assertEqual(self.provider.applied_hs, float(new_hs))
        self.assertEqual(self.provider.last_config.get("hs"), new_hs)


if __name__ == "__main__":
    unittest.main()



