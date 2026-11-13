"""
Acquisition Parameters v1 Serializer — writes a frequency sweep's facts in the
`acquisition-parameters.json` schema 1.3.

See acquisition_parameters_v1_serializer_intention.md. The sections common to
every acquisition come from infrastructure/persistence/acquisition_parameters/
acquisition_parameters_v1.py; this module adds only what the sweep did:
procedure (role, grid, table height), swept frequency, excitation, columns.
"""

from datetime import datetime
from typing import Any, Dict

from application.frequency_sweep.frequency_sweep_service.dtos.acquisition_parameters_dtos import (
    FrequencySweepAcquisitionParametersDTO,
    FrequencySweepActivityDTO,
)
from application.frequency_sweep.frequency_sweep_service.dtos.frequency_sweep_dtos import VALUE_CHANNELS
from application.shared.acquisition_parameters.acquisition_conditions_dtos import AcquisitionConditionsDTO
from infrastructure.persistence.acquisition_parameters import acquisition_parameters_v1 as v1
from infrastructure.persistence.acquisition_parameters.acquisition_parameters_v1 import (  # noqa: F401 — re-used names
    ACQUISITION_PARAMETERS_FILE_NAME,
)

ACTIVITY_KIND = "frequency_sweep"
PROCEDURE_PATH = f"procedure.{ACTIVITY_KIND}"
TABLE_HEIGHT_KEY = "table_height"

_ROLE_NOTES = {
    "instrument_reference": "Référence instrument : table en position basse, aucun objet sur le banc.",
    "background": "Fond : table à la hauteur de travail, aucun objet sur le banc.",
}
OBJECT_MEASUREMENT = "object_measurement"


def serialize_acquisition_parameters_v1(
    parameters: FrequencySweepAcquisitionParametersDTO, generated_at: datetime
) -> Dict[str, Any]:
    """The acquisition-parameters 1.3 document of one frequency sweep (JSON-ready)."""
    activity, conditions = parameters.activity, parameters.conditions
    warnings, warn = v1.new_warnings()
    provenance = v1.provenance(
        activity_id=activity.activity_id, kind=ACTIVITY_KIND,
        started_at=activity.started_at, ended_at=activity.ended_at,
        status=activity.status, failure_reason=activity.failure_reason,
        owner=activity.controller, held_controls=activity.held_controls,
        software=parameters.software, conditions=conditions, generated_at=generated_at, warn=warn,
        operator_name=activity.operator_name, operator_id=activity.operator_id,
    )
    if activity.status != "completed":
        warn(
            f"{PROCEDURE_PATH}.acquired_frequency_count",
            f"balayage incomplet ({activity.acquired_frequency_count}/{len(activity.frequencies_hz)} fréquences) : "
            "ni référence ni fond utilisable",
        )
    if activity.role == OBJECT_MEASUREMENT:
        feature_of_interest = v1.feature_of_interest(
            present=True, description=activity.measured_object_name or None,
            notes="Mesure objet : même hauteur de table que le fond, objet posé.", warn=warn,
            measured_object_id=activity.measured_object_id or None, lift_off_mm=activity.lift_off_mm,
        )
    else:
        feature_of_interest = v1.feature_of_interest(
            present=False, description=None, notes=_ROLE_NOTES.get(activity.role), warn=warn,
            absent_because=f"rôle {activity.role}",
        )
    components = v1.components(conditions, warn, state_read=(
        "au démarrage du balayage, mémoire du contrôleur — fréquence de l'opérateur, pas celle des points"
    ))
    chip_settings = components["signal_generation_chip"].get("settings")
    if chip_settings is not None:
        chip_settings["frequency"] = {
            "derived_from": f"{PROCEDURE_PATH}.frequency_grid",
            "notes": "balayée : une fréquence par point (colonne frequency_hz)",
        }
    components["microcontroller"]["settings"] = {
        "host_link": v1.host_link(conditions, activity.usb_latency_timer_ms, activity.usb_latency_unknown_reason, warn),
    }
    return {
        "schema": dict(v1.SCHEMA),
        "provenance": provenance,
        "feature_of_interest": feature_of_interest,
        "procedure": {ACTIVITY_KIND: _procedure(activity)},
        "components": components,
        "measurement_chain": _measurement_chain(activity, conditions, warn),
        "data": v1.data(parameters.files, COLUMNS),
        "warnings": warnings,
    }


