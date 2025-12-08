"""
Arcus Motion Adapter - Infrastructure Layer

Responsibility:
- Implement IMotionPort interface
- Translate domain Position2D to hardware axis commands
- Manage Arcus Performax 4EX motor controller via serial/USB

Rationale:
- Separates domain logic from hardware details
- Allows domain to remain independent of specific motor controller
- Encapsulates hardware-specific motion control

Design:
- Hexagonal Architecture: Adapter pattern
- Uses pylablib for Arcus communication
- Maps Position2D (x, y) to hardware axes
"""

from typing import Optional
import time

from domain.ports.i_motion_port import IMotionPort
from domain.value_objects.geometric.position_2d import Position2D


class ArcusAdapter(IMotionPort):
    """
    Infrastructure adapter for Arcus Performax 4EX motor controller.
    Implements IMotionPort interface using pylablib.
    """
    
    def __init__(self, port: Optional[str] = None, dll_path: Optional[str] = None):
        """
        Args:
            port: Serial port (e.g., 'COM3'). If None, auto-detect
            dll_path: Path to Arcus DLL files. If None, use default
        """
        self._stage = None
        self._port = port
        self._dll_path = dll_path
        self._axis_x = 0  # Arcus axis index for X
        self._axis_y = 1  # Arcus axis index for Y
        
    def connect(self) -> bool:
        """
        Establish connection to Arcus controller.
        
        Returns:
            True if connection successful
        """
        try:
            import pylablib as pll
            from pylablib.devices import Arcus
            
            # Set DLL path if provided
            if self._dll_path:
                pll.par["devices/dlls/arcus_performax"] = self._dll_path
            
            # Connect to stage
            if self._port:
                self._stage = Arcus.Performax4EXStage(conn=self._port)
            else:
                self._stage = Arcus.Performax4EXStage()
            
            # Enable absolute mode
            self._stage.enable_absolute_mode(True)
            
            return True
        except Exception as e:
            print(f"[ArcusAdapter] Connection failed: {e}")
            return False
    
    def disconnect(self) -> None:
        """Close connection to Arcus controller."""
        if self._stage:
            self._stage.close()
            self._stage = None
    
    def move_to(self, position: Position2D) -> None:
        """
        Move to the specified 2D position.
        
        Args:
            position: Target position in domain units (mm or µm)
        
        Raises:
            RuntimeError: If not connected or movement fails
        """
        if not self._stage:
            raise RuntimeError("Arcus controller not connected")
        
        try:
            # Move both axes simultaneously
            # Note: pylablib Arcus uses increments/steps, not mm
            # Conversion factor should be configured based on hardware setup
            self._stage.move_to(self._axis_x, position.x)
            self._stage.move_to(self._axis_y, position.y)
        except Exception as e:
            raise RuntimeError(f"Move failed: {e}")
    
    def get_current_position(self) -> Position2D:
        """
        Get current position of the motion system.
        
        Returns:
            Current 2D position in domain units
        
        Raises:
            RuntimeError: If not connected
        """
        if not self._stage:
            raise RuntimeError("Arcus controller not connected")
        
        try:
            x_pos = self._stage.get_position(self._axis_x)
            y_pos = self._stage.get_position(self._axis_y)
            return Position2D(x=x_pos, y=y_pos)
        except Exception as e:
            raise RuntimeError(f"Failed to get position: {e}")
    
    def is_moving(self) -> bool:
        """
        Check if motion system is currently moving.
        
        Returns:
            True if any axis is moving
        
        Raises:
            RuntimeError: If not connected
        """
        if not self._stage:
            raise RuntimeError("Arcus controller not connected")
        
        try:
            return (self._stage.is_moving(self._axis_x) or 
                    self._stage.is_moving(self._axis_y))
        except Exception as e:
            raise RuntimeError(f"Failed to check motion status: {e}")
    
    def wait_until_stopped(self, timeout: float = 30.0, poll_interval: float = 0.1) -> None:
        """
        Block until motion system has stopped moving.
        
        Args:
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds
        
        Raises:
            RuntimeError: If not connected or timeout exceeded
        """
        if not self._stage:
            raise RuntimeError("Arcus controller not connected")
        
        start_time = time.time()
        
        while self.is_moving():
            if time.time() - start_time > timeout:
                raise RuntimeError(f"Motion timeout after {timeout}s")
            time.sleep(poll_interval)
    
    def stop(self, immediate: bool = False) -> None:
        """
        Stop motion on all axes.
        
        Args:
            immediate: If True, abrupt stop. If False, gradual deceleration.
        """
        if self._stage:
            self._stage.stop(self._axis_x, immediate=immediate)
            self._stage.stop(self._axis_y, immediate=immediate)
    
    def home(self, axis: Optional[str] = None) -> None:
        """
        Home the specified axis or both axes.
        
        Args:
            axis: 'x', 'y', or None for both
        
        Raises:
            RuntimeError: If not connected or homing fails
        """
        if not self._stage:
            raise RuntimeError("Arcus controller not connected")
        
        try:
            if axis is None or axis.lower() == 'x':
                self._stage.home(self._axis_x, direction="-", home_mode="only_limit_input")
            if axis is None or axis.lower() == 'y':
                self._stage.home(self._axis_y, direction="-", home_mode="only_limit_input")
        except Exception as e:
            raise RuntimeError(f"Homing failed: {e}")

