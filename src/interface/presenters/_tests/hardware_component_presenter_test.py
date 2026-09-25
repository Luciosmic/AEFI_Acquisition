"""Unit tests for HardwareComponentPresenter, against the real service on a Fake repository."""

import unittest

from application.services.hardware_component_service.hardware_component_service import HardwareComponentService
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.persistence.calibration.fake.fake_hardware_component_repository import (
    FakeHardwareComponentRepository,
)
from interface.presenters.hardware_component_presenter import HardwareComponentPresenter


class TestHardwareComponentPresenter(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus()
        self.service = HardwareComponentService(FakeHardwareComponentRepository(), self.event_bus)
        kinds = {k.key: k for k in self.service.list_kinds()}
        self.adc = HardwareComponentPresenter(self.service, kinds["adc"], self.event_bus)
        self.motors = HardwareComponentPresenter(self.service, kinds["motors"], self.event_bus)
        self.adc_listed, self.adc_mounted, self.status, self.motors_listed = [], [], [], []
        self.adc.components_listed.connect(self.adc_listed.append)
        self.adc.mounted_component_updated.connect(self.adc_mounted.append)
        self.adc.status_message.connect(self.status.append)
        self.motors.components_listed.connect(self.motors_listed.append)

    def test_save_then_mount_refreshes_only_its_own_kind(self):
        self.adc.on_save_requested("ADS131A04", {"lsb_v": 2.91109e-7})
        self.adc.on_mount_requested("ADS131A04")

        self.assertEqual([c.component_name for c in self.adc_listed[-1]], ["ADS131A04"])
        self.assertEqual(self.adc_mounted[-1].component_name, "ADS131A04")
        self.assertEqual(self.motors_listed, [])

    def test_errors_are_reported_not_raised(self):
        self.adc.on_mount_requested("Unknown")

        self.assertIn("Erreur", self.status[-1])
        self.assertEqual(self.adc_mounted, [])


if __name__ == "__main__":
    unittest.main()
