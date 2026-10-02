"""
Acquisition Parameters v1 — the sections of `acquisition-parameters.json`
(schema 1.0) common to every acquisition: provenance, components, sensor
deployment, synchronous detection, serial link, positions, produced files.

See acquisition_parameters_v1_intention.md. The schema contract is
application/services/scan_export_service/acquisition_parameters/acquisition_parameters_intention.md.
Each export's serializer (scan, time series, throughput sweep) adds only what
its acquisition did: procedure, its measurement chain specifics, its columns.
"""

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from application.shared.acquisition_parameters.acquisition_conditions_dtos import (
    AcquisitionConditionsDTO,
    BenchPositionDTO,
    ExportedFileDTO,
    MountedComponentDTO,
    SignalGenerationSettingsDTO,
    SoftwareProvenanceDTO,
)
from domain.calibration.value_objects.rotation_convention.rotation_convention import RotationConvention
from domain.shared_kernel.excitation.value_objects.phase_angle import PhaseAngle

ACQUISITION_PARAMETERS_FILE_NAME = "acquisition-parameters.json"
SCHEMA = {"name": "aefi-acquisition-parameters", "version": "1.0"}

# Every unit the 1.0 documents write, as UCUM codes (guard tests: nothing else).
# ponytail: UCUM has no fractional exponent — V/√Hz is written V/{sqrt_Hz}.
UCUM_UNITS = frozenset({
    "1", "%", "s", "ms", "h", "Hz", "V", "V/m", "deg", "mm", "By", "Bd",
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
_UCUM_BY_CURVE_X_LABEL = {"n_avg": "{sample}"}

CHIP_CHANNELS_PATH = "components.signal_generation_chip.settings.channels"
# Channels of the AD9106 per function (measurement_chain `uses`).
EXCITATION_CHANNELS = ["1", "2"]
REFERENCE_CHANNELS = ["3", "4"]

Warn = Callable[[str, str], None]


def new_warnings() -> Tuple[List[Dict[str, str]], Warn]:
    """The document's single warnings list, and the function that appends to it."""
    warnings: List[Dict[str, str]] = []

    def warn(path: str, message: str) -> None:
        warnings.append({"path": path, "message": message})

    return warnings, warn


def quantity(value: Any, unit: str) -> Optional[Dict[str, Any]]:
    """Quantity object: the unit travels with the value."""
    return None if value is None else {"value": value, "unit": unit}


def iso(moment: Optional[datetime]) -> Optional[str]:
    """ISO 8601 with offset, local time (naive datetimes are local)."""
    return None if moment is None else moment.astimezone().isoformat(timespec="milliseconds")


def ucum(catalog_unit: str, path: str, warn: Warn) -> str:
    unit = _UCUM_BY_CATALOG_UNIT.get(catalog_unit)
    if unit is None:
        warn(path, f"unité du catalogue « {catalog_unit} » sans équivalent UCUM connu : écrite en annotation")
        return "{" + "".join(c if c.isalnum() else "_" for c in catalog_unit) + "}"
    return unit


def reason(conditions: AcquisitionConditionsDTO, field: str, default: str = "raison inconnue") -> str:
    return conditions.unknown.get(field, default)


# -- provenance (PROV-O) -------------------------------------------------------------


def provenance(
    *,
    activity_id: str,
    kind: str,
    started_at: datetime,
    ended_at: Optional[datetime],
    status: str,
    failure_reason: Optional[str],
    owner: Optional[str],
    held_controls: Sequence[str],
    software: SoftwareProvenanceDTO,
    conditions: AcquisitionConditionsDTO,
    generated_at: datetime,
    warn: Warn,
) -> Dict[str, Any]:
    if ended_at is None:
        warn(
            "provenance.activity.ended_at",
            "acquisition non terminée : document écrit au démarrage — resté ainsi, l'acquisition a été interrompue",
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
            "id": activity_id,
            "kind": kind,
            "started_at": iso(started_at),
            "ended_at": iso(ended_at),
            "status": status,
            "failure_reason": failure_reason,
            "exclusive_control": {"owner": owner, "held": list(held_controls)},
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
        "generated_at": iso(generated_at),
    }


def feature_of_interest(
    *, present: bool, description: Optional[str], notes: Optional[str], warn: Warn, absent_because: str = "",
) -> Dict[str, Any]:
    if present and not description:
        warn("feature_of_interest.description", "objet mesuré non décrit")
    elif not present:
        because = f" ({absent_because})" if absent_because else ""
        warn(
            "feature_of_interest",
            f"aucun objet par construction{because} ; la présence éventuelle d'un objet sur le banc n'est pas saisie",
        )
    return {"present": present, "description": description, "notes": notes}


# -- components (SOSA System) --------------------------------------------------------


def components(conditions: AcquisitionConditionsDTO, warn: Warn, *, state_read: str = None) -> Dict[str, Any]:
    """Every mounted component with its catalog characterization, plus the
    applied settings of the ADC and the AD9106. The caller adds the
    microcontroller settings (`n_avg` is a procedure fact for a sweep).
    `state_read`: when the AD9106 state was read (default: at acquisition start)."""
    blocks: Dict[str, Any] = {mounted.kind: component(mounted, warn) for mounted in conditions.components}
    if not conditions.components:
        warn("components", f"catalogue des composants illisible : {reason(conditions, 'components')}")
    empty = {"component": None, "characterization": None}
    blocks.setdefault("adc", dict(empty))["settings"] = adc_settings(conditions, warn)
    chip_kwargs = {"state_read": state_read} if state_read else {}
    blocks.setdefault("signal_generation_chip", dict(empty))["settings"] = signal_generation_settings(
        conditions.signal_generation, conditions, warn, **chip_kwargs
    )
    blocks.setdefault("microcontroller", dict(empty))
    blocks.setdefault("motors", dict(empty))["settings"] = motors_settings(conditions, warn)
    return blocks


def motors_settings(conditions: AcquisitionConditionsDTO, warn: Warn) -> Optional[Dict[str, Any]]:
    motors = conditions.motors
    if motors is None:
        warn("components.motors.settings", f"réglages moteurs inconnus : {reason(conditions, 'motors')}")
        return None

    def axis(a) -> Dict[str, Any]:
        return {
            "low_speed": quantity(a.low_speed_hz, "Hz"),
            "high_speed": quantity(a.high_speed_hz, "Hz"),
            "acceleration": quantity(a.acceleration_ms, "ms"),
            "deceleration": quantity(a.deceleration_ms, "ms"),
        }

    return {
        "step_size": quantity(motors.microns_per_step, "um/{step}"),
        "x": axis(motors.x),
        "y": axis(motors.y),
        "speed_mode": motors.speed_mode,
        "referential": motors.referential,
    }


def component(mounted: MountedComponentDTO, warn: Warn) -> Dict[str, Any]:
    path = f"components.{mounted.kind}"
    if mounted.name is None:
        warn(f"{path}.component", "aucun composant déclaré monté : configuration incomplète")
        return {"component": None, "characterization": None}
    characterization: Dict[str, Any] = {}
    for key, value in mounted.characterization.items():
        key_path = f"{path}.characterization.{key}"
        unit = ucum(mounted.units.get(key, ""), key_path, warn)
        if value is None:
            characterization[key] = None
            warn(key_path, "non caractérisé")
        elif key in mounted.curve_x_labels:
            characterization[key] = curve(value, mounted.curve_x_labels[key], unit, key_path, warn)
        else:
            characterization[key] = quantity(value, unit)
    return {
        "component": {"name": mounted.name, "id": mounted.entry_id, "recorded_at": iso(mounted.recorded_at)},
        "characterization": characterization,
    }


def curve(points, x_label: str, unit: str, path: str, warn: Warn) -> Dict[str, Any]:
    if x_label not in _UCUM_BY_CURVE_X_LABEL:
        warn(f"{path}.abscissa", f"unité de l'abscisse « {x_label} » inconnue : écrite sans dimension")
    pairs = [tuple(point) for point in points]
    return {
        "abscissa": {"name": x_label, "value": [x for x, _ in pairs], "unit": _UCUM_BY_CURVE_X_LABEL.get(x_label, "1")},
        "ordinate": {"value": [y for _, y in pairs], "unit": unit},
    }


def adc_settings(conditions: AcquisitionConditionsDTO, warn: Warn) -> Optional[Dict[str, Any]]:
    adc = conditions.adc
    if adc is None:
        warn("components.adc.settings", f"réglages ADC inconnus : {reason(conditions, 'adc')}")
        return None
    return {
        "oversampling_ratio": quantity(adc.oversampling_ratio, "1"),
        "clkin_divider": quantity(adc.clkin_divider, "1"),
        "iclk_divider": quantity(adc.iclk_divider, "1"),
        "reference_voltage": quantity(adc.reference_voltage_v, "V"),
        "reference_source": adc.reference_source,
        "high_resolution": adc.high_resolution,
        "negative_charge_pump": adc.negative_charge_pump,
        "channels": {
            channel: {"digital_gain": quantity(gain, "1"), "enabled": adc.channel_enabled.get(channel)}
            for channel, gain in sorted(adc.channel_gains.items(), key=lambda item: int(item[0]))
        },
    }


def signal_generation_settings(
    chip: Optional[SignalGenerationSettingsDTO], conditions: AcquisitionConditionsDTO, warn: Warn,
    state_read: str = "mémoire du contrôleur au démarrage de l'acquisition — pas de relecture des registres",
) -> Optional[Dict[str, Any]]:
    path = "components.signal_generation_chip.settings"
    if chip is None:
        warn(path, f"réglages AD9106 inconnus : {reason(conditions, 'signal_generation')}")
        return None
    for flag in ("link_dds1_dds2", "enforce_dds3_dds4_quadrature", "link_dds3_dds4_gain"):
        if getattr(chip, flag) is None:
            warn(f"{path}.{flag}", "inconnu (configuration AD9106 illisible)")
    return {
        "frequency": quantity(chip.frequency_hz, "Hz"),
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
        "state_read": state_read,
    }


def host_link(
    conditions: AcquisitionConditionsDTO, usb_latency_timer_ms: Optional[float],
    usb_latency_unknown_reason: Optional[str], warn: Warn,
) -> Dict[str, Any]:
    """Serial link host <-> MCU, for components.microcontroller.settings.host_link."""
    path = "components.microcontroller.settings.host_link"
    link = conditions.host_link
    if link.serial_port is None:
        warn(f"{path}.serial_port", f"port série inconnu : {reason(conditions, 'host_link', 'non connecté ou simulé')}")
    if link.baud_rate is None:
        warn(f"{path}.baud_rate", "débit de la liaison série inconnu")
    if usb_latency_timer_ms is None:
        warn(f"{path}.usb_latency_timer", f"latence USB inconnue : {usb_latency_unknown_reason or 'raison inconnue'}")
    return {
        "serial_port": link.serial_port,
        "baud_rate": quantity(link.baud_rate, "Bd"),
        "usb_latency_timer": quantity(usb_latency_timer_ms, "ms"),
        "usb_latency_timer_source": "registre Windows du pilote FTDI (LatencyTimer), appliqué à l'ouverture du port",
    }


# -- measurement chain (SOSA Procedure / Actuation / Observation) --------------------


def excitation_uses():
    return [
        {"component": "signal_generation_chip", "channels": EXCITATION_CHANNELS, "role": "excitation"},
        {"component": "excitation_electronics_board"},
    ]


def synchronous_detection_uses():
    return [{"component": "signal_generation_chip", "channels": REFERENCE_CHANNELS, "role": "reference"}]


def deployment(conditions: AcquisitionConditionsDTO, *, applies_to_data: bool, notes: str, warn: Warn) -> Optional[Dict[str, Any]]:
    path = "measurement_chain.sensor.deployment"
    sensor = conditions.sensor_deployment
    if sensor is None:
        warn(path, f"montage du capteur inconnu : {reason(conditions, 'sensor_deployment')}")
        return None
    if sensor.mounting_id is None:
        warn(f"{path}.id", "aucun montage du capteur enregistré")
    if sensor.rotation_origin != "calibrated":
        warn(f"{path}.rotation_applied.origin", f"rotation non calibrée (origine : {sensor.rotation_origin})")
    elif sensor.calibration_id is None:
        warn(f"{path}.rotation_applied.calibration_id", "entrée de calibration appliquée introuvable dans le registre")
    convention = RotationConvention.standard()  # the only convention the application applies
    return {
        "id": sensor.mounting_id,
        "mounted_at": iso(sensor.mounted_at),
        "rotation_applied": {
            "theta_x": quantity(sensor.theta_x_degrees, "deg"),
            "theta_y": quantity(sensor.theta_y_degrees, "deg"),
            "theta_z": quantity(sensor.theta_z_degrees, "deg"),
            "convention": {"type": convention.type, "order": convention.order, "direction": convention.direction},
            "origin": sensor.rotation_origin,
            "calibration_id": sensor.calibration_id,
            "applies_to_data": applies_to_data,
            "notes": notes,
        },
    }


def synchronous_detection_state(conditions: AcquisitionConditionsDTO, warn: Warn) -> Optional[Dict[str, Any]]:
    path = "measurement_chain.synchronous_detection.state"
    detection, chip = conditions.synchronous_detection, conditions.signal_generation
    if detection is None:
        warn(path, f"état de la détection synchrone inconnu : {reason(conditions, 'synchronous_detection')}")
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
        state["phase_offset"] = quantity(round(offset, 6), "deg")
    return state


def positioning_state(
    start: Optional[BenchPositionDTO], end: Optional[BenchPositionDTO], unknown_reason: Optional[str],
    *, motors_held: bool, warn: Warn,
) -> Dict[str, Any]:
    path = "measurement_chain.positioning.state"
    if start is None:
        warn(f"{path}.position_at_start", f"position du banc inconnue : {unknown_reason or 'raison inconnue'}")
    if not motors_held and start is not None and end is not None and start != end:
        warn(path, "le banc a bougé pendant l'acquisition (moteurs non réservés par celle-ci)")
    return {
        "frame": "bench",
        "position_at_start": position(start),
        "position_at_end": position(end),
        "motors_held_by_activity": motors_held,
    }


def position(bench_position: Optional[BenchPositionDTO]) -> Optional[Dict[str, Any]]:
    if bench_position is None:
        return None
    return {"x": quantity(bench_position.x_mm, "mm"), "y": quantity(bench_position.y_mm, "mm")}


# -- data (PROV wasGeneratedBy, SOSA observedProperty) --------------------------------


def data(
    files: Sequence[ExportedFileDTO], columns: Dict[str, Dict[str, Any]],
    document_name: str = ACQUISITION_PARAMETERS_FILE_NAME,
) -> Dict[str, Any]:
    listed = [
        {
            "name": f.name,
            "format": f.format,
            "byte_size": quantity(f.byte_size, "By"),
            "sha256": f.sha256,
            "was_generated_by": "provenance.activity",
        }
        for f in files
    ]
    listed.append({
        "name": document_name,
        "format": "JSON",
        "was_generated_by": "provenance.activity",
        "notes": "ce document ; pas d'empreinte (il devrait se contenir lui-même)",
    })
    return {"files": listed, "columns": {name: dict(meaning) for name, meaning in columns.items()}}
