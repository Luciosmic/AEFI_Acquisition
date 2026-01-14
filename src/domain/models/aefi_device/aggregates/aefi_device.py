from dataclasses import dataclass
from typing import List

from domain.shared.value_objects.vector_3d import Vector3D
from domain.models.aefi_device.value_objects.quaternion import Quaternion
from domain.models.aefi_device.value_objects.quad_source_geometry import QuadSourceGeometry, Quadrant
from domain.models.aefi_device.value_objects.aefi_interaction_pair import AefiInteractionPair

@dataclass(frozen=True)
class AefiDevice:
    """
    Aggregate Root representing the physical AEFI instrument.
    Manages its geometry and configuration.
    """
    id: str
    geometry: QuadSourceGeometry
    
    def get_orientation(self) -> Quaternion:
        """Returns the orientation of the sensor relative to the probe frame."""
        return self.geometry.sensor_orientation

    def get_interactions(self) -> List[AefiInteractionPair]:
        """
        Generates the interaction pairs (Source -> Sensor) based on the geometry.
        The sensor is assumed to be at (0,0,0) in the local frame.
        """
        interactions = []
        
        # We define a standard mapping for Source IDs to Quadrants
        source_map = {
            "S1": Quadrant.TOP_RIGHT,
            "S2": Quadrant.TOP_LEFT,
            "S3": Quadrant.BOTTOM_LEFT,
            "S4": Quadrant.BOTTOM_RIGHT
        }
        
        sensor_pos_local = Vector3D(0.0, 0.0, 0.0)
        
        for s_id, quadrant in source_map.items():
            source_pos_local = self.geometry.get_source_local_pos(quadrant)
            
            # Vector From Source To Sensor
            # r = r_sensor - r_source
            rel_vec = sensor_pos_local - source_pos_local
            
            pair = AefiInteractionPair(
                source_id=s_id,
                sensor_id="CenterSensor",
                relative_vector=rel_vec
            )
            interactions.append(pair)
            
        return interactions
