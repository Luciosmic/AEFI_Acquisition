"""Single owner of the continuous acquisition stream: while a controller
holds it, nobody else may start or stop it."""

import unittest

from application.services.aefi_acquisition_service.aefi_acquisition_service import (
    AEFI_ACQUISITION_CONTROL_CHANGED_TOPIC,
    AefiAcquisitionService,
)
from application.services.aefi_acquisition_service.dtos.aefi_acquisition_dtos import AefiAcquisitionConfig
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.mocks.adapter_mock_i_acquisition_port import RandomNoiseAcquisitionPort
from infrastructure.mocks.adapter_mock_i_aefi_acquisition_executor import MockAefiAcquisitionExecutor


class TestAefiAcquisitionControl(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus()
        self.service = AefiAcquisitionService(
            MockAefiAcquisitionExecutor(self.event_bus), RandomNoiseAcquisitionPort(noise_std=0.0, seed=1), self.event_bus
        )
        self.controllers = []
        self.event_bus.subscribe(AEFI_ACQUISITION_CONTROL_CHANGED_TOPIC, lambda e: self.controllers.append(e.controller))

    def tearDown(self):
        self.service.release_control("caractérisation")
        self.service.stop_acquisition()

    def test_free_stream_starts_and_stops_by_hand(self):
        self.assertTrue(self.service.start_acquisition(AefiAcquisitionConfig()).is_success)
        self.assertTrue(self.service.is_acquisition_running())
        self.assertTrue(self.service.stop_acquisition().is_success)

    def test_stop_by_hand_is_refused_while_controlled(self):
        self.service.start_acquisition(AefiAcquisitionConfig())
        self.service.take_control("caractérisation")

        result = self.service.stop_acquisition()

        self.assertTrue(result.is_failure)
        self.assertIn("caractérisation", result.error)
        self.assertTrue(self.service.is_acquisition_running())

    def test_start_by_hand_is_refused_while_controlled(self):
        self.service.take_control("caractérisation")
        self.assertTrue(self.service.start_acquisition(AefiAcquisitionConfig()).is_failure)
        self.assertFalse(self.service.is_acquisition_running())

    def test_owner_starts_and_stops(self):
        self.service.take_control("caractérisation")
        self.assertTrue(self.service.start_acquisition(AefiAcquisitionConfig(), controller="caractérisation").is_success)
        self.assertTrue(self.service.stop_acquisition(controller="caractérisation").is_success)

    def test_owner_changes_are_published(self):
        self.service.take_control("caractérisation")
        self.service.release_control("caractérisation")
        self.assertEqual(self.controllers, ["caractérisation", None])
        self.assertIsNone(self.service.get_controller())


if __name__ == "__main__":
    unittest.main()
