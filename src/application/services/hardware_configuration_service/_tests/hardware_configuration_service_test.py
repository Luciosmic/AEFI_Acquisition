import unittest
from typing import List
import sys
from pathlib import Path

# Ensure src is on sys.path when running this file directly
ROOT = Path(__file__).parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from application.services.hardware_configuration_service.hardware_configuration_service import (
    HardwareConfigurationService,
)
from domain.value_objects.hardware_configuration.hardware_advanced_parameter_schema import (
    HardwareAdvancedParameterSchema,
)
from infrastructure.hardware.arcus_performax_4EX.arcus_advanced_configuration import (
    ArcusPerformax4EXAdvancedConfigurator,
)
from tool.diagram_friendly_test import DiagramFriendlyTest

# Stable hardware_id exposed by ArcusPerformax4EXAdvancedConfigurator
_ARCUS_HW_ID = "arcus_performax_4ex_advanced"


class TestHardwareConfigurationService(DiagramFriendlyTest):
    """
    Diagram-friendly test for HardwareConfigurationService.

    Responsibility:
    - Exercise the happy-path flow of discovering hardware and its parameters
    - Produce a JSON trace consumable by the generate_puml script
    """

    def setUp(self):
        super().setUp()

        # Arrange: create provider and service
        self.log_interaction(
            "Test",
            "CREATE",
            "ArcusPerformax4EXAdvancedConfigurator",
            "Instantiate Arcus hardware advanced configurator",
        )
        self.arcus_provider = ArcusPerformax4EXAdvancedConfigurator(controller=None, adapter=None)

        self.log_interaction(
            "Test",
            "CREATE",
            "HardwareConfigurationService",
            "Create service with Arcus advanced configurator",
            data={"providers": [_ARCUS_HW_ID]},
        )
        self.service = HardwareConfigurationService([self.arcus_provider])

    def test_hardware_config_discovery_flow(self):
        """End-to-end discovery of Arcus hardware config."""
        # List hardware ids
        self.log_interaction(
            "Test",
            "CALL",
            "HardwareConfigurationService",
            "list_hardware_ids()",
        )
        hardware_ids: List[str] = self.service.list_hardware_ids()

        self.log_interaction(
            "HardwareConfigurationService",
            "RETURN",
            "Test",
            "Hardware ids discovered",
            data={"hardware_ids": hardware_ids},
        )

        # Assert Arcus id present
        self.log_interaction(
            "Test",
            "ASSERT",
            "HardwareConfigurationService",
            "Verify Arcus hardware id present",
            expect=_ARCUS_HW_ID,
            got=hardware_ids[0] if hardware_ids else None,
        )
        self.assertIn(_ARCUS_HW_ID, hardware_ids)

        # Get display name
        self.log_interaction(
            "Test",
            "CALL",
            "HardwareConfigurationService",
            f"get_hardware_display_name('{_ARCUS_HW_ID}')",
        )
        display_name = self.service.get_hardware_display_name(_ARCUS_HW_ID)

        self.log_interaction(
            "HardwareConfigurationService",
            "RETURN",
            "Test",
            "Display name resolved",
            data={"display_name": display_name},
        )

        self.log_interaction(
            "Test",
            "ASSERT",
            "HardwareConfigurationService",
            "Verify display name non-empty",
            expect="non-empty string",
            got=display_name,
        )
        self.assertIsInstance(display_name, str)
        self.assertNotEqual(display_name.strip(), "")

        # Get parameter specs
        self.log_interaction(
            "Test",
            "CALL",
            "HardwareConfigurationService",
            f"get_parameter_specs('{_ARCUS_HW_ID}')",
        )
        specs: List[HardwareAdvancedParameterSchema] = self.service.get_parameter_specs(
            _ARCUS_HW_ID
        )

        self.log_interaction(
            "HardwareConfigurationService",
            "RETURN",
            "Test",
            "Parameter specs resolved",
            data={"count": len(specs)},
        )

        # Basic assertions on specs
        self.log_interaction(
            "Test",
            "ASSERT",
            "HardwareConfigurationService",
            "Verify at least one parameter spec",
            expect=">= 1",
            got=len(specs),
        )
        self.assertGreaterEqual(len(specs), 1)

        first_spec = specs[0]
        self.log_interaction(
            "Test",
            "ASSERT",
            "HardwareConfigurationService",
            "Verify first spec has key and display_name",
            expect="non-empty key/display_name",
            got={"key": first_spec.key, "display_name": first_spec.display_name},
        )
        self.assertIsInstance(first_spec.key, str)
        self.assertIsInstance(first_spec.display_name, str)
        self.assertNotEqual(first_spec.key.strip(), "")
        self.assertNotEqual(first_spec.display_name.strip(), "")


if __name__ == "__main__":
    unittest.main()


