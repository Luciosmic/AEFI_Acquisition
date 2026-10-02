"""
Acquisition Conditions Reader

See acquisition_conditions_reader_intention.md.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Tuple

from application.shared.acquisition_parameters.acquisition_conditions_dtos import (
    AcquisitionConditionsDTO,
    AdcSettingsDTO,
    AxisMotionSettingsDTO,
    BenchPositionDTO,
    DdsChannelSettingsDTO,
    HostLinkDTO,
    MotorsSettingsDTO,
    MountedComponentDTO,
    SensorDeploymentDTO,
    SignalGenerationSettingsDTO,
    SynchronousDetectionStateDTO,
)
from application.shared.acquisition_parameters.i_acquisition_conditions_port import (
    IAcquisitionConditionsPort,
)
from application.services.motion_control_service.ports.i_motion_port import IMotionPort
from application.services.sensor_calibration_service.dtos.sensor_calibration_dto import ActiveSensorRotationDTO
from domain.calibration.calibration import Calibration
from domain.calibration.repositories.i_hardware_component_repository import IHardwareComponentRepository
from domain.calibration.repositories.i_sensor_calibration_repository import ISensorCalibrationRepository
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import HardwareComponentKind
from domain.shared_kernel.operation_result import OperationResult

logger = logging.getLogger(__name__)

DDS_CHANNELS = (1, 2, 3, 4)
ARCUS_CONFIG = Path(".aefi_acquisition/configs/arcus_default_config.json")
MOTION_CONFIG = Path(".aefi_acquisition/configs/motion_last_config.json")


class AcquisitionConditionsReader(IAcquisitionConditionsPort):
    """Gathers the hardware conditions from where they already live: the
    acquisition snapshot (component catalog + resolved chip configs), the
    controllers' memory, the sensor calibration and synchronous detection
    services (as bound queries), the motors and the serial communicator."""

    def __init__(
        self,
        snapshot_reader,  # AcquisitionSnapshotReader (IAcquisitionSnapshotPort): read() -> dict
        hardware_component_repository: IHardwareComponentRepository,
        sensor_calibration_repository: ISensorCalibrationRepository,
        active_rotation: Callable[[], ActiveSensorRotationDTO],
        compensation_enabled: Callable[[], bool],
        ad9106_memory_state: Callable[[], Mapping[str, Any]],
        oversampling_ratio: Callable[[], int],
        serial_communicator,
        motion_port: IMotionPort,
        hardware_backends: Mapping[str, str],
    ) -> None:
        self._snapshot_reader = snapshot_reader
        self._hardware_components = hardware_component_repository
        self._sensor_calibrations = sensor_calibration_repository
        self._active_rotation = active_rotation
        self._compensation_enabled = compensation_enabled
        self._ad9106_memory_state = ad9106_memory_state
        self._oversampling_ratio = oversampling_ratio
        self._communicator = serial_communicator
        self._motion = motion_port
        self._hardware_backends = dict(hardware_backends)

    # -- IAcquisitionConditionsPort ----------------------------------------------------

    def read_conditions(self) -> AcquisitionConditionsDTO:
        unknown: Dict[str, str] = {}
        snapshot = self._read("components", unknown, self._snapshot_reader.read) or {}
        settings = snapshot.get("hardware_settings") or {}
        conditions = AcquisitionConditionsDTO(
            components=self._read("components", unknown, lambda: _components(snapshot)) or (),
            adc=self._read("adc", unknown, lambda: self._adc(settings.get("ads131a04"))),
            signal_generation=self._read(
                "signal_generation", unknown, lambda: self._signal_generation(settings.get("ad9106"))
            ),
            synchronous_detection=self._read(
                "synchronous_detection", unknown,
                lambda: SynchronousDetectionStateDTO(compensation_enabled=bool(self._compensation_enabled())),
            ),
            sensor_deployment=self._read("sensor_deployment", unknown, self._sensor_deployment),
            motors=self._read("motors", unknown, _motors_settings),
            host_link=self._read("host_link", unknown, self._host_link) or HostLinkDTO(),
            hardware_backends=self._hardware_backends,
            unknown=unknown,
        )
        logger.info(
            "AcquisitionConditionsReader: conditions read (%d components, unknown=%s)",
            len(conditions.components), sorted(unknown),
        )
        return conditions

    def read_bench_position(self) -> OperationResult[BenchPositionDTO, str]:
        try:
            position = self._motion.get_current_position()
        except Exception as error:  # motion adapter: not connected, controller error
            logger.warning("AcquisitionConditionsReader: bench position unknown: %s", error)
            return OperationResult.fail(f"{type(error).__name__}: {error}")
        return OperationResult.ok(BenchPositionDTO(x_mm=float(position.x), y_mm=float(position.y)))

    # -- sections ------------------------------------------------------------------------

    @staticmethod
    def _read(field: str, unknown: Dict[str, str], read: Callable[[], Any]) -> Any:
        """One fact family; any failure makes it unknown, with its reason."""
        try:
            value = read()
        except Exception as error:  # other services / adapters / files: never fail the sweep
            unknown.setdefault(field, f"{type(error).__name__}: {error}")
            logger.warning("AcquisitionConditionsReader: %s unknown: %s", field, error)
            return None
        if value is None:
            unknown.setdefault(field, "non disponible")
        return value

    def _adc(self, resolved: Optional[Mapping[str, Any]]) -> Optional[AdcSettingsDTO]:
        if not resolved:
            raise LookupError("aucune configuration ads131a04 résolue (default + last)")
        oversampling_ratio = int(self._oversampling_ratio())  # controller memory: the value applied
        if oversampling_ratio != int(resolved["oversampling_ratio"]):
            logger.info(
                "AcquisitionConditionsReader: OSR in controller memory (%d) differs from resolved config (%s). "
                "Adopting controller memory.", oversampling_ratio, resolved["oversampling_ratio"],
            )
        channels = resolved.get("channels", {})
        return AdcSettingsDTO(
            oversampling_ratio=oversampling_ratio,
            clkin_divider=int(resolved["clkin_divider"]),
            iclk_divider=int(resolved["iclk_divider"]),
            reference_voltage_v=float(str(resolved["reference_voltage"]).rstrip("V")),
            reference_source=str(resolved["reference_source"]),
            high_resolution=bool(resolved["high_resolution"]),
            negative_charge_pump=bool(resolved["negative_charge_pump"]),
            channel_gains={str(ch): int(c["gain"]) for ch, c in channels.items()},
            channel_enabled={str(ch): bool(c.get("enabled", True)) for ch, c in channels.items()},
        )

    def _signal_generation(self, resolved: Optional[Mapping[str, Any]]) -> SignalGenerationSettingsDTO:
        dds = self._ad9106_memory_state()["DDS"]
        resolved = resolved or {}

        def flag(key: str) -> Optional[bool]:
            return bool(resolved[key]) if key in resolved else None

        return SignalGenerationSettingsDTO(
            frequency_hz=float(dds["Frequence"]),
            channels={
                str(ch): DdsChannelSettingsDTO(
                    gain_code=int(dds["Gain"][ch]),
                    phase_code=int(dds["Phase"][ch]),
                    offset_code=int(dds["Offset"][ch]),
                    constant_code=int(dds["Const"][ch]),
                    mode=str(dds["Mode"][ch]),
                )
                for ch in DDS_CHANNELS
            },
            link_dds1_dds2=flag("link_dds1_dds2"),
            enforce_dds3_dds4_quadrature=flag("enforce_dds3_dds4_quadrature"),
            link_dds3_dds4_gain=flag("link_dds3_dds4_gain"),
        )

    def _sensor_deployment(self) -> SensorDeploymentDTO:
        mounting = Calibration.current_mounting(self._hardware_components.find_selections(HardwareComponentKind.SENSOR))
        rotation = self._active_rotation()
        origin = "trial" if rotation.is_trial else "calibrated" if rotation.is_calibrated else "ideal"
        calibration_id = None
        if origin == "calibrated":
            # The active rotation names its entry only by recorded_at: find it in the registry.
            matching = [
                entry for entry in self._sensor_calibrations.find_all()
                if entry.recorded_at == rotation.recorded_at
                and (mounting is None or entry.sensor_mounting_id == mounting.mounting_id)
            ]
            calibration_id = str(matching[0].entry_id) if len(matching) == 1 else None
        return SensorDeploymentDTO(
            mounting_id=str(mounting.mounting_id) if mounting else None,
            mounted_at=mounting.selected_at if mounting else None,
            theta_x_degrees=rotation.theta_x_degrees,
            theta_y_degrees=rotation.theta_y_degrees,
            theta_z_degrees=rotation.theta_z_degrees,
            rotation_origin=origin,
            calibration_id=calibration_id,
            calibration_recorded_at=rotation.recorded_at,
        )

    def _host_link(self) -> HostLinkDTO:
        port = getattr(self._communicator, "port", None)
        baud_rate = getattr(self._communicator, "baudrate", None)
        return HostLinkDTO(serial_port=port, baud_rate=int(baud_rate) if port and baud_rate else None)


def _motors_settings() -> MotorsSettingsDTO:
    """Arcus profile (the file the Arcus configurator applies and saves) and the
    Motion panel's speed mode / referential."""
    with ARCUS_CONFIG.open(encoding="utf-8") as f:
        arcus = json.load(f)
    motion: Dict[str, Any] = {}
    if MOTION_CONFIG.exists():
        with MOTION_CONFIG.open(encoding="utf-8") as f:
            motion = json.load(f)

    def axis(name: str) -> AxisMotionSettingsDTO:
        return AxisMotionSettingsDTO(
            low_speed_hz=float(arcus[f"{name}_ls"]), high_speed_hz=float(arcus[f"{name}_hs"]),
            acceleration_ms=float(arcus[f"{name}_acc"]), deceleration_ms=float(arcus[f"{name}_dec"]),
        )

    return MotorsSettingsDTO(
        microns_per_step=float(arcus["microns_per_step"]), x=axis("x"), y=axis("y"),
        speed_mode=motion.get("speed_mode"), referential=motion.get("referential_mode"),
    )


def _components(snapshot: Mapping[str, Any]) -> Tuple[MountedComponentDTO, ...]:
    catalog = snapshot.get("hardware_configuration")
    if catalog is None:
        raise LookupError("catalogue des composants absent de l'instantané")
    components = []
    for kind in HardwareComponentKind:
        entry = catalog.get(kind.value)
        if entry is None:
            components.append(MountedComponentDTO(kind=kind.value, name=None))
            continue
        components.append(MountedComponentDTO(
            kind=kind.value,
            name=entry["component_name"],
            entry_id=entry.get("entry_id"),
            recorded_at=datetime.fromisoformat(entry["recorded_at"]) if entry.get("recorded_at") else None,
            characterization=dict(entry.get("characterization", {})),
            units=dict(entry.get("units", {})),
            curve_x_labels={q.key: q.curve_x_label for q in kind.quantities if q.is_curve},
        ))
    return tuple(components)
