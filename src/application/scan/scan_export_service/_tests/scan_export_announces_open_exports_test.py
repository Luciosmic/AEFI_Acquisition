"""The scan export announces each export it opens and closes, so the closing guard can refuse to close
the application meanwhile, without calling this service."""

import unittest

from application.scan.scan_export_service._tests import scan_export_service_test as base
from application.scan.scan_export_service.dtos.scan_export_dtos import ExportConfigDTO
from domain.step_scan.events.scan_cancelled.scan_cancelled import ScanCancelled
from domain.step_scan.events.scan_completed.scan_completed import ScanCompleted
from domain.step_scan.events.scan_failed.scan_failed import ScanFailed


class TestScanExportAnnouncesOpenExports(unittest.TestCase):
    def setUp(self) -> None:
        base.TestScanExportServiceMetadata.setUp(self)
        self.announced = []
        self.event_bus.subscribe("acquisitionexportopened", lambda e: self.announced.append(("opened", e)))
        self.event_bus.subscribe("acquisitionexportclosed", lambda e: self.announced.append(("closed", e)))

    def _summary(self):
        return [(what, e.acquisition_kind, e.acquisition_id) for what, e in self.announced]

    def test_un_scan_avec_export_annonce_l_ouverture_puis_la_fermeture(self) -> None:
        self.service.configure_export(ExportConfigDTO(enabled=True, output_directory="", measured_object="plaque"))
        started = base._make_scan_started_event()
        self.event_bus.publish("scanstarted", started)
        self.assertEqual(self._summary(), [("opened", "step_scan", str(started.scan_id))])
        self.assertEqual(self.announced[0][1].measured_object, "plaque")

        self.event_bus.publish("scancompleted", ScanCompleted(scan_id=started.scan_id, total_points=1))
        self.assertEqual(self._summary()[-1], ("closed", "step_scan", str(started.scan_id)))

    def test_un_fly_scan_s_annonce_comme_fly_scan(self) -> None:
        started = base._make_scan_started_event(fly_scan=True)
        self.event_bus.publish("scanstarted", started)
        self.assertEqual(self._summary(), [("opened", "fly_scan", str(started.scan_id))])

    def test_un_scan_arrete_ou_en_echec_annonce_aussi_la_fermeture(self) -> None:
        for end in (lambda s: ScanCancelled(scan_id=s), lambda s: ScanFailed(scan_id=s, reason="motion error")):
            started = base._make_scan_started_event()
            self.event_bus.publish("scanstarted", started)
            event = end(started.scan_id)
            self.event_bus.publish(type(event).__name__.lower(), event)
            self.assertEqual(self._summary()[-1], ("closed", "step_scan", str(started.scan_id)))

    def test_un_scan_sans_export_n_annonce_rien(self) -> None:
        self.service.configure_export(ExportConfigDTO(enabled=False, output_directory=""))
        self.event_bus.publish("scanstarted", base._make_scan_started_event())
        self.assertEqual(self.announced, [])

    def test_une_lecture_continue_avec_export_arme_annonce_l_ouverture_puis_la_fermeture(self) -> None:
        self.service.configure_time_series_export(ExportConfigDTO(enabled=True, output_directory=""))
        acquisition_id = base._publish_reading(self.event_bus, n_samples=2)
        self.assertEqual(self._summary(), [
            ("opened", "time_series", str(acquisition_id)),
            ("closed", "time_series", str(acquisition_id)),
        ])

    def test_une_lecture_continue_sans_export_n_annonce_rien(self) -> None:
        base._publish_reading(self.event_bus, n_samples=2)
        self.assertEqual(self.announced, [])
