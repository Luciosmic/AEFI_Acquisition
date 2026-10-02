"""
Scan Export Service

Responsibility:
- Listen to scan-related domain events and drive an `IExportPort`
  to export step-scan point results (position + averaged value + std dev)
  to an external format (e.g. CSV).
- Export a continuous AEFI reading as a time series (one CSV row per
  sample, vs time since the first sample), when armed from the UI.

Rationale:
- Keep export orchestration in the Application layer, decoupled from
  UI and infrastructure details.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import replace
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from .dtos.scan_export_dtos import ExportConfigDTO
from .ports.i_scan_export_port import IScanExportPort
from .dtos.scan_acquisition_parameters_dtos import (
    STEP_SCAN,
    TIME_SERIES,
    ElectricFieldProbeDTO,
    ExcitationStateDTO,
    ScanAcquisitionParametersDTO,
    ScanActivityDTO,
    StepScanProcedureDTO,
)
from application.shared.acquisition_parameters.acquisition_conditions_dtos import (
    AcquisitionConditionsDTO,
    SoftwareProvenanceDTO,
)
from application.shared.acquisition_parameters.i_acquisition_conditions_port import IAcquisitionConditionsPort
from application.shared.acquisition_parameters.i_software_provenance_port import ISoftwareProvenancePort
from application.shared.acquisition_parameters.i_usb_latency_timer_port import IUsbLatencyTimerPort
from .ports.i_post_processing_port import IPostProcessingPort
from application.shared.ports.i_async_task_runner import IAsyncTaskRunner

from domain.step_scan.events.scan_started.scan_started import ScanStarted
from domain.step_scan.value_objects.line_scan_config.line_scan_config import LineScanConfig
from domain.step_scan.events.scan_point_acquired.scan_point_acquired import ScanPointAcquired
from domain.step_scan.events.scan_completed.scan_completed import ScanCompleted
from domain.step_scan.events.scan_failed.scan_failed import ScanFailed
from domain.step_scan.events.scan_cancelled.scan_cancelled import ScanCancelled
from domain.step_scan.events.electric_field_scan_point_acquired.electric_field_scan_point_acquired import ElectricFieldScanPointAcquired
from domain.electric_field_probe.electric_field_probe import ElectricFieldProbe
from domain.electric_field_probe.events.electric_field_probe_connection_changed.electric_field_probe_connection_changed import ElectricFieldProbeConnectionChanged
from domain.shared_kernel.events.aefi_voltage_reading_started.aefi_voltage_reading_started import AefiVoltageReadingStarted
from domain.shared_kernel.events.aefi_voltage_sample_acquired.aefi_voltage_sample_acquired import AefiVoltageSampleAcquired
from domain.shared_kernel.events.aefi_voltage_reading_stopped.aefi_voltage_reading_stopped import AefiVoltageReadingStopped
from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from application.services.excitation_configuration_service.excitation_configuration_service import ExcitationConfigurationService


logger = logging.getLogger(__name__)


class ScanExportService:
    """
    Application service responsible for export of scan point results.

    Notes:
    - Works in an event-driven fashion: subscribes to `ScanStarted`,
      `ScanPointAcquired`, `ScanCompleted`, `ScanFailed`, `ScanCancelled`.
    - Also handles `ElectricFieldScanPointAcquired` events for electric field probe data.
    - Uses `ExportConfigDTO` to know whether export is enabled and
      where to write files.
    """

    def __init__(
        self,
        event_bus: IDomainEventBus,
        csv_export_port: IScanExportPort,
        hdf5_export_port: IScanExportPort,
        excitation_service: ExcitationConfigurationService,
        conditions_port: Optional[IAcquisitionConditionsPort] = None,
        post_processing_port: Optional[IPostProcessingPort] = None,
        task_runner: Optional[IAsyncTaskRunner] = None,
        software_provenance_port: Optional[ISoftwareProvenancePort] = None,
        usb_latency_timer_port: Optional[IUsbLatencyTimerPort] = None,
    ) -> None:
        """`conditions_port`, `software_provenance_port`, `usb_latency_timer_port`:
        the facts of the acquisition-parameters document (schema 1.0). Absent,
        the document still gets written and declares them unknown."""
        self._event_bus = event_bus
        self._csv_export_port = csv_export_port
        self._hdf5_export_port = hdf5_export_port
        # ponytail: direct Application-Service-to-Application-Service call,
        # only to read current excitation params at scan start — no
        # ExcitationChanged domain event exists yet to passively cache
        # instead (unlike the probe, see _handle_probe_connection_changed).
        # Replace with an event subscription once that event exists.
        self._excitation_service = excitation_service
        self._conditions_port = conditions_port
        self._software_provenance_port = software_provenance_port
        self._usb_latency_timer_port = usb_latency_timer_port
        # Facts of the open export's acquisition-parameters document; the
        # final write adds the outcome (see _close_export).
        self._parameters: Optional[ScanAcquisitionParametersDTO] = None
        self._post_processing_port = post_processing_port
        self._task_runner = task_runner
        self._active_ports: List[IScanExportPort] = []
        # Events come from several threads (ADC worker, motion worker, scan
        # loop): the recorder must never see a port that is not open yet, or
        # write into one being closed by another thread.
        self._events_lock = threading.RLock()

        self._config: Optional[ExportConfigDTO] = None
        self._export_active: bool = False  # True between ScanStarted and completion/failure/cancel
        self._points_written: int = 0  # reset per scan — see _handle_scan_finished cleanup
        self._field_export_active: bool = False  # True if electric field export is configured
        self._field_probe_info: Optional[Dict[str, Any]] = None
        self._field_n_components: int = 0
        self._last_known_probe: Optional[ElectricFieldProbe] = None
        # Continuous reading export: armed by configure_time_series_export,
        # consumed by the next AefiVoltageReadingStarted. Arming is explicit
        # because scans also start the continuous ADC worker — those readings
        # must not be exported as time series.
        self._time_series_config: Optional[ExportConfigDTO] = None
        self._time_series_active: bool = False
        self._time_series_t0: Optional[datetime] = None

        # Subscribe to scan events
        self._event_bus.subscribe("scanstarted", self._on_event)
        self._event_bus.subscribe("scanpointacquired", self._on_event)
        self._event_bus.subscribe("scancompleted", self._on_event)
        self._event_bus.subscribe("scanfailed", self._on_event)
        self._event_bus.subscribe("scancancelled", self._on_event)
        # Subscribe to electric field scan events
        self._event_bus.subscribe("electricfieldscanpointacquired", self._on_event)
        # Passively cache the last-connected probe's identity — avoids a
        # constructor dependency on ElectricFieldProbeService.
        self._event_bus.subscribe("electricfieldprobeconnectionchanged", self._on_event)
        # Continuous reading (time-series export)
        self._event_bus.subscribe("aefivoltagereadingstarted", self._on_event)
        self._event_bus.subscribe("aefivoltagesampleacquired", self._on_event)
        self._event_bus.subscribe("aefivoltagereadingstopped", self._on_event)
        # Per-scan event store: every event published while the export is open.
        self._event_bus.subscribe("*", self._record_event)

    # ------------------------------------------------------------------ #
    # Configuration API (called from UI / presenter)
    # ------------------------------------------------------------------ #

    def configure_export(self, config: ExportConfigDTO) -> None:
        """
        Configure export behaviour.

        - If `config.enabled` is False, export is disabled and no files
          will be produced.
        - When enabled, the actual file is only created when a scan
          starts (on `ScanStarted` event).
        """
        self._config = config
        logger.info(
            "Command: configure export. enabled=%s, dir=%s, file=%s",
            config.enabled, config.output_directory, config.filename_base,
        )
        logger.debug("ScanExportService configured: %s", config)

    def configure_time_series_export(self, config: ExportConfigDTO) -> None:
        """Arm (enabled=True) or disarm the export of the next continuous
        reading. Call right before starting the reading: the arming is
        consumed by the next `AefiVoltageReadingStarted`."""
        self._time_series_config = config if config.enabled else None
        logger.info(
            "Command: configure time-series export. enabled=%s, dir=%s, file=%s",
            config.enabled, config.output_directory, config.filename_base,
        )

    # ------------------------------------------------------------------ #
    # Event handling
    # ------------------------------------------------------------------ #

    def _on_event(self, event: DomainEvent) -> None:
        """Central handler for subscribed domain events."""
        try:
            # print(f"[ScanExportService] Received event: {type(event).__name__}")
            if isinstance(event, ScanStarted):
                self._handle_scan_started(event)
            elif isinstance(event, ScanPointAcquired):
                self._handle_scan_point_acquired(event)
            elif isinstance(event, ElectricFieldScanPointAcquired):
                self._handle_electric_field_scan_point_acquired(event)
            elif isinstance(event, (ScanCompleted, ScanFailed, ScanCancelled)):
                self._handle_scan_finished(event)
            elif isinstance(event, ElectricFieldProbeConnectionChanged):
                self._handle_probe_connection_changed(event)
            elif isinstance(event, AefiVoltageReadingStarted):
                self._handle_reading_started(event)
            elif isinstance(event, AefiVoltageSampleAcquired):
                self._handle_voltage_sample_acquired(event)
            elif isinstance(event, AefiVoltageReadingStopped):
                self._handle_reading_stopped(event)
        except Exception as exc:
            logger.exception("Error handling %s: %s", type(event).__name__, exc)

    def _record_event(self, event: DomainEvent) -> None:
        """Forward every event published during the scan — not only the
        scan_id-tagged ones: motion, excitation, probe events are the context
        needed to replay what happened during the acquisition.

        Relies on the bus dispatching "*" subscribers after typed ones: the
        export is already open when ScanStarted reaches here, and already
        closed for the finishing event (written by _close_export).
        `_active_ports` only lists open ports: filled once they are started,
        emptied before they are closed — an event from another thread landing
        while a scan export opens or closes is simply not recorded."""
        with self._events_lock:
            for port in self._active_ports:
                port.write_event(event)

    def _handle_scan_started(self, event: ScanStarted) -> None:
        logger.info("Handling ScanStarted. scan_id=%s, config present: %s", event.scan_id, self._config is not None)
        # The scan owns the ADC worker and the export ports from here on.
        self._time_series_config = None
        if self._time_series_active:
            logger.info("Scan started during a time-series export: closing it. scan_id=%s", event.scan_id)
            self._close_export(event)
        if not self._config or not self._config.enabled:
            logger.info("Export disabled or not configured. Doing nothing.")
            self._export_active = False
            self._field_export_active = False
            return

        # Every scan is exported to both formats simultaneously.
        ports = [self._csv_export_port, self._hdf5_export_port]

        directory = self._config.output_directory
        # Scan name only — each export port builds its own acquisition folder
        # and per-device filenames (timestamp_<stepScan|flyScan>_<device>_<name>) from it.
        filename_base = self._config.filename_base
        # Shared across both ports so CSV and HDF5 land in the same
        # acquisition folder (the post-processing trigger needs both files
        # side by side — see _handle_scan_finished).
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

        metadata = self._build_metadata(event)

        logger.info("Starting export to dir=%s, base=%s", directory, filename_base)
        logger.debug(
            "Starting scan export for scan_id=%s to directory=%s, filename_base=%s",
            event.scan_id,
            directory,
            filename_base,
        )

        parameters = self._start_parameters(
            str(event.scan_id), STEP_SCAN, self._config, self._step_scan_procedure(event)
        )
        # Folder/file tag: a fly scan is an exploration map, not a measurement —
        # its files must not be mistaken for a step scan's.
        acquisition_kind = "flyScan" if getattr(event.config, "fly_scan", False) else "stepScan"
        for port in ports:
            port.configure(directory, filename_base, metadata, timestamp=timestamp, acquisition_kind=acquisition_kind)
            port.start()
            port.write_acquisition_parameters(parameters)
        with self._events_lock:  # visible to the event recorder only once open
            self._active_ports = ports
        self._export_active = True
        self._points_written = 0
        # Reset per-scan field-export state — must not leak into a new scan
        # (would otherwise skip re-calling configure_field_data below).
        self._field_n_components = 0

        # Field export rides on every active port that supports it — field
        # data is configured lazily on the first electric field point (see
        # _handle_electric_field_scan_point_acquired), once the probe's
        # component count is known from the actual event.
        if any(hasattr(port, 'configure_field_data') for port in self._active_ports):
            self._field_export_active = True

    def _handle_scan_point_acquired(self, event: ScanPointAcquired) -> None:
        if not self._export_active:
            return

        data = self._flatten_point(event)
        for port in self._active_ports:
            port.write_point(data)
        self._points_written += 1

    def _handle_electric_field_scan_point_acquired(self, event: ElectricFieldScanPointAcquired) -> None:
        """Handle electric field scan point acquired events."""
        if not self._export_active or not self._field_export_active:
            return

        # Configure field data on first point if not already configured for this scan
        if self._field_n_components == 0:
            n_components = len(event.field_measurement.components)
            probe = self._last_known_probe
            probe_info = {
                "probe_label": self._probe_label(probe) if probe is not None else "field_probe",
                "n_components": n_components,
                "axis_labels": tuple(a.lower() for a in probe.axis_labels) if probe is not None else None,
            }
            for port in self._active_ports:
                if hasattr(port, 'configure_field_data'):
                    port.configure_field_data(n_components, probe_info)
            self._field_n_components = n_components

        # Flatten the electric field point
        data = self._flatten_electric_field_point(event)

        # Write to every active port that supports field data
        for port in self._active_ports:
            if hasattr(port, 'write_field_point'):
                port.write_field_point(data)

    def _handle_probe_connection_changed(self, event: ElectricFieldProbeConnectionChanged) -> None:
        """Cache the connected probe's identity for the next scan's metadata JSON."""
        self._last_known_probe = event.probe if event.connected else None

    def _handle_reading_started(self, event: AefiVoltageReadingStarted) -> None:
        config, self._time_series_config = self._time_series_config, None
        if config is None:
            logger.info("Reading started, time-series export not armed. Doing nothing. acquisition_id=%s", event.acquisition_id)
            return
        if self._export_active:
            logger.info("Reading started during a scan export: time-series export skipped. acquisition_id=%s", event.acquisition_id)
            return

        logger.info(
            "Starting time-series export. acquisition_id=%s, dir=%s, base=%s",
            event.acquisition_id, config.output_directory, config.filename_base,
        )
        # CSV only: the HDF5 layout is a position grid, meaningless vs time.
        port = self._csv_export_port
        port.configure(
            config.output_directory, config.filename_base,
            {"acquisition_id": str(event.acquisition_id)},
            acquisition_kind="timeSeries",
        )
        port.start()
        port.write_acquisition_parameters(self._start_parameters(str(event.acquisition_id), TIME_SERIES, config))
        with self._events_lock:  # visible to the event recorder only once open
            self._active_ports = [port]
        self._time_series_active = True
        self._time_series_t0 = None
        self._points_written = 0

    def _handle_voltage_sample_acquired(self, event: AefiVoltageSampleAcquired) -> None:
        if not self._time_series_active:
            return
        m = event.sample
        if self._time_series_t0 is None:
            self._time_series_t0 = m.timestamp
        self._csv_export_port.write_point({
            "sample_index": event.sample_index,
            "t_s": (m.timestamp - self._time_series_t0).total_seconds(),
            "timestamp": m.timestamp.astimezone().isoformat(),  # ISO 8601 with offset
            "voltage_x_in_phase": m.voltage_x_in_phase,
            "voltage_x_quadrature": m.voltage_x_quadrature,
            "voltage_y_in_phase": m.voltage_y_in_phase,
            "voltage_y_quadrature": m.voltage_y_quadrature,
            "voltage_z_in_phase": m.voltage_z_in_phase,
            "voltage_z_quadrature": m.voltage_z_quadrature,
        })
        self._points_written += 1

    def _handle_reading_stopped(self, event: AefiVoltageReadingStopped) -> None:
        if not self._time_series_active:
            return
        logger.info(
            "Time-series export closed. acquisition_id=%s, samples=%d",
            event.acquisition_id, self._points_written,
        )
        self._close_export(event)

    def _close_export(self, event: DomainEvent) -> List[Optional[Path]]:
        """Write the finishing event, close every active port, and drop the
        acquisition folder if nothing was written. Returns each active port's
        output path, in `_active_ports` order."""
        # Hidden from the event recorder before closing: an event from another
        # thread can no longer reach a port being stopped.
        with self._events_lock:
            ports, self._active_ports = self._active_ports, []
        # Read before stop() — ports clear their path once closed.
        paths = [port.get_output_path() for port in ports]
        finished = self._finish_parameters(event)
        try:
            for port in ports:
                port.write_event(event)  # last event of the export, before its file closes
                port.stop()
            # Once every file is closed: the final document lists and hashes them.
            if finished is not None:
                for port in ports:
                    port.write_acquisition_parameters(finished)
        finally:
            self._export_active = False
            self._time_series_active = False
            self._active_ports = []
            self._parameters = None

        if self._points_written == 0:
            # A scan/reading that ended before any point leaves nothing worth
            # keeping (0-row CSV, near-empty HDF5) — remove the acquisition
            # folder instead of littering the exports directory. stop()
            # already closed the file handles, so this is safe on Windows.
            logger.info("No points written; removing empty acquisition folder(s)")
            for folder in {p.parent for p in paths if p is not None}:
                shutil.rmtree(folder, ignore_errors=True)
        return paths

    def _handle_scan_finished(self, event: DomainEvent) -> None:
        if not self._export_active:
            return

        logger.debug("Stopping scan export after event: %s", type(event).__name__)
        csv_path, hdf5_path = self._close_export(event)  # scan ports are [csv, hdf5]

        if (
            isinstance(event, ScanCompleted)
            and self._post_processing_port is not None
            and self._task_runner is not None
            and csv_path is not None
            and hdf5_path is not None
        ):
            # Fire-and-forget: this service's promise is "exported, and
            # post-processing was triggered" — the pipeline is a downstream
            # consumer of the export, not something this service waits on.
            post_processing_port = self._post_processing_port
            self._task_runner.submit(lambda: post_processing_port.run(csv_path, hdf5_path))

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _probe_label(probe: ElectricFieldProbe) -> str:
        """`Narda` + `EP-601` -> `narda-ep601`, used as the sidecar file's
        device tag — derived from the actually-connected probe rather than
        hardcoded, so a second probe model doesn't need a code change here."""
        return f"{probe.brand}-{probe.model.replace('-', '')}".lower()

    def _build_metadata(self, event: ScanStarted) -> Dict[str, Any]:
        """Extract basic metadata from the scan configuration."""
        cfg = event.config
        if isinstance(cfg, LineScanConfig):
            start, end = cfg.endpoints()
            return {
                "scan_id": str(event.scan_id),
                "scan_kind": "line",
                "center_x": cfg.center.x,
                "center_y": cfg.center.y,
                "length_mm": cfg.length_mm,
                "theta_deg": cfg.theta_deg,
                "start_x": start.x,
                "start_y": start.y,
                "end_x": end.x,
                "end_y": end.y,
                "stabilization_delay_ms": cfg.stabilization_delay_ms,
                "averaging_per_position": cfg.averaging_per_position,
                "total_points": cfg.total_points(),
            }

        zone = cfg.scan_zone

        return {
            "scan_id": str(event.scan_id),
            "pattern": cfg.scan_pattern.name,
            "scan_axis": cfg.scan_axis.name,
            # True = exploration map (positions interpolated at constant
            # speed, no averaging) — not to be read as a measurement.
            "fly_scan": cfg.fly_scan,
            "x_min": zone.x_min,
            "x_max": zone.x_max,
            "x_nb_points": cfg.x_nb_points,
            "y_min": zone.y_min,
            "y_max": zone.y_max,
            "y_nb_points": cfg.y_nb_points,
            "stabilization_delay_ms": cfg.stabilization_delay_ms,
            "averaging_per_position": cfg.averaging_per_position,
            "total_points": cfg.total_points(),
            "estimated_duration_s": cfg.estimated_duration_seconds(),
        }

    # -- acquisition-parameters document (facts only; the port writes schema 1.0) --

    @staticmethod
    def _step_scan_procedure(event: ScanStarted) -> StepScanProcedureDTO:
        cfg = event.config
        zone = cfg.scan_zone
        return StepScanProcedureDTO(
            x_min_mm=zone.x_min, x_max_mm=zone.x_max, y_min_mm=zone.y_min, y_max_mm=zone.y_max,
            x_nb_points=cfg.x_nb_points, y_nb_points=cfg.y_nb_points, total_points=cfg.total_points(),
            pattern=cfg.scan_pattern.name, fast_axis=cfg.scan_axis.name,
            stabilization_delay_ms=cfg.stabilization_delay_ms, averaging_per_position=cfg.averaging_per_position,
            measurement_uncertainty_v=cfg.measurement_uncertainty.max_uncertainty_volts,
            differential_mode=cfg.differential_mode, differential_settle_delay_ms=cfg.differential_settle_delay_ms,
            estimated_duration_s=cfg.estimated_duration_seconds(),
        )

    def _start_parameters(
        self, activity_id: str, kind: str, config: ExportConfigDTO, procedure: Optional[StepScanProcedureDTO] = None
    ) -> ScanAcquisitionParametersDTO:
        """Gather the facts at acquisition start; kept to add the outcome at the end."""
        conditions = (
            self._conditions_port.read_conditions() if self._conditions_port is not None
            else AcquisitionConditionsDTO(unknown={"components": "lecteur de conditions non câblé"})
        )
        software = (
            self._software_provenance_port.read() if self._software_provenance_port is not None
            else SoftwareProvenanceDTO(name="AEFI Acquisition", unknown_reason="lecteur de provenance non câblé")
        )
        position, position_reason = self._bench_position()
        latency, latency_reason = self._usb_latency(conditions)
        excitation = self._excitation_service.get_current_parameters()
        owner = self._excitation_service.get_controller()
        probe = self._last_known_probe
        activity = ScanActivityDTO(
            activity_id=activity_id,
            kind=kind,
            started_at=datetime.now().astimezone(),
            status="running",
            excitation=ExcitationStateDTO(
                mode=excitation.mode.name,
                level_s1_s2_percent=excitation.level_s1_s2.value,
                level_s3_s4_percent=excitation.level_s3_s4.value,
            ),
            owner=owner,
            held_controls=("excitation",) if owner else (),
            procedure=procedure,
            measured_object=config.measured_object.strip() or None,
            operator_id=config.operator_id or None,
            operator=config.operator.strip() or None,
            probe=ElectricFieldProbeDTO(
                brand=probe.brand, model=probe.model, serial_number=probe.serial_number,
                axis_labels=tuple(probe.axis_labels), battery_voltage_v=probe.battery_voltage_v,
                battery_percentage=probe.battery_percentage, battery_remaining_hours=probe.battery_remaining_hours,
            ) if probe is not None else None,
            bench_position_start=position,
            bench_position_unknown_reason=position_reason,
            usb_latency_timer_ms=latency,
            usb_latency_unknown_reason=latency_reason,
        )
        self._parameters = ScanAcquisitionParametersDTO(activity=activity, conditions=conditions, software=software)
        return self._parameters

    def _finish_parameters(self, event: DomainEvent) -> Optional[ScanAcquisitionParametersDTO]:
        if self._parameters is None:
            return None
        if isinstance(event, ScanFailed):
            status, reason = "failed", event.reason
        elif isinstance(event, ScanCancelled):
            status, reason = "cancelled", None
        elif isinstance(event, ScanStarted):  # a scan closed this time series
            status, reason = "cancelled", "interrompue par le démarrage d'un scan"
        else:  # ScanCompleted, AefiVoltageReadingStopped (stopped by the operator)
            status, reason = "completed", None
        position, position_reason = self._bench_position()
        activity = replace(
            self._parameters.activity,
            ended_at=datetime.now().astimezone(), status=status, failure_reason=reason,
            records_written=self._points_written, bench_position_end=position,
            bench_position_unknown_reason=self._parameters.activity.bench_position_unknown_reason or position_reason,
        )
        return replace(self._parameters, activity=activity)

    def _bench_position(self):
        if self._conditions_port is None:
            return None, "lecteur de conditions non câblé"
        result = self._conditions_port.read_bench_position()
        return (result.value, None) if result.is_success else (None, result.error)

    def _usb_latency(self, conditions: AcquisitionConditionsDTO):
        if self._usb_latency_timer_port is None:
            return None, "lecteur de latence USB non câblé"
        serial_port = conditions.host_link.serial_port
        if serial_port is None:
            return None, "port série inconnu (non connecté ou simulé)"
        result = self._usb_latency_timer_port.read_latency_timer_ms(serial_port)
        return (result.value, None) if result.is_success else (None, result.error)

    def _flatten_point(self, event: ScanPointAcquired) -> Dict[str, Any]:
        """
        Flatten a `ScanPointAcquired` event into a dict suitable for CSV.

        Includes:
        - scan_id, point_index
        - x, y
        - mean voltages for each component
        - standard deviations for each component (if available)
        """
        pos = event.position
        m = event.measurement
        b = event.baseline_measurement  # None unless the scan ran in differential mode

        return {
            "scan_id": str(event.scan_id),
            "point_index": event.point_index,
            "x": pos.x,
            "y": pos.y,
            # Mean voltages
            "voltage_x_in_phase": m.voltage_x_in_phase,
            "voltage_x_quadrature": m.voltage_x_quadrature,
            "voltage_y_in_phase": m.voltage_y_in_phase,
            "voltage_y_quadrature": m.voltage_y_quadrature,
            "voltage_z_in_phase": m.voltage_z_in_phase,
            "voltage_z_quadrature": m.voltage_z_quadrature,
            # Standard deviations (may be None if not provided)
            "std_dev_x_in_phase": getattr(m, "std_dev_x_in_phase", None),
            "std_dev_x_quadrature": getattr(m, "std_dev_x_quadrature", None),
            "std_dev_y_in_phase": getattr(m, "std_dev_y_in_phase", None),
            "std_dev_y_quadrature": getattr(m, "std_dev_y_quadrature", None),
            "std_dev_z_in_phase": getattr(m, "std_dev_z_in_phase", None),
            "std_dev_z_quadrature": getattr(m, "std_dev_z_quadrature", None),
            # Baseline (excitation muted) — empty/None columns when not differential
            "baseline_voltage_x_in_phase": b.voltage_x_in_phase if b else None,
            "baseline_voltage_x_quadrature": b.voltage_x_quadrature if b else None,
            "baseline_voltage_y_in_phase": b.voltage_y_in_phase if b else None,
            "baseline_voltage_y_quadrature": b.voltage_y_quadrature if b else None,
            "baseline_voltage_z_in_phase": b.voltage_z_in_phase if b else None,
            "baseline_voltage_z_quadrature": b.voltage_z_quadrature if b else None,
        }

    def _flatten_electric_field_point(self, event: ElectricFieldScanPointAcquired) -> Dict[str, Any]:
        """
        Flatten an `ElectricFieldScanPointAcquired` event into a dict for export.

        Includes:
        - scan_id, point_index
        - x, y
        - field components
        - field standard deviations (if available)
        """
        pos = event.position
        fm = event.field_measurement
        bfm = event.baseline_field_measurement  # None unless the scan ran in differential mode

        return {
            "scan_id": str(event.scan_id),
            "point_index": event.point_index,
            "x": pos.x,
            "y": pos.y,
            # Field measurement components
            "field_components": fm.components,
            # Standard deviations (may be None if not provided)
            "field_std_dev_components": fm.std_dev_components,
            # Baseline (excitation muted) — empty/None columns when not differential
            "baseline_field_components": bfm.components if bfm else None,
            "baseline_field_std_dev_components": bfm.std_dev_components if bfm else None,
        }


