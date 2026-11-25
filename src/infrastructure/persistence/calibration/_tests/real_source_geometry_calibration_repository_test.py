import json

import pytest

from domain.test_bench_calibration.entities.source_geometry_calibration_entry.source_geometry_calibration_entry import (
    SourceGeometryCalibrationEntry,
)
from domain.test_bench_calibration.value_objects.caliper_measurement.caliper_measurement import CaliperMeasurement
from infrastructure.persistence.calibration.real_source_geometry_calibration_repository import (
    RealSourceGeometryCalibrationRepository,
)

_DIAMETERS_M = (0.0196, 0.0196, 0.0195, 0.0195)
_DISTANCES_M = (0.11142, 0.10908, 0.08436, 0.08352, 0.08230, 0.08450)


def _measurements(values_m):
    return tuple(CaliperMeasurement.from_resolution(v) for v in values_m)


def _make_entry(diameters_m=_DIAMETERS_M) -> SourceGeometryCalibrationEntry:
    return SourceGeometryCalibrationEntry.single(
        sphere_diameters=_measurements(diameters_m),
        pairwise_distances_ext=_measurements(_DISTANCES_M),
    )


def _make_repository(tmp_path) -> RealSourceGeometryCalibrationRepository:
    storage_path = tmp_path / "source_geometry_calibration.json"
    return RealSourceGeometryCalibrationRepository(storage_path=storage_path)


def test_find_all_returns_empty_list_when_none_recorded(tmp_path):
    repository = _make_repository(tmp_path)

    assert repository.find_all() == []


def test_add_then_find_all_round_trips_entry(tmp_path):
    repository = _make_repository(tmp_path)
    entry = _make_entry()

    repository.add(entry)
    found = repository.find_all()

    assert len(found) == 1
    assert found[0].entry_id == entry.entry_id
    assert found[0].sphere_diameters == entry.sphere_diameters
    assert found[0].pairwise_distances_ext == entry.pairwise_distances_ext
    assert found[0].recorded_at == entry.recorded_at


def test_add_appends_multiple_entries_without_dropping_the_first(tmp_path):
    repository = _make_repository(tmp_path)
    first_entry = _make_entry(diameters_m=(0.0196, 0.0196, 0.0195, 0.0195))
    second_entry = _make_entry(diameters_m=(0.0200, 0.0200, 0.0199, 0.0199))

    repository.add(first_entry)
    repository.add(second_entry)

    found = repository.find_all()

    assert [e.entry_id for e in found] == [first_entry.entry_id, second_entry.entry_id]


def test_storage_file_shape_matches_documented_contract(tmp_path):
    repository = _make_repository(tmp_path)
    entry = _make_entry()

    repository.add(entry)

    storage_path = tmp_path / "source_geometry_calibration.json"
    with storage_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    assert len(raw["entries"]) == 1
    stored_entry = raw["entries"][0]
    assert stored_entry["entry_id"] == str(entry.entry_id)
    assert len(stored_entry["sphere_diameters"]) == 4
    assert len(stored_entry["pairwise_distances_ext"]) == 6
    assert stored_entry["sphere_diameters"][0] == {
        "value_m": entry.sphere_diameters[0].value_m,
        "uncertainty_expanded_m": entry.sphere_diameters[0].uncertainty_expanded_m,
        "k": entry.sphere_diameters[0].k,
        "uniform_half_width_m": entry.sphere_diameters[0].uniform_half_width_m,
    }
    assert stored_entry["recorded_at"] == entry.recorded_at.isoformat()


def test_half_widths_round_trip_with_their_standard_uncertainty(tmp_path):
    """±0.25 mm on the distances, ±0.01 mm on the diameters, uniform law."""
    repository = _make_repository(tmp_path)
    entry = SourceGeometryCalibrationEntry.single(
        sphere_diameters=tuple(
            CaliperMeasurement.from_uniform_half_width(v, half_width_m=0.00001) for v in _DIAMETERS_M
        ),
        pairwise_distances_ext=tuple(
            CaliperMeasurement.from_uniform_half_width(v, half_width_m=0.00025) for v in _DISTANCES_M
        ),
    )

    repository.add(entry)
    (found,) = repository.find_all()

    assert found.pairwise_distances_ext == entry.pairwise_distances_ext
    assert found.sphere_diameters == entry.sphere_diameters
    for m in found.pairwise_distances_ext:
        assert m.uniform_half_width_m == 0.00025
        assert m.uncertainty_expanded_m / m.k == pytest.approx(0.00025 / 3 ** 0.5, rel=1e-12)
    for m in found.sphere_diameters:
        assert m.uniform_half_width_m == 0.00001
        assert m.uncertainty_expanded_m / m.k == pytest.approx(0.00001 / 3 ** 0.5, rel=1e-12)


def test_legacy_file_without_half_widths_reads_back_unchanged_at_0_01_mm(tmp_path):
    """A registry written before the half-widths existed: same values, same
    uncertainty, read as the default 0.01 mm half-width — no error."""
    legacy_u = 2.0 * 0.00002 / (2 * 3 ** 0.5)
    legacy = lambda v: {"value_m": v, "uncertainty_expanded_m": legacy_u, "k": 2.0}
    storage_path = tmp_path / "source_geometry_calibration.json"
    storage_path.write_text(json.dumps({"entries": [{
        "entry_id": "6f1c1d2e-0000-4000-8000-000000000001",
        "sphere_diameters": [legacy(v) for v in _DIAMETERS_M],
        "pairwise_distances_ext": [legacy(v) for v in _DISTANCES_M],
        "recorded_at": "2026-11-20T10:00:00+00:00",
    }]}), encoding="utf-8")

    (found,) = RealSourceGeometryCalibrationRepository(storage_path=storage_path).find_all()

    for m, v in zip((*found.sphere_diameters, *found.pairwise_distances_ext), (*_DIAMETERS_M, *_DISTANCES_M)):
        assert m.value_m == v
        assert m.uncertainty_expanded_m == legacy_u
        assert m.k == 2.0
        assert m.uniform_half_width_m == pytest.approx(0.00001, rel=1e-12)


def test_add_handles_missing_parent_directory(tmp_path):
    storage_path = tmp_path / "nested" / "does" / "not" / "exist.json"
    repository = RealSourceGeometryCalibrationRepository(storage_path=storage_path)
    entry = _make_entry()

    repository.add(entry)

    assert storage_path.exists()
    assert len(repository.find_all()) == 1


def test_find_all_recovers_from_corrupt_file(tmp_path):
    storage_path = tmp_path / "source_geometry_calibration.json"
    storage_path.write_text("not valid json", encoding="utf-8")
    repository = RealSourceGeometryCalibrationRepository(storage_path=storage_path)

    assert repository.find_all() == []
