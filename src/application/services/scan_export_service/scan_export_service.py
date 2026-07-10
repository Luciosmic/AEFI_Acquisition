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
from typing import Optional, Dict, Any

from .dtos.scan_export_dtos import ExportConfigDTO
from .ports.i_scan_export_port import IScanExportPort

from domain.step_scan.events.scan_started.scan_started import ScanStarted
from domain.step_scan.events.scan_point_acquired.scan_point_acquired import ScanPointAcquired
from domain.step_scan.events.scan_completed.scan_completed import ScanCompleted
from domain.step_scan.events.scan_failed.scan_failed import ScanFailed
from domain.step_scan.events.scan_cancelled.scan_cancelled import ScanCancelled
from domain.step_scan.events.electric_field_scan_point_acquired.electric_field_scan_point_acquired import ElectricFieldScanPointAcquired
from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus


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
    ) -> None:
        self._event_bus = event_bus
        self._csv_export_port = csv_export_port
        self._hdf5_export_port = hdf5_export_port
        self._active_port: Optional[IScanExportPort] = None

        self._config: Optional[ExportConfigDTO] = None
        self._export_active: bool = False  # True between ScanStarted and completion/failure/cancel
        self._field_export_active: bool = False  # True if electric field export is configured
        self._field_probe_info: Optional[Dict[str, Any]] = None
        self._field_n_components: int = 0

        # Subscribe to scan events
        self._event_bus.subscribe("scanstarted", self._on_event)
        self._event_bus.subscribe("scanpointacquired", self._on_event)
        self._event_bus.subscribe("scancompleted", self._on_event)
        self._event_bus.subscribe("scanfailed", self._on_event)
        self._event_bus.subscribe("scancancelled", self._on_event)
        # Subscribe to electric field scan events
        self._event_bus.subscribe("electricfieldscanpointacquired", self._on_event)

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

        # Select the appropriate export port based on configuration.
        fmt = (self._config.format or "CSV").upper()
        if fmt == "HDF5":
            self._active_port = self._hdf5_export_port
        else:
            self._active_port = self._csv_export_port

        directory = self._config.output_directory
        # Base filename specific to exported scan data; actual timestamp
        # is applied inside the export port implementation.
        filename_base = f"{self._config.filename_base}_stepScanResults"

        metadata = self._build_metadata(event)

        print(f"[ScanExportService] Starting export to dir='{directory}', base='{filename_base}'")
        logger.debug(
            "Starting scan export for scan_id=%s to directory=%s, filename_base=%s",
            event.scan_id,
            directory,
            filename_base,
        )

        self._active_port.configure(directory, filename_base, metadata)
        self._active_port.start()
        self._export_active = True
        
        # Check if this is an HDF5 port and configure field data if needed
        if fmt == "HDF5" and hasattr(self._active_port, 'configure_field_data'):
            # For now, we'll configure field data when we receive the first electric field point
            # This allows us to get the probe info and number of components from the actual event
            self._field_export_active = True

    def _handle_scan_point_acquired(self, event: ScanPointAcquired) -> None:
        if not self._export_active:
            return

        data = self._flatten_point(event)
        if self._active_port is not None:
            self._active_port.write_point(data)

    def _handle_electric_field_scan_point_acquired(self, event: ElectricFieldScanPointAcquired) -> None:
        """Handle electric field scan point acquired events."""
        if not self._export_active or not self._field_export_active:
            return

        # For HDF5 export, configure field data on first point if not already configured
        if self._field_n_components == 0 and hasattr(self._active_port, 'configure_field_data'):
            n_components = len(event.field_measurement.components)
            # Extract probe info if available from the measurement
            probe_info = {
                "probe_serial": getattr(event.field_measurement, "probe_serial", "unknown"),
                "n_components": n_components,
            }
            self._active_port.configure_field_data(n_components, probe_info)
            self._field_n_components = n_components

        # Flatten the electric field point
        data = self._flatten_electric_field_point(event)
        
        # Write to the active port if it supports field data
        if hasattr(self._active_port, 'write_field_point'):
            self._active_port.write_field_point(data)

    def _handle_scan_finished(self, event: DomainEvent) -> None:
        if not self._export_active:
            return

        logger.debug("Stopping scan export after event: %s", type(event).__name__)
        try:
            if self._active_port is not None:
                self._active_port.stop()
        finally:
            self._export_active = False
            self._active_port = None

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _build_metadata(self, event: ScanStarted) -> Dict[str, Any]:
        """Extract basic metadata from the scan configuration."""
        cfg = event.config
        zone = cfg.scan_zone

        return {
            "scan_id": str(event.scan_id),
            "pattern": cfg.scan_pattern.name,
            "x_min": zone.x_min,
            "x_max": zone.x_max,
            "x_nb_points": cfg.x_nb_points,
            "y_min": zone.y_min,
            "y_max": zone.y_max,
            "y_nb_points": cfg.y_nb_points,
            "stabilization_delay_ms": cfg.stabilization_delay_ms,
            "averaging_per_position": cfg.averaging_per_position,
        }

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

        return {
            "scan_id": str(event.scan_id),
            "point_index": event.point_index,
            "x": pos.x,
            "y": pos.y,
            # Field measurement components
            "field_components": fm.components,
            # Standard deviations (may be None if not provided)
            "field_std_dev_components": fm.std_dev_components,
        }


