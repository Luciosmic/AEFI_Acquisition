"""
Scan Export Service

Responsibility:
- Listen to scan-related domain events and drive an `IExportPort`
  to export step-scan point results (position + averaged value + std dev)
  to an external format (e.g. CSV).

Rationale:
- Keep export orchestration in the Application layer, decoupled from
  UI and infrastructure details.
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime
from typing import Optional, Dict, Any, List

from .dtos.scan_export_dtos import ExportConfigDTO
from .ports.i_scan_export_port import IScanExportPort
from .ports.i_acquisition_snapshot_port import IAcquisitionSnapshotPort
from .ports.i_post_processing_port import IPostProcessingPort
from application._shared.ports.i_async_task_runner import IAsyncTaskRunner

from domain.step_scan.events.scan_started.scan_started import ScanStarted
from domain.step_scan.events.scan_point_acquired.scan_point_acquired import ScanPointAcquired
from domain.step_scan.events.scan_completed.scan_completed import ScanCompleted
from domain.step_scan.events.scan_failed.scan_failed import ScanFailed
from domain.step_scan.events.scan_cancelled.scan_cancelled import ScanCancelled
from domain.step_scan.events.electric_field_scan_point_acquired.electric_field_scan_point_acquired import ElectricFieldScanPointAcquired
from domain.electric_field_probe.electric_field_probe import ElectricFieldProbe
from domain.electric_field_probe.events.electric_field_probe_connection_changed.electric_field_probe_connection_changed import ElectricFieldProbeConnectionChanged
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
        print(f"[ScanExportService] Configured: enabled={config.enabled}, dir='{config.output_directory}', file='{config.filename_base}'")
        logger.debug("ScanExportService configured: %s", config)

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
        except Exception as exc:
            print(f"[ScanExportService] ERROR handling {type(event).__name__}: {exc}")
            logger.error("Error in ScanExportService while handling %s: %s", type(event).__name__, exc)

    def _handle_scan_started(self, event: ScanStarted) -> None:
        print(f"[ScanExportService] Handling ScanStarted. Config present: {self._config is not None}")
        if not self._config or not self._config.enabled:
            print("[ScanExportService] Export disabled or not configured.")
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

        print(f"[ScanExportService] Starting export to dir='{directory}', base='{filename_base}'")
        logger.debug(
            "Starting scan export for scan_id=%s to directory=%s, filename_base=%s",
            event.scan_id,
            directory,
            filename_base,
        )

        acquisition_metadata = self._build_acquisition_metadata(event)
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

    def _handle_scan_finished(self, event: DomainEvent) -> None:
        if not self._export_active:
            return

        logger.debug("Stopping scan export after event: %s", type(event).__name__)
        # Output paths must be read before stop() — both ports clear their
        # path once closed.
        csv_path = self._csv_export_port.get_output_path()
        hdf5_path = self._hdf5_export_port.get_output_path()
        points_written = self._points_written
        try:
            for port in self._active_ports:
                port.stop()
        finally:
            self._export_active = False
            self._active_ports = []

        if points_written == 0:
            # A scan that failed/was cancelled before any point was
            # acquired leaves nothing worth keeping (0-row CSV, near-empty
            # HDF5) — remove the acquisition folder instead of littering
            # the exports directory. stop() already closed the file
            # handles above, so this is safe on Windows.
            for folder in {p.parent for p in (csv_path, hdf5_path) if p is not None}:
                shutil.rmtree(folder, ignore_errors=True)

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
            "measurement_uncertainty_max_volts": cfg.measurement_uncertainty.max_uncertainty_volts,
            "total_points": cfg.total_points(),
            "estimated_duration_s": cfg.estimated_duration_seconds(),
        }

    def _build_acquisition_metadata(self, event: ScanStarted) -> Dict[str, Any]:
        """Bundle every acquisition parameter currently accessible into one
        JSON-ready snapshot (v0, agile — see i_acquisition_snapshot_port.py
        and the ExcitationConfigurationService coupling note in __init__ for
        what's a live getter vs. an on-disk config read)."""
        scan = self._build_metadata(event)
        scan_id = scan.pop("scan_id")

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
            "metadata_schema_version": "0.1-agile",
            "scan_id": scan_id,
            "generated_at": datetime.now().isoformat(),
            "scan": scan,
            "export": {
                "formats": ["CSV", "HDF5"],
                "filename_base": self._config.filename_base,
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


