"""
Acquisition Parameters v1 Serializer — writes a throughput sweep's facts in
the `acquisition-parameters.json` schema 1.0.

See acquisition_parameters_v1_serializer_intention.md. The sections common to
every acquisition come from infrastructure/persistence/acquisition_parameters/
acquisition_parameters_v1.py; this module adds only what the sweep did:
procedure, swept n_avg, cut excitation, stream origin, bench position, columns.
"""

from datetime import datetime
from typing import Any, Dict

from application.services.acquisition_throughput_characterization_service.dtos.acquisition_parameters_dtos import (
    AcquisitionParametersDTO,
    ThroughputActivityDTO,
)
from application.services.acquisition_throughput_characterization_service.dtos.acquisition_throughput_dtos import (
    VALUE_CHANNELS,
)
from application.shared.acquisition_parameters.acquisition_conditions_dtos import AcquisitionConditionsDTO
from infrastructure.persistence.acquisition_parameters import acquisition_parameters_v1 as v1
from infrastructure.persistence.acquisition_parameters.acquisition_parameters_v1 import (  # noqa: F401 — re-used names
    ACQUISITION_PARAMETERS_FILE_NAME,
    UCUM_UNITS,
)

ACTIVITY_KIND = "mcu_throughput_characterization"
PROCEDURE_PATH = f"procedure.{ACTIVITY_KIND}"


def serialize_acquisition_parameters_v1(parameters: AcquisitionParametersDTO, generated_at: datetime) -> Dict[str, Any]:
    """The acquisition-parameters 1.0 document of one throughput sweep (JSON-ready)."""
    activity, conditions = parameters.activity, parameters.conditions
    warnings, warn = v1.new_warnings()
    provenance = v1.provenance(
        activity_id=activity.activity_id, kind=ACTIVITY_KIND,
        started_at=activity.started_at, ended_at=activity.ended_at,
        status=activity.status, failure_reason=activity.failure_reason,
        owner=activity.controller, held_controls=activity.held_controls,
        software=parameters.software, conditions=conditions, generated_at=generated_at, warn=warn,
    )
    feature_of_interest = v1.feature_of_interest(
        present=False, description=None,
        notes="Caractérisation de la chaîne d'acquisition seule : excitation coupée, aucun objet mesuré.",
        warn=warn, absent_because="excitation coupée",
    )
    components = v1.components(conditions, warn, state_read=(
        "pendant le balayage (excitation coupée), mémoire du contrôleur — pas de relecture des registres"
    ))
    components["microcontroller"]["settings"] = _microcontroller_settings(activity, conditions, warn)
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


def _procedure(activity: ThroughputActivityDTO) -> Dict[str, Any]:
    return {
        "n_avg_grid": v1.quantity(list(activity.request.n_avg_values), "{sample}"),
        "samples_per_point": v1.quantity(activity.request.samples_per_point, "{sample}"),
        "settle_delay": v1.quantity(activity.settle_delay_s, "s"),
        "point_timeout": v1.quantity(activity.sample_timeout_s, "s"),
        "excitation": activity.excitation_condition.name,
    }


def _microcontroller_settings(
    activity: ThroughputActivityDTO, conditions: AcquisitionConditionsDTO, warn: v1.Warn
) -> Dict[str, Any]:
    if activity.n_avg_restored is False:
        warn("components.microcontroller.settings.n_avg_before_activity", "n_avg de l'opérateur NON restauré après le balayage")
    return {
        "n_avg": {"derived_from": f"{PROCEDURE_PATH}.n_avg_grid", "notes": "balayé : une valeur par point"},
        "n_avg_before_activity": v1.quantity(activity.operator_n_avg, "{sample}"),
        "n_avg_restored_after_activity": activity.n_avg_restored,
        "host_link": v1.host_link(conditions, activity.usb_latency_timer_ms, activity.usb_latency_unknown_reason, warn),
    }


def _measurement_chain(activity: ThroughputActivityDTO, conditions: AcquisitionConditionsDTO, warn: v1.Warn) -> Dict[str, Any]:
    operator = activity.operator_excitation
    condition = activity.excitation_condition
    return {
        "excitation": {
            "uses": v1.excitation_uses(),
            "state": {
                "applied": condition.name,
                "definition": condition.definition,
                "derived_from": v1.CHIP_CHANNELS_PATH,
                "operator_setting": {
                    "mode": operator.mode,
                    "level_s1_s2": v1.quantity(operator.level_s1_s2_percent, "%"),
                    "level_s3_s4": v1.quantity(operator.level_s3_s4_percent, "%"),
                },
                "operator_setting_restored_after_activity": activity.excitation_restored,
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
                activity.bench_position_unknown_reason, motors_held=False, warn=warn,
            ),
        },
        "auxiliary_probes": {"uses": [], "notes": "aucune sonde auxiliaire lue par ce balayage"},
    }


def _columns() -> Dict[str, Any]:
    columns: Dict[str, Any] = {
        "n_avg": {"observed_property": "MCU averaging: ADC conversions averaged per returned sample", "unit": "{sample}"},
        "sample_index": {"observed_property": "index of the sample in the acquisition stream", "unit": "1"},
        "timestamp": {"observed_property": "result time (host clock, sample received)", "format": "ISO 8601 with offset"},
        "sample_period_s": {"observed_property": "mean period between consecutive samples", "unit": "s"},
        "sample_rate_per_s": {"observed_property": "returned samples per second", "unit": "{sample}/s"},
        "adc_conversions_per_s": {"observed_property": "ADC conversions per second (n_avg x sample rate)", "unit": "{conversion}/s"},
        "noise_rms_v": {"observed_property": "quadratic mean of the 6 channels' standard deviation", "unit": "V"},
        "noise_in_one_second_v": {"observed_property": "noise of a 1 s average at this sample rate", "unit": "V"},
    }
    for channel in VALUE_CHANNELS:
        axis, component = channel.split("_", 1)
        meaning = "in-phase component" if component == "in_phase" else "quadrature component"
        columns[f"{channel}_v"] = {
            "observed_property": f"electric field, {meaning} (sensor output voltage)",
            "axis": axis, "frame": "sensor", "unit": "V",
        }
        columns[f"noise_v_rms_{channel}"] = {
            "observed_property": f"standard deviation of the {meaning} over the point's samples",
            "axis": axis, "frame": "sensor", "unit": "V",
        }
    return columns


# Description of every column the CSV export writes (summary.csv, samples.csv).
COLUMNS = _columns()
