"""
Hardware Signature JSON

Responsibility:
- The one JSON shape of a `HardwareSignature` in every calibration registry
  that stores one (synchronous detection phase, sensor calibration).
"""

from typing import Any, Dict

from domain.calibration.value_objects.hardware_component_name.hardware_component_name import (
    HardwareComponentName,
)
from domain.calibration.value_objects.hardware_signature.hardware_signature import HardwareSignature

# Keys written before the board fields became component references (2026-09-25).
_LEGACY_KEYS = {
    "excitation_electronics_board_name": "excitation_board_version",
    "conditioning_electronics_board_name": "conditioning_board_version",
}


def hardware_signature_to_json(signature: HardwareSignature) -> Dict[str, Any]:
    return {
        "excitation_electronics_board_name": signature.excitation_electronics_board_name,
        "conditioning_electronics_board_name": signature.conditioning_electronics_board_name,
        "sensor_name": signature.sensor_name,
    }


def hardware_signature_from_json(raw: Dict[str, Any]) -> HardwareSignature:
    def board(key: str) -> HardwareComponentName:
        return HardwareComponentName(raw[key] if key in raw else raw[_LEGACY_KEYS[key]])

    return HardwareSignature(
        excitation_electronics_board_name=board("excitation_electronics_board_name"),
        conditioning_electronics_board_name=board("conditioning_electronics_board_name"),
        sensor_name=HardwareComponentName(raw["sensor_name"] if "sensor_name" in raw else _legacy_sensor_name(raw)),
    )


def _legacy_sensor_name(raw: Dict[str, Any]) -> str:
    """Before the sensor became a catalog component (2026-09-25) it was
    identified by version + serial number; its component name is
    "<version>_<serial>" (or "<version>" without serial number)."""
    serial = raw.get("sensor_serial_number")
    return f"{raw['sensor_version']}_{serial}" if serial else raw["sensor_version"]
