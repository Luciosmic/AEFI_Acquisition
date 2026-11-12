"""
Scan Acquisition Parameters v1 Serializer — writes a step scan's or a time
series' facts in the `acquisition-parameters.json` schema 1.0.

See scan_acquisition_parameters_v1_serializer_intention.md. The sections
common to every acquisition come from infrastructure/persistence/
acquisition_parameters/acquisition_parameters_v1.py; this module adds only what
a scan / time series did: procedure, excitation as set, probe, positions, columns.
"""

from datetime import datetime
from typing import Any, Dict

from application.services.scan_export_service.dtos.scan_acquisition_parameters_dtos import (
    STEP_SCAN,
    ColumnStabilizationDTO,
    ScanAcquisitionParametersDTO,
    ScanActivityDTO,
    StepScanProcedureDTO,
)
from application.shared.acquisition_parameters.acquisition_conditions_dtos import AcquisitionConditionsDTO
from infrastructure.persistence.acquisition_parameters import acquisition_parameters_v1 as v1

_AXES = ("x", "y", "z")
_DEMODULATION = {"in_phase": "in-phase", "quadrature": "quadrature"}


def serialize_scan_acquisition_parameters_v1(
    parameters: ScanAcquisitionParametersDTO, generated_at: datetime,
    document_name: str = v1.ACQUISITION_PARAMETERS_FILE_NAME,
) -> Dict[str, Any]:
    """The acquisition-parameters 1.0 document of one step scan or time series (JSON-ready);
    `document_name`: the file it is written to (listed in data.files)."""
    activity, conditions = parameters.activity, parameters.conditions
    warnings, warn = v1.new_warnings()
    provenance = v1.provenance(
        activity_id=activity.activity_id, kind=activity.kind,
        started_at=activity.started_at, ended_at=activity.ended_at,
        status=activity.status, failure_reason=activity.failure_reason,
        owner=activity.owner, held_controls=activity.held_controls,
        software=parameters.software, conditions=conditions, generated_at=generated_at, warn=warn,
        operator_name=activity.operator, operator_id=activity.operator_id,
        operator_comment=activity.comment,
    )
    # Typed by the operator at start (Scan / Continuous Reading panels); empty = warning.
    feature_of_interest = v1.feature_of_interest(
        present=True, description=activity.measured_object, notes=None, warn=warn,
        measured_object_id=activity.measured_object_id,
        lift_off_mm=activity.lift_off_mm,
    )
    components = v1.components(conditions, warn)
    components["microcontroller"]["settings"] = _microcontroller_settings(activity, conditions, warn)
    components["electric_field_probe"] = _probe(activity)
    procedure = _step_scan_procedure(activity.procedure) if activity.kind == STEP_SCAN else {}
    if activity.kind == STEP_SCAN:
        procedure["column_stabilization"] = _column_stabilization(activity.column_stabilization, warn)
    data = v1.data(
        parameters.files, STEP_SCAN_COLUMNS if activity.kind == STEP_SCAN else TIME_SERIES_COLUMNS, document_name
    )
    for listed in data["files"]:
        if listed["format"] == "HDF5":
            listed["notes"] = (
                "empreinte à la fin de l'acquisition, avant le post-traitement "
                "(qui ajoute ses étapes dans ce fichier)"
            )
    return {
        "schema": dict(v1.SCHEMA),
        "provenance": provenance,
        "feature_of_interest": feature_of_interest,
        "procedure": {activity.kind: procedure},
        "components": components,
        "measurement_chain": _measurement_chain(activity, conditions, warn),
        "data": data,
        "warnings": warnings,
    }


def _step_scan_procedure(procedure: StepScanProcedureDTO) -> Dict[str, Any]:
    q = v1.quantity
    return {
        "zone": {
            "x_min": q(procedure.x_min_mm, "mm"), "x_max": q(procedure.x_max_mm, "mm"),
            "y_min": q(procedure.y_min_mm, "mm"), "y_max": q(procedure.y_max_mm, "mm"),
        },
        "grid": {"x_nb_points": procedure.x_nb_points, "y_nb_points": procedure.y_nb_points, "total_points": procedure.total_points},
        "pattern": procedure.pattern,
        "fast_axis": procedure.fast_axis,
        "stabilization_delay": q(procedure.stabilization_delay_ms, "ms"),
        "averaging_per_position": q(procedure.averaging_per_position, "{sample}"),
        "measurement_uncertainty": q(procedure.measurement_uncertainty_v, "V"),
        "differential": {"enabled": procedure.differential_mode, "settle_delay": q(procedure.differential_settle_delay_ms, "ms")},
        "estimated_duration": q(procedure.estimated_duration_s, "s"),
    }


# 1.3: the vibration the column is judged on (ColumnRestCriterion.vibration_g).
VIBRATION = ("RMS de |a − ā| : écart quadratique moyen du vecteur accélération à sa moyenne ā sur la fenêtre "
             "(= racine(σx² + σy² + σz²), σ de population) ; indépendant de l'orientation de la carte, retire la "
             "pesanteur et le décalage statique")


