import unittest
from datetime import datetime
from uuid import UUID

from domain.calibration.entities.source_geometry_calibration_entry.source_geometry_calibration_entry import (
    SourceGeometryCalibrationEntry,
)
from domain.calibration.value_objects.caliper_measurement.caliper_measurement import CaliperMeasurement
from domain.calibration.value_objects.geometric_configuration_signature.geometric_configuration_signature import (
    GeometricConfigurationSignature,
)

_REAL_DIAMETERS_M = (0.0196, 0.0196, 0.0195, 0.0195)
_REAL_DISTANCES_M = (0.11142, 0.10908, 0.08436, 0.08352, 0.08230, 0.08450)


def _measurements(values_m):
    return tuple(CaliperMeasurement.from_resolution(v) for v in values_m)


def _make_entry(diameters_m=_REAL_DIAMETERS_M, distances_m=_REAL_DISTANCES_M) -> SourceGeometryCalibrationEntry:
    return SourceGeometryCalibrationEntry.single(
        sphere_diameters=_measurements(diameters_m),
        pairwise_distances_ext=_measurements(distances_m),
    )


class TestSourceGeometryCalibrationEntry(unittest.TestCase):
    def test_single_mints_entry_with_uuid_and_timestamp(self):
        entry = _make_entry()

        self.assertIsInstance(entry.entry_id, UUID)
        self.assertIsInstance(entry.recorded_at, datetime)
        self.assertEqual(len(entry.sphere_diameters), 4)
        self.assertEqual(len(entry.pairwise_distances_ext), 6)

    def test_accepts_real_device_config_values(self):
        """Sanity check against config_templates/aefi_device_config.json's
        current real measurements — must not be rejected as overlapping."""
        entry = _make_entry()
        self.assertAlmostEqual(entry.sphere_diameters[0].value_m, 0.0196)

    def test_is_immutable(self):
        entry = _make_entry()
        with self.assertRaises(Exception):
            entry.sphere_diameters = None

    def test_successive_entries_get_distinct_ids(self):
        entry_a = _make_entry()
        entry_b = _make_entry()
        self.assertNotEqual(entry_a.entry_id, entry_b.entry_id)

    def test_rejects_wrong_diameter_count(self):
        with self.assertRaises(ValueError):
            SourceGeometryCalibrationEntry.single(
                sphere_diameters=_measurements(_REAL_DIAMETERS_M[:3]),
                pairwise_distances_ext=_measurements(_REAL_DISTANCES_M),
            )

    def test_rejects_wrong_distance_count(self):
        with self.assertRaises(ValueError):
            SourceGeometryCalibrationEntry.single(
                sphere_diameters=_measurements(_REAL_DIAMETERS_M),
                pairwise_distances_ext=_measurements(_REAL_DISTANCES_M[:5]),
            )

    def test_rejects_overlapping_spheres(self):
        """D_S1_S2 smaller than r1+r2 — physically impossible, must be a
        measurement error (e.g. digits swapped on the caliper reading)."""
        bad_distances = (0.005,) + _REAL_DISTANCES_M[1:]  # D_S1_S2 way too small
        with self.assertRaises(ValueError):
            SourceGeometryCalibrationEntry.single(
                sphere_diameters=_measurements(_REAL_DIAMETERS_M),
                pairwise_distances_ext=_measurements(bad_distances),
            )

    # -- geometric_configuration ------------------------------------------------

    def test_geometric_configuration_extracts_raw_values_in_order(self):
        entry = _make_entry()

        signature = entry.geometric_configuration

        self.assertEqual(
            signature,
            GeometricConfigurationSignature(
                sphere_diameters_m=_REAL_DIAMETERS_M, pairwise_distances_ext_m=_REAL_DISTANCES_M
            ),
        )

    def test_geometric_configuration_drops_uncertainty(self):
        entry = _make_entry()

        signature = entry.geometric_configuration

        self.assertFalse(hasattr(signature, "uncertainty_expanded_m"))


if __name__ == "__main__":
    unittest.main()
