from domain.calibration.entities.synchronous_detection_phase_calibration_entry.synchronous_detection_phase_calibration_entry import (
    SynchronousDetectionPhaseCalibrationEntry,
)
from domain.calibration.value_objects.hardware_signature.hardware_signature import HardwareSignature
from domain.calibration.value_objects.synchronous_detection_phase_calibration_point.synchronous_detection_phase_calibration_point import (
    SynchronousDetectionPhaseCalibrationPoint,
)
from infrastructure.persistence.calibration.fake.fake_synchronous_detection_phase_calibration_repository import (
    FakeSynchronousDetectionPhaseCalibrationRepository,
)


def _make_signature(serial: str = "SN-1") -> HardwareSignature:
    return HardwareSignature(
        excitation_board_version="board_v2",
        conditioning_board_version="cond_v4",
        sensor_version="v2b",
        sensor_serial_number=serial,
    )


def _make_entry(signature: HardwareSignature, frequency_hz: float = 1000.0) -> SynchronousDetectionPhaseCalibrationEntry:
    return SynchronousDetectionPhaseCalibrationEntry.single(
        hardware_signature=signature,
        point=SynchronousDetectionPhaseCalibrationPoint(frequency_hz=frequency_hz, delta_phi_degrees=12.5),
    )


def test_load_compensation_enabled_defaults_to_false():
    repository = FakeSynchronousDetectionPhaseCalibrationRepository()

    assert repository.load_compensation_enabled() is False


def test_save_and_load_compensation_enabled_round_trip():
    repository = FakeSynchronousDetectionPhaseCalibrationRepository()

    repository.save_compensation_enabled(True)

    assert repository.load_compensation_enabled() is True


def test_find_by_hardware_signature_returns_empty_list_when_none_recorded():
    repository = FakeSynchronousDetectionPhaseCalibrationRepository()

    assert repository.find_by_hardware_signature(_make_signature()) == []


def test_add_then_find_by_hardware_signature_round_trips_entry():
    repository = FakeSynchronousDetectionPhaseCalibrationRepository()
    signature = _make_signature()
    entry = _make_entry(signature)

    repository.add(entry)

    assert repository.find_by_hardware_signature(signature) == [entry]


def test_add_is_append_only_across_different_signatures():
    repository = FakeSynchronousDetectionPhaseCalibrationRepository()
    first_signature = _make_signature(serial="SN-FIRST")
    second_signature = _make_signature(serial="SN-SECOND")
    first_entry = _make_entry(first_signature, frequency_hz=1000.0)
    second_entry = _make_entry(second_signature, frequency_hz=2000.0)

    repository.add(first_entry)
    repository.add(second_entry)

    assert repository.find_by_hardware_signature(first_signature) == [first_entry]
    assert repository.find_by_hardware_signature(second_signature) == [second_entry]


def test_add_appends_multiple_entries_for_same_signature():
    repository = FakeSynchronousDetectionPhaseCalibrationRepository()
    signature = _make_signature()
    first_entry = _make_entry(signature, frequency_hz=1000.0)
    second_entry = _make_entry(signature, frequency_hz=1500.0)

    repository.add(first_entry)
    repository.add(second_entry)

    assert repository.find_by_hardware_signature(signature) == [first_entry, second_entry]


def test_save_compensation_enabled_never_touches_entries():
    repository = FakeSynchronousDetectionPhaseCalibrationRepository()
    signature = _make_signature()
    entry = _make_entry(signature)
    repository.add(entry)

    repository.save_compensation_enabled(True)

    assert repository.find_by_hardware_signature(signature) == [entry]
