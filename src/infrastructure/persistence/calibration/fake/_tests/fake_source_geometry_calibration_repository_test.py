from domain.calibration.entities.source_geometry_calibration_entry.source_geometry_calibration_entry import (
    SourceGeometryCalibrationEntry,
)
from domain.calibration.value_objects.caliper_measurement.caliper_measurement import CaliperMeasurement
from infrastructure.persistence.calibration.fake.fake_source_geometry_calibration_repository import (
    FakeSourceGeometryCalibrationRepository,
)

_DIAMETERS_M = (0.0196, 0.0196, 0.0195, 0.0195)
_DISTANCES_M = (0.11142, 0.10908, 0.08436, 0.08352, 0.08230, 0.08450)


def _make_entry() -> SourceGeometryCalibrationEntry:
    return SourceGeometryCalibrationEntry.single(
        sphere_diameters=tuple(CaliperMeasurement.from_resolution(v) for v in _DIAMETERS_M),
        pairwise_distances_ext=tuple(CaliperMeasurement.from_resolution(v) for v in _DISTANCES_M),
    )


def test_find_all_returns_empty_list_when_none_recorded():
    repository = FakeSourceGeometryCalibrationRepository()

    assert repository.find_all() == []


def test_add_then_find_all_round_trips_entry():
    repository = FakeSourceGeometryCalibrationRepository()
    entry = _make_entry()

    repository.add(entry)

    assert repository.find_all() == [entry]


def test_add_appends_multiple_entries():
    repository = FakeSourceGeometryCalibrationRepository()
    first_entry = _make_entry()
    second_entry = _make_entry()

    repository.add(first_entry)
    repository.add(second_entry)

    assert repository.find_all() == [first_entry, second_entry]


def test_find_all_returns_a_copy_not_internal_state():
    repository = FakeSourceGeometryCalibrationRepository()
    repository.add(_make_entry())

    found = repository.find_all()
    found.clear()

    assert len(repository.find_all()) == 1
