"""
Acquisition Parameters v1 Serializer — writes a throughput sweep's facts in
the `acquisition-parameters.json` schema 1.0.

See acquisition_parameters_v1_serializer_intention.md. The schema contract
is application/services/scan_export_service/acquisition_parameters/acquisition_parameters_intention.md.
This is the ONLY place that knows the schema layout and units for the
throughput sweep: a shared schema builder replaces it without touching the
application.
"""

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Sequence

from application.shared.acquisition_parameters.acquisition_conditions_dtos import (
    AcquisitionConditionsDTO,
    BenchPositionDTO,
    ExportedFileDTO,
    MountedComponentDTO,
    SignalGenerationSettingsDTO,
    SoftwareProvenanceDTO,
)
from application.services.acquisition_throughput_characterization_service.dtos.acquisition_parameters_dtos import (
    AcquisitionParametersDTO,
    ThroughputActivityDTO,
)
from application.services.acquisition_throughput_characterization_service.dtos.acquisition_throughput_dtos import (
    VALUE_CHANNELS,
)
from domain.calibration.value_objects.rotation_convention.rotation_convention import RotationConvention
from domain.shared_kernel.excitation.value_objects.phase_angle import PhaseAngle

ACQUISITION_PARAMETERS_FILE_NAME = "acquisition-parameters.json"
SCHEMA_NAME = "aefi-acquisition-parameters"
SCHEMA_VERSION = "1.0"
ACTIVITY_KIND = "mcu_throughput_characterization"

# Every unit this module writes, as UCUM codes (guard test: nothing else).
# ponytail: UCUM has no fractional exponent — V/√Hz is written V/{sqrt_Hz}.
UCUM_UNITS = frozenset({
    "1", "%", "s", "ms", "Hz", "V", "deg", "mm", "By", "Bd",
    "{sample}", "{sample}/s", "{conversion}/s",
    "{DDS_gain_code}", "{DDS_offset_code}", "{DDS_constant_code}",
    "V/(V/m)", "V/V", "V/{sqrt_Hz}", "{DDS_gain_code}/V", "V/{LSB}", "V{RMS}", "um/{step}", "mm/s", "mm/s2",
})
# Component catalog display units (HardwareComponentKind) -> UCUM.
_UCUM_BY_CATALOG_UNIT = {
    "V/(V/m)": "V/(V/m)",
    "V/V": "V/V",
    "Hz": "Hz",
    "V": "V",
    "V/√Hz": "V/{sqrt_Hz}",
    "value/V": "{DDS_gain_code}/V",
    "V/LSB": "V/{LSB}",
    "V RMS": "V{RMS}",
    "mesures/s": "{sample}/s",
    "µm/pas": "um/{step}",
    "mm/s": "mm/s",
    "mm/s²": "mm/s2",
}
_UCUM_BY_CURVE_X_LABEL = {"n_avg": "{sample}", "OSR": "1"}

PROCEDURE_PATH = f"procedure.{ACTIVITY_KIND}"
CHIP_CHANNELS_PATH = "components.signal_generation_chip.settings.channels"
# Channels of the AD9106 per function (measurement_chain `uses`).
EXCITATION_CHANNELS = ["1", "2"]
REFERENCE_CHANNELS = ["3", "4"]

Warn = Callable[[str, str], None]


def serialize_acquisition_parameters_v1(parameters: AcquisitionParametersDTO, generated_at: datetime) -> Dict[str, Any]:
    """The acquisition-parameters 1.0 document of one throughput sweep (JSON-ready)."""
    activity, conditions = parameters.activity, parameters.conditions
    warnings: List[Dict[str, str]] = []

    def warn(path: str, message: str) -> None:
        warnings.append({"path": path, "message": message})

    return {
        "schema": {"name": SCHEMA_NAME, "version": SCHEMA_VERSION},
        "provenance": _provenance(activity, conditions, parameters.software, generated_at, warn),
        "feature_of_interest": _feature_of_interest(warn),
        "procedure": {ACTIVITY_KIND: _procedure(activity)},
        "components": _components(activity, conditions, warn),
        "measurement_chain": _measurement_chain(activity, conditions, warn),
        "data": _data(parameters.files),
        "warnings": warnings,
    }


# -- helpers ----------------------------------------------------------------------------


