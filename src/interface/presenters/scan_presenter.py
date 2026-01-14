from PySide6.QtCore import QObject, Signal, Slot
from typing import Dict, Any

from src.application.services.scan_application_service.scan_application_service import ScanApplicationService
from src.application.services.scan_application_service.ports.i_scan_output_port import IScanOutputPort
from src.application.services.scan_application_service.scan_export_service import ScanExportService
from application.dtos.scan_dtos import Scan2DConfigDTO, ExportConfigDTO
from domain.shared.events.i_domain_event_bus import IDomainEventBus
from application.services.transformation_service.transformation_service import TransformationService
from scipy.spatial.transform import Rotation as R
import numpy as np
from typing import Dict, Any

class ScanPresenter(QObject, IScanOutputPort):
    """
    Presenter for the Scan feature.
    
    Responsibility:
    - Acts as the Output Port for ScanApplicationService (receives updates).
    - Handles user interactions from ScanControlPanel.
    - Updates ScanControlPanel and ScanVisualizationPanel via signals.
    """
    
    # Signals to update Views
    scan_started = Signal(str, dict) # scan_id, config
    scan_progress = Signal(int, int, dict) # current, total, point_data
    scan_completed = Signal(int) # total_points
    scan_failed = Signal(str) # reason
    scan_cancelled = Signal(str) # scan_id
    scan_paused = Signal(str, int) # scan_id, current_point_index
    scan_resumed = Signal(str, int) # scan_id, resume_from_point_index
    scan_resumed = Signal(str, int) # scan_id, resume_from_point_index
    status_updated = Signal(str) # status message
    scan_data_bulk_update = Signal(dict) # data_grids
    
    def __init__(self, service: ScanApplicationService, export_service: ScanExportService, event_bus: IDomainEventBus, transformation_service: TransformationService):
        super().__init__()
        self._service = service
        self._export_service = export_service
        self._event_bus = event_bus
        self._transformation_service = transformation_service
        
        # Rotation State
        self._scan_rotation = None
        self._raw_grids = {}
        self._rotated_grids = {}
        self._apply_rotation = False
        self._grid_dims = (0, 0)
        
        # Register myself as the output port only if service doesn't have one yet
        # (to allow Controller CLI → Presenter CLI → Presenter UI pattern)
        if not hasattr(self._service, '_output_port') or self._service._output_port is None:
            self._service.set_output_port(self)
        
    # ==================================================================================
    # IScanOutputPort Implementation (Service -> Presenter)
    # ==================================================================================
    
    def present_scan_started(self, scan_id: str, config: Dict[str, Any]) -> None:
        # Capture rotation angles at start
        angles = self._transformation_service.get_rotation_angles()
        self._scan_rotation = R.from_euler('XYZ', angles, degrees=True)
        
        # Initialize grids
        x_nb = int(config.get('x_nb_points', 0))
        y_nb = int(config.get('y_nb_points', 0))
        self._grid_dims = (x_nb, y_nb)
        
        channels = ['x_in_phase', 'x_quadrature', 'y_in_phase', 'y_quadrature', 'z_in_phase', 'z_quadrature']
        self._raw_grids = {c: np.full((y_nb, x_nb), np.nan) for c in channels}
        self._rotated_grids = {c: np.full((y_nb, x_nb), np.nan) for c in channels}
        
        self.scan_started.emit(scan_id, config)
        self.status_updated.emit(f"Scan started (ID: {scan_id})")
        
    def present_scan_progress(self, current_point_index: int, total_points: int, point_data: Any) -> None:
        # 1. Store Raw Data
        meas = point_data['value']
        x_idx = -1 # We need indices. ScanApplicationService passes x,y coords but not indices directly in 'value'.
        # Wait, ScanApplicationService passes 'index' (linear). We need 2D indices.
        # We can calculate them if we know x_nb.
        
        # Calculate 2D indices from linear index
        # Assuming Raster/Serpentine fills row by row?
        # Actually, ScanVisualizationPanel calculates indices from X/Y coordinates.
        # We should do the same or rely on the View to do it?
        # But we need to store it in OUR grids.
        
        # Let's rely on the View's logic for index calculation? No, Presenter should be robust.
        # Let's use the coordinates to find the index.
        # But we don't have the full grid definition here (min/max/step).
        # We have _grid_dims.
        
        # For now, let's just pass the data to the view as usual, BUT we intercept it to modify the values if rotation is enabled.
        # AND we store both versions.
        
        # We need to calculate rotated values.
        v_in_phase = (meas['x_in_phase'], meas['y_in_phase'], meas['z_in_phase'])
        v_quadrature = (meas['x_quadrature'], meas['y_quadrature'], meas['z_quadrature'])
        
        # Apply rotation (Force application using our captured rotation object)
        v_rot_in_phase = self._scan_rotation.apply(v_in_phase)
        v_rot_quadrature = self._scan_rotation.apply(v_quadrature)
        
        rotated_meas = {
            'x_in_phase': v_rot_in_phase[0], 'x_quadrature': v_rot_quadrature[0],
            'y_in_phase': v_rot_in_phase[1], 'y_quadrature': v_rot_quadrature[1],
            'z_in_phase': v_rot_in_phase[2], 'z_quadrature': v_rot_quadrature[2]
        }
        
        # Store in our grids (We need indices for this!)
        # Since we can't easily calculate indices without x_min/max/step, 
        # let's assume the View handles the mapping from X/Y to pixels.
        # BUT we need to store the FULL GRID to support toggling.
        # So we MUST know the indices.
        
        # Hack: We can ask the Service to pass indices? Or calculate them.
        # ScanPointAcquired has 'point_index'.
        # If we assume row-major order:
        if self._grid_dims[0] > 0:
            y_idx = current_point_index // self._grid_dims[0]
            x_idx = current_point_index % self._grid_dims[0]
            
            # Handle Serpentine? No, index is usually strictly increasing in the trajectory list.
            # But trajectory might be serpentine.
            # This is tricky. The trajectory list order doesn't map linearly to grid if pattern is complex.
            
            # Alternative: Store a list of points (x, y, raw_val, rot_val) and rebuild grid on toggle?
            # Or just update the View with the *current* point using the *selected* mode.
            # And when toggling, we need to re-send ALL points.
            
            # Let's store the list of points.
            if not hasattr(self, '_scan_points_cache'):
                self._scan_points_cache = []
                
            self._scan_points_cache.append({
                'x': point_data['x'],
                'y': point_data['y'],
                'raw': meas,
                'rotated': rotated_meas
            })
            
            # Prepare data for View
            view_data = point_data.copy()
            view_data['value'] = rotated_meas if self._apply_rotation else meas
            
            self.scan_progress.emit(current_point_index, total_points, view_data)
            
            percentage = (current_point_index / total_points * 100) if total_points > 0 else 0
            self.status_updated.emit(f"Progress: {current_point_index}/{total_points} ({percentage:.1f}%)")
        
    def present_scan_completed(self, scan_id: str, total_points: int) -> None:
        self.scan_completed.emit(total_points)
        self.status_updated.emit("Scan completed successfully.")
        
    def present_scan_failed(self, scan_id: str, reason: str) -> None:
        self.scan_failed.emit(reason)
        self.status_updated.emit(f"Scan failed: {reason}")

    def present_scan_cancelled(self, scan_id: str) -> None:
        self.scan_cancelled.emit(scan_id)
        self.status_updated.emit("Scan cancelled.")

    def present_scan_paused(self, scan_id: str, current_point_index: int) -> None:
        self.scan_paused.emit(scan_id, current_point_index)
        self.status_updated.emit(f"Scan paused at point {current_point_index}.")

    def present_scan_resumed(self, scan_id: str, resume_from_point_index: int) -> None:
        self.scan_resumed.emit(scan_id, resume_from_point_index)
        self.status_updated.emit(f"Scan resumed from point {resume_from_point_index}.")
    
    # ==================================================================================
    # FlyScan-specific methods (IScanOutputPort)
    # ==================================================================================
    
    def present_flyscan_started(self, scan_id: str, config: Dict[str, Any]) -> None:
        """Handle FlyScan start event."""
        # Capture rotation angles at start
        angles = self._transformation_service.get_rotation_angles()
        self._scan_rotation = R.from_euler('XYZ', angles, degrees=True)
        
        # Initialize grids (FlyScan has many more points than grid points)
        x_nb = int(config.get('x_nb_points', 0))
        y_nb = int(config.get('y_nb_points', 0))
        estimated_points = int(config.get('estimated_points', 0))
        
        # For FlyScan, we store points in a list (not a fixed grid)
        if not hasattr(self, '_flyscan_points_cache'):
            self._flyscan_points_cache = []
        self._flyscan_points_cache.clear()
        
        self._grid_dims = (x_nb, y_nb)
        
        # Emit signal (reuse scan_started signal)
        self.scan_started.emit(scan_id, config)
        self.status_updated.emit(f"FlyScan started (ID: {scan_id}, estimated {estimated_points} points)")
    
    def present_flyscan_progress(
        self,
        current_point_index: int,
        total_points: int,
        point_data: Any
    ) -> None:
        """Handle FlyScan progress event."""
        # Store point data
        meas = point_data['value']
        
        # Apply rotation if enabled
        v_in_phase = (meas['x_in_phase'], meas['y_in_phase'], meas['z_in_phase'])
        v_quadrature = (meas['x_quadrature'], meas['y_quadrature'], meas['z_quadrature'])
        
        if self._scan_rotation:
            v_rot_in_phase = self._scan_rotation.apply(v_in_phase)
            v_rot_quadrature = self._scan_rotation.apply(v_quadrature)
        else:
            v_rot_in_phase = v_in_phase
            v_rot_quadrature = v_quadrature
        
        rotated_meas = {
            'x_in_phase': v_rot_in_phase[0], 'x_quadrature': v_rot_quadrature[0],
            'y_in_phase': v_rot_in_phase[1], 'y_quadrature': v_rot_quadrature[1],
            'z_in_phase': v_rot_in_phase[2], 'z_quadrature': v_rot_quadrature[2]
        }
        
        # Store in cache
        if not hasattr(self, '_flyscan_points_cache'):
            self._flyscan_points_cache = []
        
        self._flyscan_points_cache.append({
            'x': point_data['x'],
            'y': point_data['y'],
            'raw': meas,
            'rotated': rotated_meas
        })
        
        # Prepare data for View
        view_data = point_data.copy()
        view_data['value'] = rotated_meas if self._apply_rotation else meas
        
        # Emit progress signal (reuse scan_progress signal)
        self.scan_progress.emit(current_point_index, total_points, view_data)
        
        percentage = (current_point_index / total_points * 100) if total_points > 0 else 0
        self.status_updated.emit(f"FlyScan progress: {current_point_index}/{total_points} ({percentage:.1f}%)")
    
    def present_flyscan_completed(self, scan_id: str, total_points: int) -> None:
        """Handle FlyScan completion event."""
        self.scan_completed.emit(total_points)
        self.status_updated.emit(f"FlyScan completed successfully ({total_points} points acquired).")
    
    def present_flyscan_failed(self, scan_id: str, reason: str) -> None:
        """Handle FlyScan failure event."""
        self.scan_failed.emit(reason)
        self.status_updated.emit(f"FlyScan failed: {reason}")
    
    def present_flyscan_cancelled(self, scan_id: str) -> None:
        """Handle FlyScan cancellation event."""
        self.scan_cancelled.emit(scan_id)
        self.status_updated.emit("FlyScan cancelled.")

    # ==================================================================================
    # User Actions (View -> Presenter)
    # ==================================================================================

    @Slot(dict)
    def on_scan_start_requested(self, params: dict):
        """
        Handle start request from View.
        Converts raw dict params to DTO and calls service.
        """
        try:
            # Parse parameters
            dto = Scan2DConfigDTO(
                x_min=float(params.get("x_min", 600)),
                x_max=float(params.get("x_max", 800)),
                x_nb_points=int(params.get("x_nb_points", 41)),
                y_min=float(params.get("y_min", 600)),
                y_max=float(params.get("y_max", 800)),
                y_nb_points=int(params.get("y_nb_points", 41)),
                scan_pattern=params.get("scan_pattern", "SERPENTINE"),
                motion_speed_mm_s=None, # Controlled by hardware config
                stabilization_delay_ms=int(params.get("stabilization_delay_ms", 300)),
                averaging_per_position=int(params.get("averaging_per_position", 10)),
                uncertainty_volts=0.001     # Default
            )
            
            # Configure Export
            export_dto = ExportConfigDTO(
                enabled=params.get("export_enabled", False),
                output_directory=params.get("export_output_directory", ""),
                filename_base=params.get("export_filename_base", "scan"),
                format=params.get("export_format", "CSV")
            )
            self._export_service.configure_export(export_dto)
            
            success = self._service.execute_scan(dto)
            if not success:
                self.status_updated.emit("Failed to start scan (check logs).")
                
        except ValueError as e:
            self.status_updated.emit(f"Invalid parameters: {e}")
        except Exception as e:
            self.status_updated.emit(f"Error starting scan: {e}")

    @Slot()
    def on_scan_stop_requested(self):
        self._service.cancel_scan()
        # Don't set status here - wait for ScanCancelled event

    @Slot()
    def on_scan_pause_requested(self):
        self._service.pause_scan()
        # Don't set status here - wait for ScanPaused event

    @Slot()
    def on_scan_resume_requested(self):
        self._service.resume_scan()
        # Don't set status here - wait for ScanResumed event
    
    # ==================================================================================
    # FlyScan User Actions (View -> Presenter)
    # ==================================================================================
    
    @Slot(dict)
    def on_flyscan_start_requested(self, params: dict):
        """
        Handle FlyScan start request from View.
        Converts raw dict params to FlyScanConfig and calls service.
        """
        try:
            from domain.models.scan.value_objects.fly_scan_config import FlyScanConfig
            from domain.models.scan.value_objects.scan_zone import ScanZone
            from domain.models.scan.value_objects.scan_pattern import ScanPattern
            from domain.models.test_bench.value_objects.motion_profile import MotionProfile
            from application.services.acquisition_configuration_service.acquisition_rate_measurement_service import AcquisitionRateMeasurementService
            from application.services.acquisition_configuration_service.flyscan_configuration_service import FlyScanConfigurationService
            
            # Parse motion profile
            motion_profile_dict = params.get("motion_profile", {})
            motion_profile = MotionProfile(
                min_speed=float(motion_profile_dict.get("min_speed", 0.1)),
                target_speed=float(motion_profile_dict.get("target_speed", 10.0)),
                acceleration=float(motion_profile_dict.get("acceleration", 5.0)),
                deceleration=float(motion_profile_dict.get("deceleration", 5.0))
            )
            
            # Create FlyScanConfig
            config = FlyScanConfig(
                scan_zone=ScanZone(
                    x_min=float(params.get("x_min", 0.0)),
                    x_max=float(params.get("x_max", 10.0)),
                    y_min=float(params.get("y_min", 0.0)),
                    y_max=float(params.get("y_max", 10.0))
                ),
                x_nb_points=int(params.get("x_nb_points", 3)),
                y_nb_points=int(params.get("y_nb_points", 3)),
                scan_pattern=ScanPattern[params.get("scan_pattern", "SERPENTINE")],
                motion_profile=motion_profile,
                desired_acquisition_rate_hz=float(params.get("desired_acquisition_rate_hz", 100.0)),
                max_spatial_gap_mm=float(params.get("max_spatial_gap_mm", 0.5))
            )
            
            # Configure Export
            export_dto = ExportConfigDTO(
                enabled=params.get("export_enabled", False),
                output_directory=params.get("export_output_directory", ""),
                filename_base=params.get("export_filename_base", "flyscan"),
                format=params.get("export_format", "CSV")
            )
            self._export_service.configure_export(export_dto)
            
            # Measure acquisition rate capability (required for FlyScan)
            # For now, use a default or measure
            measurement_service = AcquisitionRateMeasurementService()
            # TODO: Add UI for measurement or use cached value
            # For now, use a reasonable default
            acquisition_rate_hz = config.desired_acquisition_rate_hz
            
            # Validate configuration
            from domain.models.scan.value_objects.acquisition_rate_capability import AcquisitionRateCapability
            from datetime import datetime
            capability = AcquisitionRateCapability(
                measured_rate_hz=acquisition_rate_hz,
                measured_std_dev_hz=0.0,
                measurement_timestamp=datetime.now(),
                measurement_duration_s=1.0,
                sample_count=100
            )
            
            config_service = FlyScanConfigurationService()
            validation = config_service.validate_flyscan_config(config, capability)
            
            if not validation.is_valid:
                errors = "; ".join(validation.errors)
                self.status_updated.emit(f"FlyScan configuration invalid: {errors}")
                return
            
            # Execute FlyScan
            success = self._service.execute_fly_scan(config, acquisition_rate_hz)
            if not success:
                self.status_updated.emit("Failed to start FlyScan (check logs).")
                
        except ValueError as e:
            self.status_updated.emit(f"Invalid parameters: {e}")
        except Exception as e:
            self.status_updated.emit(f"Error starting FlyScan: {e}")

    @Slot(bool)
    def set_apply_rotation(self, enabled: bool):
        """Toggle between Raw and Rotated view."""
        if self._apply_rotation == enabled:
            return
            
        self._apply_rotation = enabled
        self._rebuild_grids_and_emit()

    def _rebuild_grids_and_emit(self):
        # This requires storing config and replicating grid logic.
        # Simpler: Just emit the list of points and let the View rebuild.
        # I'll change `scan_data_bulk_update` to carry a list of points.
        points_to_send = []
        for p in getattr(self, '_scan_points_cache', []):
            val = p['rotated'] if self._apply_rotation else p['raw']
            points_to_send.append({'x': p['x'], 'y': p['y'], 'value': val})
            
        self.scan_data_bulk_update.emit({'points': points_to_send})