def _procedure(activity: FrequencySweepActivityDTO) -> Dict[str, Any]:
    return {
        "role": activity.role,
        "frequency_grid": {
            **v1.quantity(list(activity.frequencies_hz), "Hz"),
            "spacing": "logarithmic",
        },
        "samples_per_frequency": v1.quantity(activity.samples_per_frequency, "{sample}"),
        "settle_delay": v1.quantity(activity.settle_delay_s, "s"),
        "frequency_timeout": v1.quantity(activity.frequency_timeout_s, "s"),
        TABLE_HEIGHT_KEY: {
            **v1.quantity(activity.table_height_mm, "mm"),
            "source": "operator",
            "notes": "hauteur de la table lue par l'opérateur sur le panneau de commande de la table",
        },
        "acquired_frequency_count": v1.quantity(activity.acquired_frequency_count, "1"),
    }


def _measurement_chain(
    activity: FrequencySweepActivityDTO, conditions: AcquisitionConditionsDTO, warn: v1.Warn
) -> Dict[str, Any]:
    excitation = activity.excitation
    if activity.excitation_restored is False:
        warn("measurement_chain.excitation.state.operator_frequency_restored_after_activity",
             "fréquence de l'opérateur NON rétablie après le balayage")
    return {
        "excitation": {
            "uses": v1.excitation_uses(),
            "state": {
                "mode": excitation.mode,
                "level_s1_s2": v1.quantity(excitation.level_s1_s2_percent, "%"),
                "level_s3_s4": v1.quantity(excitation.level_s3_s4_percent, "%"),
                "frequency": {"derived_from": f"{PROCEDURE_PATH}.frequency_grid"},
                "operator_frequency": v1.quantity(excitation.operator_frequency_hz, "Hz"),
                "operator_frequency_restored_after_activity": activity.excitation_restored,
            },
        },
        "sensor": {
            "uses": [{"component": "sensor"}],
            "deployment": v1.deployment(
                conditions, applies_to_data=False,
                notes="les fichiers de ce balayage sont dans le repère du capteur (non tournés)", warn=warn,
            ),
        },
        "conditioning": {"uses": [{"component": "conditioning_electronics_board"}]},
        "synchronous_detection": {
            "uses": v1.synchronous_detection_uses(),
            "state": v1.synchronous_detection_state(conditions, warn),
            "notes": (
                "état au démarrage ; la compensation se réapplique à chaque fréquence (point de calibration "
                "le plus proche en fréquence) : décalage appliqué par fréquence dans la colonne "
                "reference_phase_offset_deg"
            ),
        },
        "digitization": {
            "uses": [{"component": "adc"}, {"component": "microcontroller"}],
            "stream": {
                "origin": "started_by_activity" if activity.stream_started_here else "already_running",
                "stopped_after_activity": activity.stream_started_here,
            },
        },
        "positioning": {
            "uses": [{"component": "motors"}],
            "state": v1.positioning_state(
                activity.bench_position_start, activity.bench_position_end,
                activity.bench_position_unknown_reason, motors_held=False, warn=warn, motors=conditions.motors,
            ),
        },
        "auxiliary_probes": {"uses": [], "notes": "aucune sonde auxiliaire lue par ce balayage"},
    }


def _columns() -> Dict[str, Any]:
    columns: Dict[str, Any] = {
        "frequency_index": {"observed_property": "rank of the frequency in the grid", "unit": "1"},
        "frequency_hz": {"observed_property": "excitation frequency (AD9106, all DDS channels)", "unit": "Hz"},
        "samples_count": {"observed_property": "samples averaged at this frequency", "unit": "{sample}"},
        "reference_phase_offset_deg": {
            "observed_property": "phase of the synchronous detection reference relative to the excitation "
                                 "(DDS4 - DDS1) written on the chip at this frequency; empty = unknown",
            "unit": "deg",
        },
        "sample_index": {"observed_property": "index of the sample in the acquisition stream", "unit": "1"},
        "timestamp": {"observed_property": "result time (host clock, sample received)", "format": "ISO 8601 with offset"},
    }
    for channel in VALUE_CHANNELS:
        axis, component = channel.split("_", 1)
        meaning = "in-phase component" if component == "in_phase" else "quadrature component"
        columns[f"{channel}_v"] = {
            "observed_property": f"electric field, {meaning} (sensor output voltage); "
                                 "frequency_response.csv: mean over the samples of the frequency",
            "axis": axis, "frame": "sensor", "unit": "V",
        }
        columns[f"std_{channel}_v"] = {
            "observed_property": f"standard deviation of the {meaning} over the samples of the frequency",
            "axis": axis, "frame": "sensor", "unit": "V",
        }
    return columns


# Description of every column the CSV export writes (frequency_response.csv, samples.csv).
COLUMNS = _columns()
