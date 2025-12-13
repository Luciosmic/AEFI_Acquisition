from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class WindowDescriptor:
    window_id: str
    panels: List[str] = field(default_factory=list) # List of panel_ids
    active_panel_id: Optional[str] = None
    # Position info could be added here (geometry, screen, etc.)

class CarrierPresentationModel:
    """
    Pure Python Presentation Model for the Carrier (Layout Manager).
    Manages the structure of windows and tabs independent of Qt.
    """
    def __init__(self):
        self.windows: List[WindowDescriptor] = []
        # We start with at least one main window
        self.windows.append(WindowDescriptor(window_id="main"))

    def add_panel_to_window(self, panel_id: str, window_id: str = "main") -> None:
        """Adds a panel to a specific window."""
        window = self._find_window(window_id)
        if not window:
            # Fallback to main or create new? For now, fallback to first
            if self.windows:
                window = self.windows[0]
            else:
                return

        if panel_id not in window.panels:
            window.panels.append(panel_id)
            if window.active_panel_id is None:
                window.active_panel_id = panel_id

    def set_active_panel(self, panel_id: str) -> Optional[str]:
        """
        Sets the active panel in whichever window contains it.
        Returns the window_id if found, else None.
        """
        for win in self.windows:
            if panel_id in win.panels:
                win.active_panel_id = panel_id
                return win.window_id
        return None

    def get_active_panel_id(self, window_id: str = "main") -> Optional[str]:
        win = self._find_window(window_id)
        return win.active_panel_id if win else None

    def _find_window(self, window_id: str) -> Optional[WindowDescriptor]:
        return next((w for w in self.windows if w.window_id == window_id), None)

    def to_dict(self) -> Dict[str, Any]:
        """Serializable state."""
        return {
            "windows": [
                {
                    "id": w.window_id,
                    "panels": w.panels,
                    "active": w.active_panel_id
                }
                for w in self.windows
            ]
        }
