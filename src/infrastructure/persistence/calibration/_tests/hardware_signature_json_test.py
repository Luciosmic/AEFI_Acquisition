from domain.calibration.value_objects.hardware_signature.hardware_signature import HardwareSignature
from infrastructure.persistence.calibration.hardware_signature_json import (
    hardware_signature_from_json,
    hardware_signature_to_json,
)


def test_round_trip_uses_component_reference_keys():
    signature = HardwareSignature("AmpliHT_v2", "Final_v4", "v2b_SN-3")

    raw = hardware_signature_to_json(signature)

    assert raw["excitation_electronics_board_name"] == "AmpliHT_v2"
    assert raw["conditioning_electronics_board_name"] == "Final_v4"
    assert hardware_signature_from_json(raw) == signature


def test_reads_keys_written_before_the_rename():
    legacy = {
        "excitation_board_version": "AmpliHT_v2",
        "conditioning_board_version": "Final_v4",
        "sensor_version": "v2b",
        "sensor_serial_number": None,
    }

    assert hardware_signature_from_json(legacy) == HardwareSignature("AmpliHT_v2", "Final_v4", "v2b")
