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
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from .dtos.scan_export_dtos import ExportConfigDTO
from .ports.i_scan_export_port import IScanExportPort
from .ports.i_acquisition_snapshot_port import IAcquisitionSnapshotPort
from .ports.i_post_processing_port import IPostProcessingPort
from application.shared.ports.i_async_task_runner import IAsyncTaskRunner

from domain.step_scan.events.scan_started.scan_started import ScanStarted
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

# Unit of every exported column (and of the position bounds in the metadata
# "scan" section). Written to the acquisition-parameters JSON rather than the
# CSV headers: aefi_post_processor_module reads the columns by name.
EXPORT_UNITS: Dict[str, str] = {
    "x": "mm",
    "y": "mm",
    "x_min": "mm",
    "x_max": "mm",
    "y_min": "mm",
    "y_max": "mm",
    "t_s": "s",
    "timestamp": "ISO 8601, local time",
    "voltage_*": "V",
    "std_dev_*": "V",
    "baseline_voltage_*": "V",
    "field_*": "V/m",
    "baseline_field_*": "V/m",
}


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
        acquisition_snapshot_port: IAcquisitionSnapshotPort,
        post_processing_port: Optional[IPostProcessingPort] = None,
        task_runner: Optional[IAsyncTaskRunner] = None,
    ) -> None:
        self._event_bus = event_bus
        self._csv_export_port = csv_export_port
        self._hdf5_export_port = hdf5_export_port
        # ponytail: direct Application-Service-to-Application-Service call,
        # only to read current excitation params at scan start — no
        # ExcitationChanged domain event exists yet to passively cache
        # instead (unlike the probe, see _handle_probe_connection_changed).
        # Replace with an event subscription once that event exists.
        self._excitation_service = excitation_service
        self._acquisition_snapshot_port = acquisition_snapshot_port
        self._post_processing_port = post_processing_port
        self._task_runner = task_runner
        self._active_ports: List[IScanExportPort] = []

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
        `_active_ports` is empty whenever no export is open."""
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
        self._active_ports = [self._csv_export_port, self._hdf5_export_port]

        directory = self._config.output_directory
        # Scan name only — each export port builds its own acquisition folder
        # and per-device filenames (timestamp_stepScan_<device>_<name>) from it.
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

        scan_section = dict(metadata)
        acquisition_metadata = self._build_acquisition_metadata(
            {"scan_id": scan_section.pop("scan_id"), "scan": scan_section},
            formats=["CSV", "HDF5"],
            filename_base=filename_base,
        )
        for port in self._active_ports:
            port.configure(directory, filename_base, metadata, timestamp=timestamp)
            port.start()
            port.write_metadata(acquisition_metadata)
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
        port.write_metadata(self._build_acquisition_metadata(
            {"acquisition_id": str(event.acquisition_id), "acquisition_kind": "timeSeries"},
            formats=["CSV"],
            filename_base=config.filename_base,
        ))
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
            "timestamp": m.timestamp.isoformat(),
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
        # Read before stop() — ports clear their path once closed.
        paths = [port.get_output_path() for port in self._active_ports]
        try:
            for port in self._active_ports:
                port.write_event(event)  # last event of the export, before its file closes
                port.stop()
        finally:
            self._export_active = False
            self._time_series_active = False
            self._active_ports = []

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
        zone = cfg.scan_zone

        return {
            "scan_id": str(event.scan_id),
            "pattern": cfg.scan_pattern.name,
            "scan_axis": cfg.scan_axis.name,
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

    def _build_acquisition_metadata(
        self, header: Dict[str, Any], formats: List[str], filename_base: str
    ) -> Dict[str, Any]:
        """Bundle every acquisition parameter currently accessible into one
        JSON-ready snapshot (v0, agile — see i_acquisition_snapshot_port.py
        and the ExcitationConfigurationService coupling note in __init__ for
        what's a live getter vs. an on-disk config read).

        `header`: the acquisition's own identity/parameters — `scan_id` +
        `scan` section for a step scan, `acquisition_id` for a time series."""
        excitation_params = self._excitation_service.get_current_parameters()

        probe = None
        if self._last_known_probe is not None:
            p = self._last_known_probe
            probe = {
                "brand": p.brand,
                "model": p.model,
                "serial_number": p.serial_number,
                "axis_labels": list(p.axis_labels),
                "battery_voltage_v": p.battery_voltage_v,
                "battery_percentage": p.battery_percentage,
                "battery_remaining_hours": p.battery_remaining_hours,
            }

        metadata = {
            "metadata_schema_version": "0.2-agile",
            **header,
            "generated_at": datetime.now().isoformat(),
            "export": {
                "formats": formats,
                "filename_base": filename_base,
                "units": EXPORT_UNITS,
            },
            "excitation": {
                "mode": excitation_params.mode.name,
                "level_s1_s2_percent": excitation_params.level_s1_s2.value,
                "level_s3_s4_percent": excitation_params.level_s3_s4.value,
                "frequency_hz": excitation_params.frequency,
            },
            "electric_field_probe": probe,
        }
        metadata.update(self._acquisition_snapshot_port.read())
        return metadata

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


