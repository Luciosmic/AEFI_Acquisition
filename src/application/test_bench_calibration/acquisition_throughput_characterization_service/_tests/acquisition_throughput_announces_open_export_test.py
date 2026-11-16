"""The throughput characterization announces the export it opens at its start and closes at its end, so
the closing guard can refuse to close the application meanwhile, without calling this service."""

from application.test_bench_calibration.acquisition_throughput_characterization_service._tests import (
    acquisition_throughput_characterization_service_test as base,
)
from infrastructure.persistence.acquisition_throughput.fake.fake_acquisition_throughput_export_port import (
    FakeAcquisitionThroughputExportPort,
)


class TestAcquisitionThroughputAnnouncesOpenExport(base._SweepFixture):
    def setUp(self) -> None:
        super().setUp()
        self.timeline = []
        for topic in ("acquisitionexportopened", "acquisitionexportclosed", "aefivoltagesampleacquired"):
            self.event_bus.subscribe(topic, lambda e, topic=topic: self.timeline.append((topic, e)))

    def test_la_caracterisation_annonce_son_export_ouvert_avant_la_mesure_et_ferme_a_la_fin(self) -> None:
        self._run()

        topics = [topic for topic, _ in self.timeline]
        self.assertEqual(topics[0], "acquisitionexportopened")
        self.assertEqual(topics[-1], "acquisitionexportclosed")
        opened, closed = self.timeline[0][1], self.timeline[-1][1]
        self.assertEqual(opened.acquisition_kind, "acquisition_throughput")
        self.assertEqual((closed.acquisition_kind, closed.acquisition_id), (opened.acquisition_kind, opened.acquisition_id))

    def test_sans_dossier_d_export_la_caracterisation_n_annonce_rien(self) -> None:
        self._run(export_port=FakeAcquisitionThroughputExportPort(fail=True))
        topics = [topic for topic, _ in self.timeline]
        self.assertNotIn("acquisitionexportopened", topics)
        self.assertNotIn("acquisitionexportclosed", topics)
