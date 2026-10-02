"""Unit tests for AcquisitionThroughputCharacterizationPresenter."""

import unittest

from application.services.acquisition_throughput_characterization_service.dtos.acquisition_throughput_dtos import (
    AcquisitionThroughputCharacterizationDTO,
)
from application.services.acquisition_throughput_characterization_service.i_api_acquisition_throughput_characterization_service import (
    IApiAcquisitionThroughputCharacterizationService,
)
from interface.presenters.acquisition_throughput_characterization_presenter import (
    AcquisitionThroughputCharacterizationPresenter,
)


class FakeThroughputService(IApiAcquisitionThroughputCharacterizationService):
    """Hand-written stub: records requests, state-based assertions."""

    def __init__(self):
        self.output_port = None
        self.requests = []

    def set_output_port(self, output_port):
        self.output_port = output_port

    def start_characterization(self, request):
        self.requests.append(request)


RESULT = AcquisitionThroughputCharacterizationDTO(
    points=(), overhead_s=0.01, adc_output_rate_hz=1000.0, fit_max_relative_residual=0.0, recommended_n_avg=32, noise_relative_uncertainty=0.1,
    oversampling_ratio=4096, excitation="coupée", export_path="C:/exports/x",
    component_values={"max_acquisition_rate_per_s": 90.0},
)


class TestAcquisitionThroughputCharacterizationPresenter(unittest.TestCase):
    def setUp(self):
        self.service = FakeThroughputService()
        self.presenter = AcquisitionThroughputCharacterizationPresenter(self.service)
        self.running, self.messages, self.values = [], [], []
        self.presenter.running_changed.connect(self.running.append)
        self.presenter.status_message.connect(self.messages.append)
        self.presenter.component_values_measured.connect(self.values.append)

    def test_registers_itself_as_output_port(self):
        self.assertIs(self.service.output_port, self.presenter)

    def test_start_forwards_the_entered_grid_and_locks(self):
        self.presenter.on_start_requested([20, 40, 60], 200)
        request = self.service.requests[0]
        self.assertEqual((request.n_avg_values, request.samples_per_point), ((20, 40, 60), 200))
        self.assertEqual(self.running, [True])

    def test_refresh_state_offers_the_default_request(self):
        defaults = []
        self.presenter.request_defaults.connect(lambda values, samples: defaults.append((values, samples)))
        self.presenter.refresh_state()
        self.assertEqual(defaults, [((1, 2, 4, 8, 16, 32, 64, 96, 127), 50)])

    def test_success_unlocks_and_forwards_the_component_values(self):
        self.presenter.on_start_requested([1, 8], 50)
        self.presenter.present_throughput_characterization_succeeded(RESULT)
        self.assertEqual(self.running, [True, False])
        self.assertEqual(self.values, [{"max_acquisition_rate_per_s": 90.0}])
        self.assertIn("C:/exports/x", self.messages[-1])

    def test_failure_unlocks_with_an_error_message(self):
        self.presenter.on_start_requested([1, 8], 50)
        self.presenter.present_throughput_characterization_failed("excitation pilotée par : scan")
        self.assertEqual(self.running, [True, False])
        self.assertTrue(self.messages[-1].startswith("Erreur"))
        self.assertIn("scan", self.messages[-1])


if __name__ == "__main__":
    unittest.main()
