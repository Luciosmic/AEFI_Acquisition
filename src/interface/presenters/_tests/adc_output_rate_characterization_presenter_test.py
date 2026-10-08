"""Unit tests for AdcOutputRateCharacterizationPresenter."""

import unittest

from application.services.adc_output_rate_characterization_service.dtos.adc_output_rate_dtos import (
    AdcOutputRateCharacterizationDTO,
)
from application.services.adc_output_rate_characterization_service.i_api_adc_output_rate_characterization_service import (
    IApiAdcOutputRateCharacterizationService,
)
from interface.presenters.adc_output_rate_characterization_presenter import AdcOutputRateCharacterizationPresenter


class FakeOdrService(IApiAdcOutputRateCharacterizationService):
    def __init__(self):
        self.output_port, self.requests = None, []

    def set_output_port(self, output_port):
        self.output_port = output_port

    def start_characterization(self, request):
        self.requests.append(request)

    def get_allowed_oversampling_ratios(self):
        return (4096, 32)


RESULT = AdcOutputRateCharacterizationDTO(
    points=(), mean_modulator_frequency_hz=4.096e6, max_modulator_frequency_relative_deviation=0.0,
    restored_oversampling_ratio=4096, instrument="DSO-X", export_path="C:/exports/odr",
    component_values={"modulator_frequency_hz": 4.096e6},
)


class TestAdcOutputRateCharacterizationPresenter(unittest.TestCase):
    def setUp(self):
        self.service = FakeOdrService()
        self.presenter = AdcOutputRateCharacterizationPresenter(self.service)
        self.running, self.messages, self.values, self.defaults = [], [], [], []
        self.presenter.running_changed.connect(self.running.append)
        self.presenter.status_message.connect(self.messages.append)
        self.presenter.component_values_measured.connect(self.values.append)
        self.presenter.request_defaults.connect(self.defaults.append)

    def test_registers_itself_and_offers_the_accepted_osr(self):
        self.assertIs(self.service.output_port, self.presenter)
        self.presenter.refresh_state()
        self.assertEqual(self.defaults, [(4096, 32)])

    def test_start_forwards_the_request_and_locks(self):
        self.presenter.on_start_requested((2048, 32), 1, 10.0, 50)
        request = self.service.requests[0]
        self.assertEqual((request.oversampling_ratios, request.scope_channel, request.probe_ratio), ((2048, 32), 1, 10.0))
        self.assertEqual(self.running, [True])

    def test_success_unlocks_and_forwards_the_component_values(self):
        self.presenter.on_start_requested((), 1, 10.0, 50)
        self.presenter.present_output_rate_characterization_succeeded(RESULT)
        self.assertEqual(self.running, [True, False])
        self.assertEqual(self.values, [{"modulator_frequency_hz": 4.096e6}])
        self.assertIn("C:/exports/odr", self.messages[-1])

    def test_failure_unlocks_with_an_error_message(self):
        self.presenter.on_start_requested((), 1, 10.0, 50)
        self.presenter.present_output_rate_characterization_failed("aucun oscilloscope VISA détecté")
        self.assertEqual(self.running, [True, False])
        self.assertTrue(self.messages[-1].startswith("Erreur"))


if __name__ == "__main__":
    unittest.main()