def _q(value: Any, unit: str) -> Optional[Dict[str, Any]]:
    """Quantity object: the unit travels with the value."""
    return None if value is None else {"value": value, "unit": unit}


def _iso(moment: Optional[datetime]) -> Optional[str]:
    """ISO 8601 with offset, local time (naive datetimes are local)."""
    return None if moment is None else moment.astimezone().isoformat(timespec="milliseconds")


def _ucum(catalog_unit: str, path: str, warn: Warn) -> str:
    unit = _UCUM_BY_CATALOG_UNIT.get(catalog_unit)
    if unit is None:
        warn(path, f"unité du catalogue « {catalog_unit} » sans équivalent UCUM connu : écrite en annotation")
        return "{" + "".join(c if c.isalnum() else "_" for c in catalog_unit) + "}"
    return unit


def _reason(conditions: AcquisitionConditionsDTO, field: str, default: str = "raison inconnue") -> str:
    return conditions.unknown.get(field, default)


# -- provenance (PROV-O) -------------------------------------------------------------


def _provenance(
    activity: ThroughputActivityDTO,
    conditions: AcquisitionConditionsDTO,
    software: SoftwareProvenanceDTO,
    generated_at: datetime,
    warn: Warn,
) -> Dict[str, Any]:
    if activity.ended_at is None:
        warn(
            "provenance.activity.ended_at",
            "acquisition non terminée : document écrit au démarrage — resté ainsi, le balayage a été interrompu",
        )
    if software.commit is None:
        warn("provenance.software.commit", f"commit inconnu : {software.unknown_reason or 'raison inconnue'}")
    if software.dirty is None:
        warn("provenance.software.dirty", "état de l'arbre de travail inconnu : reproductibilité du code non garantie")
    elif software.dirty:
        warn("provenance.software.dirty", "arbre de travail modifié : le code exécuté n'est pas reproductible depuis le commit")
    simulated = sorted(name for name, backend in conditions.hardware_backends.items() if backend != "real")
    if simulated:
        warn("provenance.software.hardware_backends", f"matériel simulé ({', '.join(simulated)}) : ce n'est pas une mesure du banc")
    if not conditions.hardware_backends:
        warn("provenance.software.hardware_backends", "backends matériels (réel / simulé) inconnus")
    warn("provenance.operator.name", "opérateur non enregistré")
    return {
        "activity": {
            "id": activity.activity_id,
            "kind": ACTIVITY_KIND,
            "started_at": _iso(activity.started_at),
            "ended_at": _iso(activity.ended_at),
            "status": activity.status,
            "failure_reason": activity.failure_reason,
            "exclusive_control": {"owner": activity.controller, "held": list(activity.held_controls)},
        },
        "software": {
            "name": software.name,
            "version": software.version,
            "commit": software.commit,
            "branch": software.branch,
            "dirty": software.dirty,
            "hardware_backends": dict(conditions.hardware_backends),
        },
        "operator": {"name": None},
        "generated_at": _iso(generated_at),
    }


def _feature_of_interest(warn: Warn) -> Dict[str, Any]:
    warn(
        "feature_of_interest",
        "aucun objet par construction (excitation coupée) ; la présence éventuelle d'un objet sur le banc n'est pas saisie",
    )
    return {
        "present": False,
        "description": None,
        "notes": "Caractérisation de la chaîne d'acquisition seule : excitation coupée, aucun objet mesuré.",
    }


# -- procedure (SOSA Procedure) ------------------------------------------------------


def _procedure(activity: ThroughputActivityDTO) -> Dict[str, Any]:
    return {
        "n_avg_grid": _q(list(activity.request.n_avg_values), "{sample}"),
        "samples_per_point": _q(activity.request.samples_per_point, "{sample}"),
        "settle_delay": _q(activity.settle_delay_s, "s"),
        "point_timeout": _q(activity.sample_timeout_s, "s"),
        "excitation": activity.excitation_condition.name,
    }


# -- components (SOSA System) --------------------------------------------------------


