import logging
from typing import Tuple, Optional
import numpy as np
from scipy.spatial.transform import Rotation as R

from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.events.sensor_transformation_angles_updated.sensor_transformation_angles_updated import SensorTransformationAnglesUpdated
from application.services.sensor_calibration_service.sensor_calibration_service import (
    ACTIVE_SENSOR_ROTATION_CHANGED_TOPIC,
)
from .dtos.transformation_dtos import SetRotationAnglesDTO

logger = logging.getLogger(__name__)

class TransformationService:
    """
    Brings sensor readings back to the sources frame:
    E_sources = P·E_sensor, where P = Rx(theta_x)·Ry(theta_y)·Rz(theta_z)
    is the mounting rotation (brings the sensor, aligned on the sources frame,
    to its current mounting). The sensor measures E_sensor = Pᵀ·E_sources;
    the coordinate transform is its transpose.
    Definition of the frames and of P:
    domain/calibration/value_objects/rotation_convention/rotation_convention_intention.md.

    The angles follow the active sensor calibration
    (ActiveSensorRotationChanged, published by SensorCalibrationService).
    """
    def __init__(self, event_bus: Optional[IDomainEventBus] = None):
        self._angles = np.array([0.0, 0.0, 0.0]) # degrees [x, y, z]
        self._rotation = R.identity()
        self._enabled = False
        self._event_bus = event_bus
        if event_bus:
            event_bus.subscribe(ACTIVE_SENSOR_ROTATION_CHANGED_TOPIC, self._on_active_rotation_changed)

    def _on_active_rotation_changed(self, event) -> None:
        angles = event.angles
        self.set_rotation_angles(SetRotationAnglesDTO(
            theta_x=angles.theta_x_degrees,
            theta_y=angles.theta_y_degrees,
            theta_z=angles.theta_z_degrees,
        ))

    def set_rotation_angles(self, dto: SetRotationAnglesDTO) -> None:
        """
        Set the angles (DEGREES) of the mounting rotation
        P = Rx·Ry·Rz (scipy 'XYZ', uppercase = intrinsic X->Y'->Z'',
        i.e. rotations about the fixed sources axes applied Z then Y then X).
        Measurement: E_sensor = Pᵀ·E_sources; correction: E_sources = P·E_sensor.
        """
        logger.info(
            "TransformationService: Command set_rotation_angles theta_x=%s theta_y=%s theta_z=%s",
            dto.theta_x, dto.theta_y, dto.theta_z,
        )
        self._angles = np.array([dto.theta_x, dto.theta_y, dto.theta_z])
        # _rotation = P: sensor -> sources coordinate transform, E_sources = P·E_sensor
        self._rotation = R.from_euler('XYZ', self._angles, degrees=True)

        if self._event_bus:
            self._event_bus.publish("sensortransformationanglesupdated", SensorTransformationAnglesUpdated(
                theta_x=dto.theta_x,
                theta_y=dto.theta_y,
                theta_z=dto.theta_z,
            ))

    def get_rotation_angles(self) -> Tuple[float, float, float]:
        """Return current rotation angles (x, y, z) in degrees."""
        return tuple(self._angles)

    def set_enabled(self, enabled: bool):
        """Enable or disable the transformation application."""
        logger.info("TransformationService: Command set_enabled enabled=%s", enabled)
        self._enabled = enabled

    def is_enabled(self) -> bool:
        return self._enabled

    def transform_sensor_to_source(self, vector: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """
        Apply the coordinate transform (Sensor -> Sources).
        E_sources = P·E_sensor
        """
        if not self._enabled:
            return vector
            
        v_in = np.array(vector)
        v_out = self._rotation.apply(v_in)
        return tuple(v_out)

    def transform_source_to_sensor(self, vector: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """
        Apply the measurement (Sources -> Sensor).
        E_sensor = Pᵀ·E_sources
        """
        if not self._enabled:
            return vector
            
        v_in = np.array(vector)
        v_out = self._rotation.apply(v_in, inverse=True)  # Pᵀ
        return tuple(v_out)
    
    # Ignores the enabled flag.
    def force_transform_sensor_to_source(self, vector: Tuple[float, float, float]) -> Tuple[float, float, float]:
        v_in = np.array(vector)
        v_out = self._rotation.apply(v_in)
        return tuple(v_out)
