import unittest

from domain.calibration.events.source_geometry_calibration_entry_added.source_geometry_calibration_entry_added import (
    SourceGeometryCalibrationEntryAdded,
)
from domain.calibration.entities.source_geometry_calibration_entry.source_geometry_calibration_entry import (
    SourceGeometryCalibrationEntry,
)
from domain.calibration.value_objects.caliper_measurement.caliper_measurement import CaliperMeasurement

_DIAMETERS_M = (0.0196, 0.0196, 0.0195, 0.0195)
_DISTANCES_M = (0.11142, 0.10908, 0.08436, 0.08352, 0.08230, 0.08450)


def make_entry():
    return SourceGeometryCalibrationEntry.single(
        sphere_diameters=tuple(CaliperMeasurement.from_resolution(v) for v in _DIAMETERS_M),
        pairwise_distances_ext=tuple(CaliperMeasurement.from_resolution(v) for v in _DISTANCES_M),
    )


class TestSourceGeometryCalibrationEntryAdded(unittest.TestCase):
    def test_carries_entry(self):
        entry = make_entry()
        event = SourceGeometryCalibrationEntryAdded(entry=entry)
        self.assertEqual(event.entry, entry)

    def test_is_frozen(self):
        entry = make_entry()
        event = SourceGeometryCalibrationEntryAdded(entry=entry)
        with self.assertRaises(Exception):
            event.entry = make_entry()


if __name__ == "__main__":
    unittest.main()
