"""The frequency sweep announces the export it opens at its start and closes at its end, so the closing
guard can refuse to close the application meanwhile, without calling this service."""

import unittest

from application.frequency_sweep.frequency_sweep_service._tests import frequency_sweep_service_test as base
from infrastructure.persistence.frequency_sweep.fake.fake_frequency_sweep_export_port import FakeFrequencySweepExportPort


class TestFrequencySweepAnnouncesOpenExport(unittest.TestCase):
    def setUp(self) -> None:
        base.TestFrequencySweepService.setUp(self)
        self.timeline = []
        for topic in ("acquisitionexportopened", "acquisitionexportclosed", "frequencypointacquired"):
            self.event_bus.subscribe(topic, lambda e, topic=topic: self.timeline.append((topic, e)))

    _service = base.TestFrequencySweepService._service

    def test_le_balayage_annonce_son_export_ouvert_avant_la_mesure_et_ferme_a_la_fin(self) -> None:
        self._service().start_sweep(base.REQUEST)

        topics = [topic for topic, _ in self.timeline]
        self.assertEqual(topics[0], "acquisitionexportopened")
        self.assertEqual(topics[-1], "acquisitionexportclosed")
        opened, closed = self.timeline[0][1], self.timeline[-1][1]
        (result,) = self.output.ended
        self.assertEqual((opened.acquisition_kind, opened.acquisition_id), ("frequency_sweep", result.sweep_id))
        self.assertEqual((closed.acquisition_kind, closed.acquisition_id), ("frequency_sweep", result.sweep_id))

    def test_un_balayage_arrete_annonce_aussi_la_fermeture(self) -> None:
        service = self._service()
        self.output = base.RecordingOutputPort(on_point=lambda p: service.stop_sweep())
        service.set_output_port(self.output)
        service.start_sweep(base.REQUEST)
        self.assertEqual(self.timeline[-1][0], "acquisitionexportclosed")

    def test_sans_dossier_d_export_le_balayage_n_annonce_rien(self) -> None:
        self.export = FakeFrequencySweepExportPort(fail=True)
        self._service().start_sweep(base.REQUEST)
        self.assertNotIn("acquisitionexportopened", [topic for topic, _ in self.timeline])
        self.assertNotIn("acquisitionexportclosed", [topic for topic, _ in self.timeline])
