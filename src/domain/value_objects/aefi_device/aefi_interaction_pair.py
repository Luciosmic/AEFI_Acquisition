from dataclasses import dataclass
from .vector_3d import Vector3D

@dataclass(frozen=True)
class AefiInteractionPair:
    """
    Represents a physical interaction link between a specific Source and the Sensor.
    """
    source_id: str
    sensor_id: str
    relative_vector: Vector3D # Vector pointing from Source TO Sensor (or inverse depending on convention)
    # Convention: usually r_vector = r_sensor - r_source
    # This is used for calculating distance (magnitude) and direction.
