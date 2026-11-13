"""Unit tests for FrequencySweepPresenter."""

import unittest

from application.frequency_sweep.frequency_sweep_service.dtos.frequency_sweep_dtos import (
    FrequencyPointDTO,
    FrequencySweepResultDTO,
)
from application.frequency_sweep.frequency_sweep_service.i_api_frequency_sweep_service import IApiFrequencySweepService
from interface.presenters.frequency_sweep_presenter import FrequencySweepPresenter


class FakeFrequencySweepService(IApiFrequencySweepService):
    """Hand-written stub: records requests, state-based assertions."""

    def __init__(self):
        self.output_port = None
        self.requests = []
        self.stops = 0

    def set_output_port(self, output_port):
        self.output_port = output_port

    def start_sweep(self, request):
        self.requests.append(request)

    def stop_sweep(self):
        self.stops += 1


class TestFrequencySweepPresenter(unittest.TestCase):
    def setUp(self):
        self.service = FakeFrequencySweepService()
        self.presenter = FrequencySweepPresenter(self.service)
        self.messages, self.running, self.points = [], [], []
        self.presenter.status_message.connect(self.messages.append)
        self.presenter.running_changed.connect(self.running.append)
        self.presenter.point_measured.connect(self.points.append)

    def test_registers_itself_as_output_port(self):
        self.assertIs(self.service.output_port, self.presenter)

    def test_start_forwards_the_panel_fields_as_a_request(self):
        self.presenter.on_start_requested({
            "role": "background", "start_hz": 10.0, "stop_hz": 1000.0, "points_per_decade": 5, "frequency_list_hz": None,
            "samples_per_frequency": 20, "table_height_mm": 42.5, "operator_name": "Luis", "operator_id": "op-1",
        })
        (request,) = self.service.requests
        self.assertEqual((request.role, request.table_height_mm, request.points_per_decade), ("background", 42.5, 5))
        self.assertEqual(self.running, [True])

    def test_a_point_is_shown_as_amplitude_and_phase_per_axis(self):
        self.presenter.present_frequency_point_measured(
            FrequencyPointDTO(0, 100.0, 3, (3.0, 0.0, 0.0, 4.0, 1.0, 0.0), (0.0,) * 6, None)
        )
        (view,) = self.points
        self.assertEqual(view.frequency_hz, 100.0)
        self.assertAlmostEqual(view.amplitude_v[0], 5.0)
        self.assertAlmostEqual(view.phase_deg[1], 90.0)

    def test_end_and_failure_release_the_panel(self):
        self.presenter.present_frequency_sweep_ended(FrequencySweepResultDTO(
            sweep_id="s", role="background", table_height_mm=1.0, status="cancelled", points=(), export_path="C:/x",
        ))
        self.presenter.present_frequency_sweep_failed("hauteur de la table non saisie")
        self.assertEqual(self.running, [False, False])
        self.assertIn("arrêté avant la fin", self.messages[0])
        self.assertTrue(self.messages[1].startswith("Erreur"))

    def test_stop_is_forwarded(self):
        self.presenter.on_stop_requested()
        self.assertEqual(self.service.stops, 1)


if __name__ == "__main__":
    unittest.main()
