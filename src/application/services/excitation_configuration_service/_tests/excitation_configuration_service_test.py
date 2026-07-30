import unittest
from unittest.mock import MagicMock
from application.services.excitation_configuration_service.excitation_configuration_service import ExcitationConfigurationService
from application.services.excitation_configuration_service.ports.i_excitation_port import IExcitationPort
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.events.excitation_frequency_changed.excitation_frequency_changed import (
    ExcitationFrequencyChanged,
)
from domain.shared_kernel.value_objects.excitation.excitation_mode import ExcitationMode
from domain.shared_kernel.value_objects.excitation.excitation_parameters import ExcitationParameters
from tool.diagram_friendly_test import DiagramFriendlyTest


class TestExcitationConfigurationService(DiagramFriendlyTest):

    def setUp(self):
        super().setUp()
        self.port = MagicMock(spec=IExcitationPort)
        self.event_bus = MagicMock(spec=IDomainEventBus)
        self.service = ExcitationConfigurationService(
            excitation_port=self.port, event_bus=self.event_bus
        )

    def test_initial_state_is_off(self):
        params = self.service.get_current_parameters()
        self.assertEqual(params, ExcitationParameters.off())

    def test_set_excitation_calls_port(self):
        self.service.set_excitation(ExcitationMode.X_DIR, 50.0, 1000.0)
        self.port.apply_excitation.assert_called_once()

    def test_current_parameters_updated_after_set(self):
        self.service.set_excitation(ExcitationMode.X_DIR, 50.0, 1000.0)
        params = self.service.get_current_parameters()
        self.assertAlmostEqual(params.frequency, 1000.0)

    def test_set_excitation_publishes_event_when_frequency_changes(self):
        self.service.set_excitation(ExcitationMode.X_DIR, 50.0, 1000.0)

        self.event_bus.publish.assert_called_once()
        topic, event = self.event_bus.publish.call_args[0]
        self.assertEqual(topic, "excitationfrequencychanged")
        self.assertIsInstance(event, ExcitationFrequencyChanged)
        self.assertAlmostEqual(event.frequency_hz, 1000.0)

    def test_set_excitation_does_not_publish_when_only_mode_or_level_changes(self):
        self.service.set_excitation(ExcitationMode.X_DIR, 50.0, 1000.0)
        self.event_bus.reset_mock()

        self.service.set_excitation(ExcitationMode.Y_DIR, 75.0, 1000.0)

        self.event_bus.publish.assert_not_called()


if __name__ == "__main__":
    unittest.main()
