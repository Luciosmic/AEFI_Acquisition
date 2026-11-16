"""
acquisition_parameters_translator - What the catalog shows of an acquisition, read from its acquisition
parameters file, the contract of the acquisition (see acquisition_parameters_translator_intention.md).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

# Activity kind other than a scan (time series, frequency sweep): not an acquisition of the catalog.
NOT_A_SCAN = "not_a_scan"
# Schema where a fly scan stopped being declared as a step scan.
FLY_SCAN_DECLARED_FROM = (1, 4)
_SCAN_KINDS = {"step_scan": "stepScan", "fly_scan": "flyScan"}
LIFT_OFF_ALIAS = "lift_off"
LIFT_OFF_UNIT = "mm"


@dataclass(frozen=True)
class ParametersDescription:
    kind: Optional[str]  # "stepScan", "flyScan", NOT_A_SCAN, or None: the contract does not say
    acquired_at: Optional[datetime]
    measured_object: Optional[str]
    lift_off_mm: Optional[float]
    schema_version: Optional[str]


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


def describe(parameters: Any) -> ParametersDescription:
    schema_version = _get(parameters, "schema", "version")
    feature = _get(parameters, "feature_of_interest")
    description = _get(feature, "description")
    return ParametersDescription(
        kind=_kind(_get(parameters, "provenance", "activity", "kind"), schema_version),
        acquired_at=_datetime(_get(parameters, "provenance", "activity", "started_at")),
        measured_object=description if isinstance(description, str) and description else None,
        lift_off_mm=_lift_off_mm(feature),
        schema_version=str(schema_version) if schema_version is not None else None,
    )
