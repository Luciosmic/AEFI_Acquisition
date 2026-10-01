import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from domain.calibration.entities.synchronous_detection_phase_calibration_entry.synchronous_detection_phase_calibration_entry import (
    SynchronousDetectionPhaseCalibrationEntry,
)
from domain.calibration.value_objects.hardware_signature.hardware_signature import HardwareSignature
from domain.calibration.value_objects.synchronous_detection_phase_calibration_point.synchronous_detection_phase_calibration_point import (
    SynchronousDetectionPhaseCalibrationPoint,
)
from infrastructure.persistence.calibration.real_synchronous_detection_phase_calibration_repository import (
    RealSynchronousDetectionPhaseCalibrationRepository,
)


def _make_signature(serial: str = "SN-1") -> HardwareSignature:
    return HardwareSignature(
        excitation_electronics_board_name="board_v2",
        conditioning_electronics_board_name="cond_v4",
        sensor_name=f"v2b_{serial}",
    )


def _make_entry(signature: HardwareSignature, frequency_hz: float = 1000.0) -> SynchronousDetectionPhaseCalibrationEntry:
    return SynchronousDetectionPhaseCalibrationEntry.single(
        hardware_signature=signature,
        point=SynchronousDetectionPhaseCalibrationPoint(frequency_hz=frequency_hz, delta_phi_degrees=12.5),
    )


def _make_repository(tmp_path) -> RealSynchronousDetectionPhaseCalibrationRepository:
    storage_path = tmp_path / "synchronous_detection_phase_calibration.json"
    return RealSynchronousDetectionPhaseCalibrationRepository(storage_path=storage_path)


def test_load_compensation_enabled_defaults_to_false_when_file_missing(tmp_path):
    repository = _make_repository(tmp_path)

    assert repository.load_compensation_enabled() is False


def test_save_and_load_compensation_enabled_round_trip(tmp_path):
    repository = _make_repository(tmp_path)

    repository.save_compensation_enabled(True)

    assert repository.load_compensation_enabled() is True


def test_find_by_hardware_signature_returns_empty_list_when_none_recorded(tmp_path):
    repository = _make_repository(tmp_path)

    assert repository.find_by_hardware_signature(_make_signature()) == []


def test_add_then_find_by_hardware_signature_round_trips_entry(tmp_path):
    repository = _make_repository(tmp_path)
    signature = _make_signature()
    entry = _make_entry(signature)

    repository.add(entry)
    found = repository.find_by_hardware_signature(signature)

    assert len(found) == 1
    assert found[0].entry_id == entry.entry_id
    assert found[0].hardware_signature == signature
    assert found[0].points == entry.points
    assert found[0].recorded_at == entry.recorded_at


def test_add_is_append_only_across_different_signatures(tmp_path):
    """
    The registry is constructive: adding a second entry (recorded on a
    DIFFERENT hardware signature) must never drop or alter the first.
    """
    repository = _make_repository(tmp_path)
    first_signature = _make_signature(serial="SN-FIRST")
    second_signature = _make_signature(serial="SN-SECOND")
    first_entry = _make_entry(first_signature, frequency_hz=1000.0)
    second_entry = _make_entry(second_signature, frequency_hz=2000.0)

    repository.add(first_entry)
    repository.add(second_entry)

    found_first = repository.find_by_hardware_signature(first_signature)
    found_second = repository.find_by_hardware_signature(second_signature)

    assert len(found_first) == 1
    assert found_first[0].entry_id == first_entry.entry_id
    assert len(found_second) == 1
    assert found_second[0].entry_id == second_entry.entry_id


def test_add_appends_multiple_entries_for_same_signature(tmp_path):
    repository = _make_repository(tmp_path)
    signature = _make_signature()
    first_entry = _make_entry(signature, frequency_hz=1000.0)
    second_entry = _make_entry(signature, frequency_hz=1500.0)

    repository.add(first_entry)
    repository.add(second_entry)

    found = repository.find_by_hardware_signature(signature)

    assert [e.entry_id for e in found] == [first_entry.entry_id, second_entry.entry_id]


def test_save_compensation_enabled_never_touches_entries(tmp_path):
    repository = _make_repository(tmp_path)
    signature = _make_signature()
    entry = _make_entry(signature)
    repository.add(entry)

    repository.save_compensation_enabled(True)

    found = repository.find_by_hardware_signature(signature)
    assert len(found) == 1
    assert found[0].entry_id == entry.entry_id


def test_storage_file_shape_matches_documented_contract(tmp_path):
    repository = _make_repository(tmp_path)
    signature = _make_signature()
    entry = _make_entry(signature)

    repository.add(entry)
    repository.save_compensation_enabled(True)

    storage_path = tmp_path / "synchronous_detection_phase_calibration.json"
    with storage_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    assert raw["compensation_enabled"] is True
    assert len(raw["entries"]) == 1
    stored_entry = raw["entries"][0]
    assert stored_entry["entry_id"] == str(entry.entry_id)
    assert stored_entry["hardware_signature"] == {
        "excitation_electronics_board_name": "board_v2",
        "conditioning_electronics_board_name": "cond_v4",
        "sensor_name": "v2b_SN-1",
    }
    assert stored_entry["points"] == [{"frequency_hz": 1000.0, "delta_phi_degrees": 12.5}]
    assert stored_entry["recorded_at"] == entry.recorded_at.isoformat()


def test_add_handles_missing_parent_directory(tmp_path):
    storage_path = tmp_path / "nested" / "does" / "not" / "exist.json"
    repository = RealSynchronousDetectionPhaseCalibrationRepository(storage_path=storage_path)
    signature = _make_signature()
    entry = _make_entry(signature)

    repository.add(entry)

    assert storage_path.exists()
    assert len(repository.find_by_hardware_signature(signature)) == 1


def test_load_compensation_enabled_recovers_from_corrupt_file(tmp_path):
    storage_path = tmp_path / "synchronous_detection_phase_calibration.json"
    storage_path.write_text("not valid json", encoding="utf-8")
    repository = RealSynchronousDetectionPhaseCalibrationRepository(storage_path=storage_path)

    assert repository.load_compensation_enabled() is False
    assert repository.find_by_hardware_signature(_make_signature()) == []
