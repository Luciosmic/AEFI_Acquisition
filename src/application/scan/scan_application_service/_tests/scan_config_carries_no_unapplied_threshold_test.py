"""Le scan ne porte plus de seuil d'incertitude : il n'était appliqué nulle part.

Le seuil (0,001 V, codé en dur dans le presenter) traversait le DTO, la config du domaine
et la config d'acquisition continue sans que `is_acceptable` soit jamais appelée.
La dispersion réelle d'un point vit dans les colonnes `std_dev_*` de l'export, calculées
par MeasurementStatisticsService : elle n'est pas touchée (ses tests restent verts).
"""
import importlib.util
import unittest
from dataclasses import fields

from application.scan.scan_application_service.dtos.scan_dtos import Scan2DConfigDTO
from application.shared.aefi_acquisition_service.dtos.aefi_acquisition_dtos import AefiAcquisitionConfig
from domain.step_scan.value_objects.step_scan_config.step_scan_config import StepScanConfig


def _names(cls):
    return {f.name for f in fields(cls)}


class TestScanCarriesNoUnappliedThreshold(unittest.TestCase):
    def test_scan_dto_has_no_uncertainty_threshold(self):
        self.assertNotIn("uncertainty_volts", _names(Scan2DConfigDTO))

    def test_step_scan_config_has_no_uncertainty_threshold(self):
        self.assertNotIn("measurement_uncertainty", _names(StepScanConfig))

    def test_continuous_acquisition_config_has_no_uncertainty_target(self):
        self.assertNotIn("target_uncertainty", _names(AefiAcquisitionConfig))

    def test_measurement_uncertainty_value_object_is_gone(self):
        with self.assertRaises(ModuleNotFoundError):
            importlib.import_module(
                "domain.shared_kernel.value_objects.measurement_uncertainty.measurement_uncertainty"
            )


if __name__ == "__main__":
    unittest.main()
