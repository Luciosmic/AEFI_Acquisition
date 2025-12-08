"""
Application Layer: Manual Scan Service

Responsibility:
    Orchestrates manual scan workflow where user controls each acquisition point.
    Coordinates motion, acquisition, and data aggregation for manual scanning.

Rationale:
    Manual scans require flexible point-by-point control with parameter updates
    between acquisitions. This service provides the application-level coordination
    between domain entities and infrastructure adapters.

Design:
    - Stateless service (scan state managed by domain entities)
    - Delegates to motion, measurement, and persistence services
    - Returns domain objects, not infrastructure details
"""
from typing import Dict, Any
from uuid import UUID
from datetime import datetime

from ....domain.entities.spatial_scan import SpatialScan


class ManualScanService:
    """Service for manual scan operations."""
    
    def __init__(
        self,
        motion_service=None,  # MotionControlService
        reference_service=None,  # ReferenceMeasurementService
        aggregation_service=None,  # DataAggregationService
        parameter_service=None,  # ParameterManagementService
        persistence_service=None,  # DataPersistenceService
        hardware_adapter=None  # Hardware acquisition adapter (port)
    ):
        """
        Initialize manual scan service with required dependencies.
        
        Args:
            motion_service: Motion control service
            reference_service: Reference measurement service
            aggregation_service: Data aggregation service
            parameter_service: Parameter management service
            persistence_service: Data persistence service
            hardware_adapter: Hardware acquisition adapter (port interface)
        """
        self._motion = motion_service
        self._reference = reference_service
        self._aggregation = aggregation_service
        self._parameters = parameter_service
        self._persistence = persistence_service
        self._hardware = hardware_adapter
        
        # Active scans registry (in-memory for now, could be repository)
        self._active_scans: Dict[UUID, SpatialScan] = {}
    
    def create_manual_scan(self) -> UUID:
        """
        Create a new manual scan.
        
        Returns:
            UUID of created scan
        """
        scan = SpatialScan(scan_type="manual")
        self._active_scans[scan.id] = scan
        return scan.id
    
    def start_manual_scan(self, scan_id: UUID) -> None:
        """
        Start manual scan (mark as RUNNING).
        
        Args:
            scan_id: UUID of scan to start
        """
        scan = self._active_scans.get(scan_id)
        if not scan:
            raise ValueError(f"Scan {scan_id} not found")
        scan.start()
    
    def acquire_at_current_position(self, scan_id: UUID, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Acquire measurement at current motor position.
        
        Responsibility:
            Trigger acquisition without moving motors.
        
        Rationale:
            User may want to acquire at current position without motion.
        
        Design:
            - Get current position from motion service
            - Trigger acquisition with given parameters
            - Add result to scan
            - Return measurement point
        
        Args:
            scan_id: UUID of active scan
            parameters: Acquisition parameters (frequency, integration time, etc.)
            
        Returns:
            Measurement point dict with position and voltage data
        """
        scan = self._active_scans.get(scan_id)
        if not scan:
            raise ValueError(f"Scan {scan_id} not found")
        
        if scan.status.value != "running":
            raise ValueError(f"Scan must be RUNNING, current status: {scan.status.value}")
        
        # Get current position
        position = self._motion.get_current_position() if self._motion else (0.0, 0.0)
        
        # Acquire measurement
        voltage = self._hardware.acquire(parameters) if self._hardware else {"real": 0.0, "imag": 0.0}
        
        # Create measurement point
        measurement_point = {
            "position": position,
            "voltage": voltage,
            "parameters": parameters,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to scan
        scan.add_result(measurement_point)
        
        return measurement_point
    
    async def move_and_acquire(self, scan_id: UUID, position: tuple[float, float], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Move to position then acquire measurement.
        
        Responsibility:
            Coordinate motion and acquisition in sequence.
        
        Rationale:
            Common workflow: move to point, wait for stabilization, acquire.
        
        Design:
            - Command motion to target position
            - Wait for motion completion
            - Trigger acquisition
            - Add result to scan
            - Return measurement point
        
        Args:
            scan_id: UUID of active scan
            position: Target (x, y) position in mm
            parameters: Acquisition parameters
            
        Returns:
            Measurement point at specified position
        """
        scan = self._active_scans.get(scan_id)
        if not scan:
            raise ValueError(f"Scan {scan_id} not found")
        
        if scan.status.value != "running":
            raise ValueError(f"Scan must be RUNNING, current status: {scan.status.value}")
        
        # Move to position (async, waits for completion)
        if self._motion:
            await self._motion.move_to_position(position)
        
        # Acquire measurement
        voltage = self._hardware.acquire(parameters) if self._hardware else {"real": 0.0, "imag": 0.0}
        
        # Create measurement point
        measurement_point = {
            "position": position,
            "voltage": voltage,
            "parameters": parameters,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to scan
        scan.add_result(measurement_point)
        
        return measurement_point
    
    def update_parameters_before_next(self, parameters: Dict[str, Any]) -> None:
        """
        Update acquisition parameters for next measurement.
        
        Responsibility:
            Allow parameter changes between manual acquisitions.
        
        Rationale:
            User may want to adjust frequency, integration time, etc. mid-scan.
        
        Design:
            - Validate parameters
            - Update parameter management service
            - No return (fire-and-forget)
        
        Args:
            parameters: New acquisition parameters
        """
        if self._parameters:
            self._parameters.update_acquisition_params(parameters)
    
    def finalize_manual_scan(self, scan_id: UUID) -> Dict[str, Any]:
        """
        Finalize manual scan and produce structured data.
        
        Responsibility:
            Complete scan lifecycle and aggregate all measurements.
        
        Rationale:
            Manual scan needs explicit finalization to mark completion
            and trigger data structuring/persistence.
        
        Design:
            - Retrieve scan entity by ID
            - Call domain complete() method
            - Structure data via aggregation service
            - Persist structured data
            - Remove from active scans
            - Return structured scan data
        
        Args:
            scan_id: UUID of the manual scan to finalize
            
        Returns:
            Structured scan data dict ready for export/analysis
        """
        scan = self._active_scans.get(scan_id)
        if not scan:
            raise ValueError(f"Scan {scan_id} not found")
        
        # Mark scan as completed (domain lifecycle)
        scan.complete()
        
        # Structure data
        structured_data = {
            "scan_id": str(scan.id),
            "scan_type": scan.scan_type,
            "start_time": scan.start_time.isoformat() if scan.start_time else None,
            "end_time": scan.end_time.isoformat() if scan.end_time else None,
            "status": scan.status.value,
            "measurements": scan.results,
            "num_points": len(scan.results)
        }
        
        # Persist (optional, if service available)
        if self._persistence:
            self._persistence.persist_acquisition(structured_data)
        
        # Remove from active scans
        del self._active_scans[scan_id]
        
        return structured_data
    
    def cancel_scan(self, scan_id: UUID) -> None:
        """
        Cancel an active scan.
        
        Args:
            scan_id: UUID of scan to cancel
        """
        scan = self._active_scans.get(scan_id)
        if not scan:
            raise ValueError(f"Scan {scan_id} not found")
        
        scan.cancel()
        del self._active_scans[scan_id]
    
    def get_scan_status(self, scan_id: UUID) -> Dict[str, Any]:
        """
        Get current scan status.
        
        Args:
            scan_id: UUID of scan
            
        Returns:
            Dict with scan status information
        """
        scan = self._active_scans.get(scan_id)
        if not scan:
            raise ValueError(f"Scan {scan_id} not found")
        
        return {
            "scan_id": str(scan.id),
            "status": scan.status.value,
            "num_measurements": len(scan.results),
            "start_time": scan.start_time.isoformat() if scan.start_time else None
        }
