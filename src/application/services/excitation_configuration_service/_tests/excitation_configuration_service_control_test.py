"""Single owner of the excitation: while a controller (scan, automatic
calibration) holds it, nobody else may change it."""

import unittest

from application.services.excitation_configuration_service.excitation_configuration_service import (
    EXCITATION_CONTROL_CHANGED_TOPIC,
    ExcitationConfigurationService,
)
from domain.shared_kernel.excitation.value_objects.excitation_mode import ExcitationMode
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.mocks.adapter_mock_i_excitation_port import MockExcitationPort


class TestExcitationControl(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus()
        self.port = MockExcitationPort()
        self.service = ExcitationConfigurationService(self.port, self.event_bus)
        self.control_events = []
        self.event_bus.subscribe(EXCITATION_CONTROL_CHANGED_TOPIC, self.control_events.append)

    def _set(self, controller=None, level=40.0):
        return self.service.set_excitation(ExcitationMode.X_DIR, level, level, 1000.0, controller=controller)

    def test_free_excitation_is_settable_by_hand(self):
        self.assertTrue(self._set().is_success)
        self.assertIsNone(self.service.get_controller())

    def test_controller_holds_the_excitation_and_publishes_it(self):
        self.assertTrue(self.service.take_control("scan").is_success)
        self.assertEqual(self.service.get_controller(), "scan")
        self.assertEqual([e.controller for e in self.control_events], ["scan"])

    def test_hand_changes_are_refused_while_controlled(self):
        self._set(level=40.0)
        self.service.take_control("scan")

        result = self._set(level=90.0)

        self.assertTrue(result.is_failure)
        self.assertIn("scan", result.error)
        self.assertEqual(self.port.last_parameters.level_s1_s2.value, 40.0)

    def test_link_toggle_is_refused_while_controlled(self):
        self.service.take_control("scan")
        self.assertTrue(self.service.set_link(False).is_failure)

    def test_owner_may_change_the_excitation(self):
        self.service.take_control("calibration")
        self.assertTrue(self._set(controller="calibration", level=70.0).is_success)
        self.assertEqual(self.port.last_parameters.level_s1_s2.value, 70.0)

    def test_second_controller_is_refused(self):
        self.service.take_control("scan")

        result = self.service.take_control("calibration")

        self.assertTrue(result.is_failure)
        self.assertIn("scan", result.error)
        self.assertEqual(self.service.get_controller(), "scan")

    def test_taking_control_twice_is_idempotent(self):
        self.service.take_control("scan")
        self.assertTrue(self.service.take_control("scan").is_success)
        self.assertEqual(len(self.control_events), 1)

    def test_release_frees_the_excitation(self):
        self.service.take_control("scan")
        self.service.release_control("scan")

        self.assertIsNone(self.service.get_controller())
        self.assertEqual([e.controller for e in self.control_events], ["scan", None])
        self.assertTrue(self._set().is_success)

    def test_release_by_a_non_owner_is_ignored(self):
        self.service.take_control("scan")
        self.service.release_control("calibration")
        self.assertEqual(self.service.get_controller(), "scan")

    def test_release_is_idempotent(self):
        self.service.take_control("scan")
        self.service.release_control("scan")
        self.service.release_control("scan")
        self.assertEqual(len(self.control_events), 2)


if __name__ == "__main__":
    unittest.main()