def _components(activity: ThroughputActivityDTO, conditions: AcquisitionConditionsDTO, warn: Warn) -> Dict[str, Any]:
    components: Dict[str, Any] = {mounted.kind: _component(mounted, warn) for mounted in conditions.components}
    if not conditions.components:
        warn("components", f"catalogue des composants illisible : {_reason(conditions, 'components')}")
    empty = {"component": None, "characterization": None}
    components.setdefault("adc", dict(empty))["settings"] = _adc_settings(conditions, warn)
    components.setdefault("signal_generation_chip", dict(empty))["settings"] = _signal_generation_settings(
        conditions.signal_generation, conditions, warn
    )
    components.setdefault("microcontroller", dict(empty))["settings"] = _microcontroller_settings(
        activity, conditions, warn
    )
    return components


def _component(mounted: MountedComponentDTO, warn: Warn) -> Dict[str, Any]:
    path = f"components.{mounted.kind}"
    if mounted.name is None:
        warn(f"{path}.component", "aucun composant déclaré monté : configuration incomplète")
        return {"component": None, "characterization": None}
    characterization: Dict[str, Any] = {}
    for key, value in mounted.characterization.items():
        key_path = f"{path}.characterization.{key}"
        unit = _ucum(mounted.units.get(key, ""), key_path, warn)
        if value is None:
            characterization[key] = None
            warn(key_path, "non caractérisé")
        elif key in mounted.curve_x_labels:
            characterization[key] = _curve(value, mounted.curve_x_labels[key], unit, key_path, warn)
        else:
            characterization[key] = _q(value, unit)
    return {
        "component": {"name": mounted.name, "id": mounted.entry_id, "recorded_at": _iso(mounted.recorded_at)},
        "characterization": characterization,
    }


def _curve(points, x_label: str, unit: str, path: str, warn: Warn) -> Dict[str, Any]:
    if x_label not in _UCUM_BY_CURVE_X_LABEL:
        warn(f"{path}.abscissa", f"unité de l'abscisse « {x_label} » inconnue : écrite sans dimension")
    pairs = [tuple(point) for point in points]
    return {
        "abscissa": {"name": x_label, "value": [x for x, _ in pairs], "unit": _UCUM_BY_CURVE_X_LABEL.get(x_label, "1")},
        "ordinate": {"value": [y for _, y in pairs], "unit": unit},
    }


def _adc_settings(conditions: AcquisitionConditionsDTO, warn: Warn) -> Optional[Dict[str, Any]]:
    adc = conditions.adc
    if adc is None:
        warn("components.adc.settings", f"réglages ADC inconnus : {_reason(conditions, 'adc')}")
        return None
    return {
        "oversampling_ratio": _q(adc.oversampling_ratio, "1"),
        "clkin_divider": _q(adc.clkin_divider, "1"),
        "iclk_divider": _q(adc.iclk_divider, "1"),
        "reference_voltage": _q(adc.reference_voltage_v, "V"),
        "reference_source": adc.reference_source,
        "high_resolution": adc.high_resolution,
        "negative_charge_pump": adc.negative_charge_pump,
        "channels": {
            channel: {"digital_gain": _q(gain, "1"), "enabled": adc.channel_enabled.get(channel)}
            for channel, gain in sorted(adc.channel_gains.items(), key=lambda item: int(item[0]))
        },
    }


def _signal_generation_settings(
    chip: Optional[SignalGenerationSettingsDTO], conditions: AcquisitionConditionsDTO, warn: Warn
) -> Optional[Dict[str, Any]]:
    path = "components.signal_generation_chip.settings"
    if chip is None:
        warn(path, f"réglages AD9106 inconnus : {_reason(conditions, 'signal_generation')}")
        return None
    for flag in ("link_dds1_dds2", "enforce_dds3_dds4_quadrature", "link_dds3_dds4_gain"):
        if getattr(chip, flag) is None:
            warn(f"{path}.{flag}", "inconnu (configuration AD9106 illisible)")
    return {
        "frequency": _q(chip.frequency_hz, "Hz"),
        "channels": {
            channel: {
                "digital_gain": {"code": dds.gain_code, "unit": "{DDS_gain_code}"},
                "phase": {
                    "code": dds.phase_code,
                    "value": round(PhaseAngle.from_register(dds.phase_code).degrees, 6),
                    "unit": "deg",
                },
                "offset": {"code": dds.offset_code, "unit": "{DDS_offset_code}"},
                "constant": {"code": dds.constant_code, "unit": "{DDS_constant_code}"},
                "mode": dds.mode,
            }
            for channel, dds in sorted(chip.channels.items(), key=lambda item: int(item[0]))
        },
        "link_dds1_dds2": chip.link_dds1_dds2,
        "enforce_dds3_dds4_quadrature": chip.enforce_dds3_dds4_quadrature,
        "link_dds3_dds4_gain": chip.link_dds3_dds4_gain,
        "state_read": "pendant le balayage (excitation coupée), mémoire du contrôleur — pas de relecture des registres",
    }


