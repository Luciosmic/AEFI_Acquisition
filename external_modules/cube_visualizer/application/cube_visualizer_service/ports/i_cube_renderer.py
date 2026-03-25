"""
Outbound port: abstract renderer interface declared by the Application layer.

The Application expresses the NEED for a renderer — Infrastructure provides the implementation.
"""
from abc import ABC, abstractmethod
from scipy.spatial.transform import Rotation as R


class ICubeRenderer(ABC):
    """Outbound port: contract for any 3D rendering adapter."""

    @abstractmethod
    def update_view(self, rotation: R) -> None:
        """Render the cube with the given rotation."""
        ...

    @abstractmethod
    def reset_camera_view(self, view_name: str) -> None:
        """Reset the camera to a named view ('3d', 'xy', 'xz', 'yz')."""
        ...