def _column_stabilization(stabilization, warn: v1.Warn):
    """How the column was settled before each point; null while the scan runs (known at its end)
    and when no stabilization was asked for (delay 0)."""
    if stabilization is None:
        return None
    s: ColumnStabilizationDTO = stabilization
    path = "procedure.step_scan.column_stabilization"
    q = v1.quantity
    waits = dict(s.waits)
    if not s.rest_measured:
        method = "none"
    elif s.rest_vibration_g is None:
        method = "fixed_delay"
        warn(path, f"stabilisation au délai fixe à chaque point : {s.unavailable_reason or 'raison inconnue'}")
    else:
        method = "accelerometer"
        if waits.get("timeout"):
            warn(path, f"{waits['timeout']} attente(s) arrêtée(s) au délai maximal de {s.timeout_s:g} s : "
                       "colonne mesurée avant son retour au repos (voir le fichier column-stabilization)")
        if waits.get("fixed_delay"):
            warn(path, f"{waits['fixed_delay']} attente(s) au délai fixe : accéléromètre muet pendant le scan")
    return {
        "method": method,
        "criterion": None if s.window_s is None else {
            "description": ("au repos quand la vibration sur la dernière fenêtre ne dépasse pas factor × le niveau "
                            "de repos ; au moins minimum_delay et une fenêtre après l'arrêt, au plus timeout"),
            "vibration": VIBRATION,
            "rest_measurement_duration": q(s.rest_measurement_s, "s"),
            "window": q(s.window_s, "s"),
            "factor": q(s.factor, "1"),
            "timeout": q(s.timeout_s, "s"),
            "minimum_delay": q(s.minimum_delay_s, "s"),
        },
        "rest_vibration": q(s.rest_vibration_g, "[g]"),
        "rest_sample_count": s.rest_sample_count,
        "unavailable_reason": s.unavailable_reason,
        "waits": waits,
        "accelerometer_samples": s.accelerometer_samples_written,
    }


def _microcontroller_settings(activity: ScanActivityDTO, conditions: AcquisitionConditionsDTO, warn: v1.Warn) -> Dict[str, Any]:
    if conditions.microcontroller_n_avg is None:
        warn("components.microcontroller.settings.n_avg", f"n_avg inconnu : {v1.reason(conditions, 'microcontroller_n_avg')}")
    return {
        "n_avg": v1.quantity(conditions.microcontroller_n_avg, "{sample}"),
        "host_link": v1.host_link(conditions, activity.usb_latency_timer_ms, activity.usb_latency_unknown_reason, warn),
    }


def _probe(activity: ScanActivityDTO) -> Dict[str, Any]:
    probe = activity.probe
    if probe is None:  # optional auxiliary probe: not connected is not unknown
        return {"component": None, "notes": "aucune sonde auxiliaire connectée au démarrage"}
    q = v1.quantity
    return {
        "component": {"brand": probe.brand, "model": probe.model, "serial_number": probe.serial_number,
                      "axis_labels": list(probe.axis_labels)},
        "state": {
            "battery_voltage": q(probe.battery_voltage_v, "V"),
            "battery_percentage": q(probe.battery_percentage, "%"),
            "battery_remaining": q(probe.battery_remaining_hours, "h"),
        },
    }


def _measurement_chain(activity: ScanActivityDTO, conditions: AcquisitionConditionsDTO, warn: v1.Warn) -> Dict[str, Any]:
    excitation = activity.excitation
    step_scan = activity.kind == STEP_SCAN
    return {
        "excitation": {
            "uses": v1.excitation_uses(),
            "state": {
                "mode": excitation.mode,
                "level_s1_s2": v1.quantity(excitation.level_s1_s2_percent, "%"),
                "level_s3_s4": v1.quantity(excitation.level_s3_s4_percent, "%"),
                "derived_from": v1.CHIP_CHANNELS_PATH,
            },
        },
        "sensor": {
            "uses": [{"component": "sensor"}],
            "deployment": v1.deployment(
                conditions, applies_to_data=False,
                notes="tensions exportées dans le repère du capteur (rotation non appliquée aux valeurs)", warn=warn,
            ),
        },
        "conditioning": {"uses": [{"component": "conditioning_electronics_board"}]},
        "synchronous_detection": {
            "uses": v1.synchronous_detection_uses(),
            "state": v1.synchronous_detection_state(conditions, warn),
        },
        "digitization": {"uses": [{"component": "adc"}, {"component": "microcontroller"}]},
        "positioning": {
            "uses": [{"component": "motors"}],
            "state": v1.positioning_state(
                activity.bench_position_start, activity.bench_position_end,
                activity.bench_position_unknown_reason, motors_held=step_scan, warn=warn, motors=conditions.motors,
            ),
        },
        "auxiliary_probes": (
            {"uses": [{"component": "electric_field_probe"}]} if activity.probe is not None
            else {"uses": [], "notes": "aucune sonde auxiliaire connectée au démarrage"}
        ),
    }


