"""
acquisition_parameters_translator - What the catalog shows of an acquisition, read from its acquisition
parameters file, the contract of the acquisition (see acquisition_parameters_translator_intention.md).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Tuple

from ....aefi_acquisition_upstream.upstream_calibration import RotationConvention
from ....domain.acquisition_record.value_objects.applied_rotation.applied_rotation import AppliedRotation

# Activity kind other than a scan (time series, frequency sweep): not an acquisition of the catalog.
NOT_A_SCAN = "not_a_scan"
# Schema where a fly scan stopped being declared as a step scan.
FLY_SCAN_DECLARED_FROM = (1, 4)
_SCAN_KINDS = {"step_scan": "stepScan", "fly_scan": "flyScan"}
LIFT_OFF_ALIAS = "lift_off"
LIFT_OFF_UNIT = "mm"
ANGLE_UNIT = "deg"
_ANGLES = ("theta_x", "theta_y", "theta_z")


@dataclass(frozen=True)
class ParametersDescription:
    kind: Optional[str]  # "stepScan", "flyScan", NOT_A_SCAN, or None: the contract does not say
    acquired_at: Optional[datetime]
    measured_object: Optional[str]
    lift_off_mm: Optional[float]
    schema_version: Optional[str]
    # The rotation the acquisition applied (None: the file does not say, or says what cannot be used) and why it
    # cannot be used (None: nothing to say). Never both set.
    applied_rotation: Optional[AppliedRotation] = None
    rotation_problem: Optional[str] = None


def _get(mapping: Any, *keys: str) -> Any:
    for key in keys:
        if not isinstance(mapping, dict):
            return None
        mapping = mapping.get(key)
    return mapping


def _version(text: Any) -> Optional[tuple]:
    try:
        return tuple(int(part) for part in str(text).split("."))
    except ValueError:
        return None


def _kind(activity_kind: Any, schema_version: Any) -> Optional[str]:
    if activity_kind is None:
        return None
    if activity_kind not in _SCAN_KINDS:
        return NOT_A_SCAN
    version = _version(schema_version)
    if activity_kind == "step_scan" and (version is None or version < FLY_SCAN_DECLARED_FROM):
        return None
    return _SCAN_KINDS[activity_kind]


def _datetime(text: Any) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(text) if isinstance(text, str) else None
    except ValueError:
        return None


def _lift_off_mm(feature: Any) -> Optional[float]:
    if not isinstance(feature, dict):
        return None
    for quantity in feature.values():
        if isinstance(quantity, dict) and quantity.get("alias") == LIFT_OFF_ALIAS:
            if quantity.get("unit") == LIFT_OFF_UNIT and isinstance(quantity.get("value"), (int, float)):
                return float(quantity["value"])
            return None
    return None


def _angle(rotation: dict, name: str) -> Tuple[Optional[float], Optional[str]]:
    """(degrees, None) or (None, why the angle cannot be used)."""
    quantity = rotation.get(name)
    if not isinstance(quantity, dict) or quantity.get("value") is None:
        return None, f"angle {name} absent"
    value = quantity["value"]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None, f"angle {name} illisible ({value!r})"
    if quantity.get("unit") != ANGLE_UNIT:
        return None, f"angle {name} en {quantity.get('unit')!r}, attendu {ANGLE_UNIT!r}"
    return float(value), None


def _rotation(deployment: Any) -> Tuple[Optional[AppliedRotation], Optional[str]]:
    """The rotation the acquisition applied, or why it cannot be used. (None, None) when the file describes none."""
    rotation = _get(deployment, "rotation_applied")
    if rotation is None:
        return None, None
    if not isinstance(rotation, dict):
        return None, "rotation appliquée mal formée"
    if rotation.get("applies_to_data") is True:
        return None, "valeurs déjà tournées par l'acquisition (applies_to_data) : les tourner encore serait faux"
    convention = rotation.get("convention")
    if not isinstance(convention, dict):
        return None, "convention de rotation absente"
    try:
        RotationConvention(convention.get("type"), convention.get("order"), convention.get("direction"))
    except ValueError:
        return None, (
            f"convention de rotation non prise en charge ({convention.get('type')}, "
            f"{convention.get('order')}, {convention.get('direction')})"
        )
    angles = []
    for name in _ANGLES:
        degrees, problem = _angle(rotation, name)
        if problem is not None:
            return None, problem
        angles.append(degrees)
    origin, calibration_id = rotation.get("origin"), rotation.get("calibration_id")
    return AppliedRotation(
        angles=(angles[0], angles[1], angles[2]),
        convention_type=convention["type"], convention_order=convention["order"],
        convention_direction=convention["direction"],
        origin=origin if isinstance(origin, str) else None,
        calibration_id=calibration_id if isinstance(calibration_id, str) else None,
    ), None


def describe(parameters: Any) -> ParametersDescription:
    schema_version = _get(parameters, "schema", "version")
    feature = _get(parameters, "feature_of_interest")
    description = _get(feature, "description")
    applied_rotation, rotation_problem = _rotation(_get(parameters, "measurement_chain", "sensor", "deployment"))
    return ParametersDescription(
        kind=_kind(_get(parameters, "provenance", "activity", "kind"), schema_version),
        acquired_at=_datetime(_get(parameters, "provenance", "activity", "started_at")),
        measured_object=description if isinstance(description, str) and description else None,
        lift_off_mm=_lift_off_mm(feature),
        schema_version=str(schema_version) if schema_version is not None else None,
        applied_rotation=applied_rotation,
        rotation_problem=rotation_problem,
    )
