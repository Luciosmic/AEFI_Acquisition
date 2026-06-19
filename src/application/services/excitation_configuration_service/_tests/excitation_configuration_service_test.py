import unittest
from unittest.mock import MagicMock
from application.services.excitation_configuration_service.excitation_configuration_service import ExcitationConfigurationService
from application.services.excitation_configuration_service.ports.i_excitation_port import IExcitationPort
from domain.value_objects.excitation.excitation_mode import ExcitationMode
from domain.value_objects.excitation.excitation_parameters import ExcitationParameters
from tool.diagram_friendly_test import DiagramFriendlyTest


class TestExcitationConfigurationService(DiagramFriendlyTest):

    def setUp(self):
        super().setUp()
        self.port = MagicMock(spec=IExcitationPort)
        self.service = ExcitationConfigurationService(excitation_port=self.port)

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


if __name__ == "__main__":
    unittest.main()
