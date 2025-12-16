from typing import Tuple, Optional
import numpy as np
from scipy.spatial.transform import Rotation as R

from domain.events.i_domain_event_bus import IDomainEventBus
from domain.events.transformation_events import SensorTransformationAnglesUpdated

class TransformationService:
    """
    Application Service for managing coordinate transformations.
    Wraps the logic for Sensor -> Source rotations.
    """
    def __init__(self, event_bus: Optional[IDomainEventBus] = None):
        self._angles = np.array([0.0, 0.0, 0.0]) # degrees [x, y, z]
        self._rotation = R.identity()
        self._enabled = False
        self._event_bus = event_bus

    def set_rotation_angles(self, theta_x: float, theta_y: float, theta_z: float):
        """
        Set rotation angles in DEGREES.
        Rotation order is 'XYZ' (extrinsic - rotations around FIXED axes).
        """
        self._angles = np.array([theta_x, theta_y, theta_z])
        self._rotation = R.from_euler('XYZ', self._angles, degrees=True)
        
        if self._event_bus:
            self._event_bus.publish("sensortransformationanglesupdated", SensorTransformationAnglesUpdated(
                theta_x=theta_x, 
                theta_y=theta_y, 
                theta_z=theta_z
            ))

    def get_rotation_angles(self) -> Tuple[float, float, float]:
        """Return current rotation angles (x, y, z) in degrees."""
        return tuple(self._angles)

    def set_enabled(self, enabled: bool):
        """Enable or disable the transformation application."""
        self._enabled = enabled

    def is_enabled(self) -> bool:
        return self._enabled

    def transform_sensor_to_source(self, vector: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """
        Apply DIRECT rotation (Sensor -> Source).
        v_source = R * v_sensor
        """
        if not self._enabled:
            return vector
            
        v_in = np.array(vector)
        v_out = self._rotation.apply(v_in)
        return tuple(v_out)

    def transform_source_to_sensor(self, vector: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """
        Apply INVERSE rotation (Source -> Sensor).
        v_sensor = R.inv() * v_source
        """
        # Note: Usually we want inverse transform regardless of enabled state for reverse lookup?
        # But consistency implies if disabled, identity. 
        # However, "Ref. Transform" panel specific logic might need raw access.
        # Let's keep enable check for now, assuming this service drives the "Active" transformation.
        if not self._enabled:
            return vector
            
        v_in = np.array(vector)
        v_out = self._rotation.inv().apply(v_in)
        return tuple(v_out)
    
    # Bypass method for manual checks (like in Ref. Panel)
    def force_transform_sensor_to_source(self, vector: Tuple[float, float, float]) -> Tuple[float, float, float]:
        v_in = np.array(vector)
        v_out = self._rotation.apply(v_in)
        return tuple(v_out)
