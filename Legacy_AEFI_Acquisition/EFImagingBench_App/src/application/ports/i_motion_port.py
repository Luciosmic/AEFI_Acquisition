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
from src.domain.value_objects.geometric.position_2d import Position2D


class IMotionPort(ABC):
    """
    Port interface for motion control.
    
    This is an abstraction that allows the domain service to control
    motion without depending on specific hardware (StageManager, etc.).
    
    Implemented by infrastructure adapters (e.g., MotionAdapter).
    """
    
    @abstractmethod
    def move_to(self, position: Position2D) -> None:
        """
        Move to the specified 2D position.
        
        Args:
            position: Target position in 2D space
        
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
