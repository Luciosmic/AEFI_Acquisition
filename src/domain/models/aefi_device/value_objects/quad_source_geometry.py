from dataclasses import dataclass
from enum import Enum, auto
from domain.shared.value_objects.vector_3d import Vector3D
from domain.models.aefi_device.value_objects.quaternion import Quaternion

class Quadrant(Enum):
    TOP_RIGHT = auto()    # Quadrant 1 (+, +)
    TOP_LEFT = auto()     # Quadrant 2 (-, +)
    BOTTOM_LEFT = auto()  # Quadrant 3 (-, -)
    BOTTOM_RIGHT = auto() # Quadrant 4 (+, -)

@dataclass(frozen=True)
class QuadSourceGeometry:
    """
    Defines the physical configuration of the 4-source probe.
    - Sources are arranged in a square.
    - The sensor is at the center (0,0,0) of the PROBE local frame.
    """
    diagonal_spacing_mm: float
    sensor_orientation: Quaternion

    def get_source_local_pos(self, quadrant: Quadrant) -> Vector3D:
        """
        Calculate position of a source in the probe's local frame.
        We assume a square configuration where diagonal_spacing is the distance between opposite corners?
        Or is it the full diagonal length? Typically diagonal spacing implies the full diameter.
        Distance from center to a corner = diagonal / 2.
        """
        half_diag = self.diagonal_spacing_mm / 2.0
        # In a square, x = y = r * cos(45) = r * (sqrt(2)/2)
        # r = half_diag
        # coord = (half_diag * sqrt(2)) / 2  --> This simplifies to side_length / 2 geometry.
        
        # Let's trust simple geometry:
        # Distance from center is half_diag.
        # Angle is 45 degrees (pi/4) for Top Right.
        import math
        coord = half_diag * math.cos(math.pi / 4)
        
        x, y = 0.0, 0.0
        
        if quadrant == Quadrant.TOP_RIGHT:
            x, y = coord, coord
        elif quadrant == Quadrant.TOP_LEFT:
            x, y = -coord, coord
        elif quadrant == Quadrant.BOTTOM_LEFT:
            x, y = -coord, -coord
        elif quadrant == Quadrant.BOTTOM_RIGHT:
            x, y = coord, -coord
            
        # Z is 0 in the local plane of the sources
        return Vector3D(x, y, 0.0)