def _microcontroller_settings(
    activity: ThroughputActivityDTO, conditions: AcquisitionConditionsDTO, warn: Warn
) -> Dict[str, Any]:
    path = "components.microcontroller.settings"
    if activity.n_avg_restored is False:
        warn(f"{path}.n_avg_before_activity", "n_avg de l'opérateur NON restauré après le balayage")
    link = conditions.host_link
    if link.serial_port is None:
        warn(f"{path}.host_link.serial_port", f"port série inconnu : {_reason(conditions, 'host_link', 'non connecté ou simulé')}")
    if link.baud_rate is None:
        warn(f"{path}.host_link.baud_rate", "débit de la liaison série inconnu")
    if activity.usb_latency_timer_ms is None:
        warn(f"{path}.host_link.usb_latency_timer", f"latence USB inconnue : {activity.usb_latency_unknown_reason or 'raison inconnue'}")
    return {
        "n_avg": {"derived_from": f"{PROCEDURE_PATH}.n_avg_grid", "notes": "balayé : une valeur par point"},
        "n_avg_before_activity": _q(activity.operator_n_avg, "{sample}"),
        "n_avg_restored_after_activity": activity.n_avg_restored,
        "host_link": {
            "serial_port": link.serial_port,
            "baud_rate": _q(link.baud_rate, "Bd"),
            "usb_latency_timer": _q(activity.usb_latency_timer_ms, "ms"),
            "usb_latency_timer_source": "registre Windows du pilote FTDI (LatencyTimer), appliqué à l'ouverture du port",
        },
    }


# -- measurement chain (SOSA Procedure / Actuation / Observation) --------------------


def _measurement_chain(activity: ThroughputActivityDTO, conditions: AcquisitionConditionsDTO, warn: Warn) -> Dict[str, Any]:
    operator = activity.operator_excitation
    condition = activity.excitation_condition
    return {
        "excitation": {
            "uses": [
                {"component": "signal_generation_chip", "channels": EXCITATION_CHANNELS, "role": "excitation"},
                {"component": "excitation_electronics_board"},
            ],
            "state": {
                "applied": condition.name,
                "definition": condition.definition,
                "derived_from": CHIP_CHANNELS_PATH,
                "operator_setting": {
                    "mode": operator.mode,
                    "level_s1_s2": _q(operator.level_s1_s2_percent, "%"),
                    "level_s3_s4": _q(operator.level_s3_s4_percent, "%"),
                },
                "operator_setting_restored_after_activity": activity.excitation_restored,
            },
        },
        "sensor": {"uses": [{"component": "sensor"}], "deployment": _deployment(conditions, warn)},
        "conditioning": {"uses": [{"component": "conditioning_electronics_board"}]},
        "synchronous_detection": {
            "uses": [{"component": "signal_generation_chip", "channels": REFERENCE_CHANNELS, "role": "reference"}],
            "state": _synchronous_detection_state(conditions, warn),
        },
        "digitization": {
            "uses": [{"component": "adc"}, {"component": "microcontroller"}],
            "stream": {
                "origin": "started_by_activity" if activity.stream_started_here else "already_running",
                "stopped_after_activity": activity.stream_started_here,
            },
        },
        "positioning": {"uses": [{"component": "motors"}], "state": _positioning_state(activity, warn)},
        "auxiliary_probes": {"uses": [], "notes": "aucune sonde auxiliaire lue par ce balayage"},
    }


