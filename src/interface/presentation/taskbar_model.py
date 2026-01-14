from dataclasses import dataclass
from typing import List, Optional, Any, Dict, Set

@dataclass
class PanelDescriptor:
    id: str
    label: str
    icon_path: Optional[str] = None
    is_visible: bool = True  # Panel is open/visible in UI

class TaskbarPresentationModel:
    """
    Pure Python Presentation Model for the Taskbar.
    Tracks which panels exist and which are visible (open).
    """
    def __init__(self):
        self.panels: List[PanelDescriptor] = []
        self.visible_panel_ids: Set[str] = set()  # Panels currently visible

    def add_panel(self, panel_id: str, label: str, icon_path: Optional[str] = None) -> None:
        """Adds a new panel to the taskbar if it doesn't already exist."""
        if any(p.id == panel_id for p in self.panels):
            return 
            
        panel = PanelDescriptor(id=panel_id, label=label, icon_path=icon_path, is_visible=True)
        self.panels.append(panel)
        self.visible_panel_ids.add(panel_id)

    def remove_panel(self, panel_id: str) -> None:
        """Removes a panel by ID."""
        self.panels = [p for p in self.panels if p.id != panel_id]
        self.visible_panel_ids.discard(panel_id)

    def set_panel_visibility(self, panel_id: str, visible: bool) -> bool:
        """
        Sets the visibility of a panel.
        Returns True if changed, False if invalid ID.
        """
        panel = next((p for p in self.panels if p.id == panel_id), None)
        if not panel:
            return False
        
        panel.is_visible = visible
        
        if visible:
            self.visible_panel_ids.add(panel_id)
        else:
            self.visible_panel_ids.discard(panel_id)
        
        return True

    def is_panel_visible(self, panel_id: str) -> bool:
        """Check if a panel is currently visible."""
        return panel_id in self.visible_panel_ids

    def to_dict(self) -> Dict[str, Any]:
        """Serializable state."""
        return {
            "panels": [
                {"id": p.id, "label": p.label, "icon_path": p.icon_path, "is_visible": p.is_visible}
                for p in self.panels
            ],
            "visible_panel_ids": list(self.visible_panel_ids)
        }