def _aefi_voltage_columns(prefix: str, meaning: str) -> Dict[str, Dict[str, str]]:
    return {
        f"{prefix}voltage_{axis}_{part}": {
            "observed_property": f"{meaning}, {label} component (synchronous detection)",
            "axis": axis, "frame": "sensor", "unit": "V",
        }
        for axis in _AXES for part, label in _DEMODULATION.items()
    }


_VOLTAGE = "AEFI sensor output voltage (electric field)"

# Description of every column the scan CSV files write (main file + probe sidecar).
STEP_SCAN_COLUMNS: Dict[str, Dict[str, str]] = {
    "scan_id": {"observed_property": "acquisition id (provenance.activity.id)"},
    "point_index": {"observed_property": "scan point index (acquisition order)", "unit": "1"},
    "x": {"observed_property": "position", "axis": "x", "frame": "bench", "unit": "mm"},
    "y": {"observed_property": "position", "axis": "y", "frame": "bench", "unit": "mm"},
    **{
        f"{axis}_increments_commanded": {
            "observed_property": "position in controller increments, as commanded (same conversion as the move command; "
                                 "within one increment for a fly scan, whose positions are projected)",
            "axis": axis, "frame": "bench", "unit": "{step}",
        }
        for axis in ("x", "y")
    },
    **{
        f"{axis}_increments_read": {
            "observed_property": "position in controller increments, as reported by the controller when the point was "
                                 "recorded (empty during a fly scan: the axes are moving)",
            "axis": axis, "frame": "bench", "unit": "{step}",
        }
        for axis in ("x", "y")
    },
    **_aefi_voltage_columns("", _VOLTAGE),
    **{
        f"std_dev_{name[len('voltage_'):]}": {
            **column, "observed_property": f"standard deviation over averaging_per_position samples of the {column['observed_property']}",
        }
        for name, column in _aefi_voltage_columns("", _VOLTAGE).items()
    },
    **_aefi_voltage_columns("baseline_", "AEFI sensor output voltage with excitation muted (differential mode)"),
    "field_*": {"observed_property": "electric field, auxiliary probe", "frame": "probe", "unit": "V/m"},
    "field_std_dev_*": {"observed_property": "standard deviation of the electric field, auxiliary probe", "frame": "probe", "unit": "V/m"},
    "baseline_field_*": {"observed_property": "electric field, auxiliary probe, excitation muted", "frame": "probe", "unit": "V/m"},
    "baseline_field_std_dev_*": {"observed_property": "standard deviation of the muted electric field, auxiliary probe", "frame": "probe", "unit": "V/m"},
    # 1.3 — file `accelerometer`: the inertial probe stream while it ran during the scan.
    "accelerometer_sample_index": {"file": "accelerometer", "observed_property": "index of the sample in the inertial probe stream", "unit": "1"},
    "accelerometer_timestamp": {"file": "accelerometer", "observed_property": "result time (host clock, sample received)", "format": "ISO 8601 with offset"},
    **{
        f"acceleration_{axis}": {"file": "accelerometer", "observed_property": "acceleration of the column (gravity included)",
                                 "axis": axis, "frame": "inertial probe board", "unit": "[g]"}
        for axis in _AXES
    },
    # 1.3 — file `column-stabilization`: one row per wait, when the column was judged on the accelerometer.
    "stabilization_method": {"file": "column-stabilization", "observed_property": "how the wait before point_index ended: "
                             "accelerometer (back at rest), fixed_delay (accelerometer silent), timeout (still vibrating), "
                             "interrupted (scan stopped)"},
    "stabilization_stopped_at": {"file": "column-stabilization", "observed_property": "end of the move before the wait (host clock)", "format": "ISO 8601 with offset"},
    "stabilization_waited": {"file": "column-stabilization", "observed_property": "time from the end of the move to the measurement", "unit": "s"},
    "stabilization_vibration": {"file": "column-stabilization", "observed_property": f"vibration over the last window when the wait ended: {VIBRATION}", "unit": "[g]"},
    "stabilization_threshold": {"file": "column-stabilization", "observed_property": "factor × rest vibration (procedure.step_scan.column_stabilization)", "unit": "[g]"},
}

# Description of every column the time series CSV writes.
TIME_SERIES_COLUMNS: Dict[str, Dict[str, str]] = {
    "sample_index": {"observed_property": "index of the sample in the acquisition stream", "unit": "1"},
    "t_s": {"observed_property": "time since the first sample", "unit": "s"},
    "timestamp": {"observed_property": "result time (host clock, sample received)", "format": "ISO 8601 with offset"},
    **_aefi_voltage_columns("", _VOLTAGE),
}