def _deployment(conditions: AcquisitionConditionsDTO, warn: Warn) -> Optional[Dict[str, Any]]:
    path = "measurement_chain.sensor.deployment"
    deployment = conditions.sensor_deployment
    if deployment is None:
        warn(path, f"montage du capteur inconnu : {_reason(conditions, 'sensor_deployment')}")
        return None
    if deployment.mounting_id is None:
        warn(f"{path}.id", "aucun montage du capteur enregistré")
    if deployment.rotation_origin != "calibrated":
        warn(f"{path}.rotation_applied.origin", f"rotation non calibrée (origine : {deployment.rotation_origin})")
    elif deployment.calibration_id is None:
        warn(f"{path}.rotation_applied.calibration_id", "entrée de calibration appliquée introuvable dans le registre")
    convention = RotationConvention.standard()  # the only convention the application applies
    return {
        "id": deployment.mounting_id,
        "mounted_at": _iso(deployment.mounted_at),
        "rotation_applied": {
            "theta_x": _q(deployment.theta_x_degrees, "deg"),
            "theta_y": _q(deployment.theta_y_degrees, "deg"),
            "theta_z": _q(deployment.theta_z_degrees, "deg"),
            "convention": {"type": convention.type, "order": convention.order, "direction": convention.direction},
            "origin": deployment.rotation_origin,
            "calibration_id": deployment.calibration_id,
            "applies_to_data": False,
            "notes": "les fichiers de ce balayage sont dans le repère du capteur (non tournés)",
        },
    }


def _synchronous_detection_state(conditions: AcquisitionConditionsDTO, warn: Warn) -> Optional[Dict[str, Any]]:
    path = "measurement_chain.synchronous_detection.state"
    detection, chip = conditions.synchronous_detection, conditions.signal_generation
    if detection is None:
        warn(path, f"état de la détection synchrone inconnu : {_reason(conditions, 'synchronous_detection')}")
        return None
    if detection.compensation_enabled and detection.phase_calibration_id is None:
        warn(f"{path}.phase_calibration_id", "compensation active mais calibration de phase appliquée non identifiée")
    state: Dict[str, Any] = {
        "lock_in_enabled": None,
        "compensation_enabled": detection.compensation_enabled,
        "phase_offset": None,
        "phase_offset_origin": "calibrated" if detection.compensation_enabled else "manual",
        "phase_calibration_id": detection.phase_calibration_id,
        "derived_from": CHIP_CHANNELS_PATH,
    }
    if chip is not None and {"1", "3", "4"} <= set(chip.channels):
        state["lock_in_enabled"] = chip.channels["3"].gain_code > 0 and chip.channels["4"].gain_code > 0
        offset = PhaseAngle.from_register(chip.channels["4"].phase_code).difference_from(
            PhaseAngle.from_register(chip.channels["1"].phase_code)
        )
        state["phase_offset"] = _q(round(offset, 6), "deg")
    return state


def _positioning_state(activity: ThroughputActivityDTO, warn: Warn) -> Dict[str, Any]:
    path = "measurement_chain.positioning.state"
    start, end = activity.bench_position_start, activity.bench_position_end
    if start is None:
        warn(f"{path}.position_at_start", f"position du banc inconnue : {activity.bench_position_unknown_reason or 'raison inconnue'}")
    if start is not None and end is not None and start != end:
        warn(path, "le banc a bougé pendant le balayage (moteurs non réservés par celui-ci)")
    return {
        "frame": "bench",
        "position_at_start": _position(start),
        "position_at_end": _position(end),
        "motors_held_by_activity": False,
    }


def _position(position: Optional[BenchPositionDTO]) -> Optional[Dict[str, Any]]:
    return None if position is None else {"x": _q(position.x_mm, "mm"), "y": _q(position.y_mm, "mm")}


# -- data (PROV wasGeneratedBy, SOSA observedProperty) --------------------------------


def _data(files: Sequence[ExportedFileDTO]) -> Dict[str, Any]:
    listed = [
        {
            "name": f.name,
            "format": f.format,
            "byte_size": _q(f.byte_size, "By"),
            "sha256": f.sha256,
            "was_generated_by": "provenance.activity",
        }
        for f in files
    ]
    listed.append({
        "name": ACQUISITION_PARAMETERS_FILE_NAME,
        "format": "JSON",
        "was_generated_by": "provenance.activity",
        "notes": "ce document ; pas d'empreinte (il devrait se contenir lui-même)",
    })
    return {"files": listed, "columns": {name: dict(meaning) for name, meaning in COLUMNS.items()}}


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
