"""
Motion Port Interface

Responsibility:
- Define abstract interface for motion control operations
- Allow domain service to control motion without knowing infrastructure details

Rationale:
- Hexagonal Architecture: Port pattern
- Domain service depends on abstraction, not concrete implementation
- Enables testing with mock implementations

Design:
- Abstract Base Class (ABC)
- Pure interface, no implementation
- Infrastructure layer provides concrete adapter
"""

from abc import ABC, abstractmethod
from typing import Optional
from domain.shared.value_objects.position_2d import Position2D


class IMotionPort(ABC):
    """
    Port interface for motion control.
    
    This is an abstraction that allows the domain service to control
    motion without depending on specific hardware (StageManager, etc.).
    
    Implemented by infrastructure adapters (e.g., MotionAdapter).
    """
    
    @abstractmethod
    def move_to(self, position: Position2D) -> str:
        """
        Move to the specified 2D position.
        
        Args:
            position: Target position in 2D space
            
        Returns:
            motion_id: Unique identifier for the motion command.
        
        Raises:
            MotionError: If movement fails
        """
        pass
    
    @abstractmethod
    def get_current_position(self) -> Position2D:
        """
        Get current position of the motion system.
        
        Returns:
            Current 2D position
        """
        pass
    
    @abstractmethod
    def is_moving(self) -> bool:
        """
        Check if motion system is currently moving.
        
        Returns:
            True if moving, False if stopped
        """
        pass
    
    @abstractmethod
    def wait_until_stopped(self) -> None:
        """
        Block until motion system has stopped moving.
        
        This is useful after issuing a move command to ensure
        the system has reached the target position before proceeding.
        """
        pass

    @abstractmethod
    def set_speed(self, speed: float) -> None:
        """
        Set the target speed for future movements.
        
        Args:
            speed: Target speed in cm/s.
        
        Raises:
            MotionError: If setting speed fails.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """
        Stop motion with deceleration (Normal Stop).
        """
        pass

    @abstractmethod
    def emergency_stop(self) -> None:
        """
        Immediately stop any ongoing motion (Hard Stop).
        """
        pass

    @abstractmethod
    def home(self, axis: Optional[str] = None) -> None:
        """
        Home the specified axis or both axes using hardware homing sequence.
        
        Args:
            axis: 'x', 'y', or None for both axes.
        
        Raises:
            MotionError: If homing fails.
        """
        pass

    @abstractmethod
    def set_reference(self, axis: str, position: float = 0.0) -> None:
        """
        Set the current position of the specified axis to the given value.
        
        This effectively defines the current physical position as the new reference point.
        
        Args:
            axis: 'x' or 'y'.
            position: The value to set the current position to (default 0.0).
        """
        pass

    @abstractmethod
    def get_axis_limits(self) -> tuple[float, float]:
        """
        Get the maximum travel limits for X and Y axes.
        
        Returns:
            tuple (max_x_mm, max_y_mm)
        """
        pass