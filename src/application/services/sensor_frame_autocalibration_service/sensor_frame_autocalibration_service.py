"""
Application Service: Sensor Frame Autocalibration

Orchestrates the automatic calibration of sensor frame rotation angles.
"""

from typing import List, Tuple, Optional
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from domain.events.i_domain_event_bus import IDomainEventBus
from application.services.transformation_service.transformation_service import TransformationService
from application.services.sensor_frame_autocalibration_service.i_sensor_frame_calibration_optimizer import (
    ISensorFrameCalibrationOptimizer
)


class SensorFrameAutocalibrationService:
    """
    Application service for automatic calibration of sensor frame rotation angles.
    
    Orchestrates the calibration process by:
    1. Delegating optimization to the optimizer port
    2. Updating the TransformationService with optimized angles
    """
    
    def __init__(
        self,
        transformation_service: TransformationService,
        optimizer: ISensorFrameCalibrationOptimizer,
        event_bus: Optional[IDomainEventBus] = None
    ):
        """
        Initialize the calibration service.
        
        Args:
            transformation_service: Service to update with calibrated angles
            optimizer: Optimizer port for angle optimization
            event_bus: Optional domain event bus for publishing events
        """
        self._transformation_service = transformation_service
        self._optimizer = optimizer
        self._event_bus = event_bus
    
    def calibrate_from_measurements(
        self,
        x_measurements: List[VoltageMeasurement],
        y_measurements: List[VoltageMeasurement],
        initial_angles: Optional[Tuple[float, float, float]] = None
    ) -> Tuple[float, float, float]:
        """
        Calibrate sensor frame rotation angles from measurement data.
        
        Args:
            x_measurements: List of measurements with X_DIR excitation
            y_measurements: List of measurements with Y_DIR excitation
            initial_angles: Optional initial guess (theta_x, theta_y, theta_z) in degrees
        
        Returns:
            Optimized angles (theta_x, theta_y, theta_z) in degrees
        """
        # Orchestration: delegate to optimizer port
        optimized_angles = self._optimizer.optimize_angles(
            x_measurements,
            y_measurements,
            initial_angles
        )
        
        # Update transformation service
        theta_x, theta_y, theta_z = optimized_angles
        self._transformation_service.set_rotation_angles(theta_x, theta_y, theta_z)
        
        return optimized_angles
