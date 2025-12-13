import unittest
from typing import List
import sys
from pathlib import Path

# Ensure src is on sys.path when running this file directly
ROOT = Path(__file__).parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from application.hardware_configuration_service.hardware_configuration_service import (
    HardwareConfigurationService,
)
from application.dtos.hardware_parameter_dtos import ActionableHardwareParametersSpec
from infrastructure.hardware.arcus_performax_4EX.adapter_arcus_performax4EX import (
    ArcusPerformax4EXConfigProvider,
)
from infrastructure.tests.diagram_friendly_test import DiagramFriendlyTest


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
            "ArcusPerformax4EXConfigProvider",
            "Instantiate Arcus hardware config provider",
        )
        self.arcus_provider = ArcusPerformax4EXConfigProvider()

        self.log_interaction(
            "Test",
            "CREATE",
            "HardwareConfigurationService",
            "Create service with Arcus provider",
            data={"providers": ["arcus_performax_4ex"]},
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
            expect="arcus_performax_4ex",
            got=hardware_ids[0] if hardware_ids else None,
        )
        self.assertIn("arcus_performax_4ex", hardware_ids)

        # Get display name
        self.log_interaction(
            "Test",
            "CALL",
            "HardwareConfigurationService",
            "get_hardware_display_name('arcus_performax_4ex')",
        )
        display_name = self.service.get_hardware_display_name("arcus_performax_4ex")

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
            "get_parameter_specs('arcus_performax_4ex')",
        )
        specs: List[ActionableHardwareParametersSpec] = self.service.get_parameter_specs(
            "arcus_performax_4ex"
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
            "Verify first spec has name and label",
            expect="non-empty name/label",
            got={"name": first_spec.name, "label": first_spec.label},
        )
        self.assertIsInstance(first_spec.name, str)
        self.assertIsInstance(first_spec.label, str)
        self.assertNotEqual(first_spec.name.strip(), "")
        self.assertNotEqual(first_spec.label.strip(), "")


if __name__ == "__main__":
    unittest.main()


