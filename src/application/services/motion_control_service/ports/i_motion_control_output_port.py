from abc import ABC, abstractmethod

class IMotionControlOutputPort(ABC):
    """
    Output port for motion control updates.
    Implemented by the Presenter to update the View.
    """
    
    @abstractmethod
    def update_position(self, x: float, y: float) -> None:
        """Update the displayed position."""
        pass

    @abstractmethod
    def update_status(self, is_moving: bool) -> None:
        """Update the motion status (e.g. moving/stopped)."""
        pass

    @abstractmethod
    def present_error(self, message: str) -> None:
        """Present an error message to the user."""
        pass
