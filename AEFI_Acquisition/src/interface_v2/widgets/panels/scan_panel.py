from interface_v2.widgets.panels.base_panel import BasePanel

# Placeholder kept for backward compatibility
# Real implementations are:
# - scan_control_panel.py
# - scan_visualization_panel.py

class ScanPanel(BasePanel):
    """
    Placeholder - kept for backward compatibility.
    Use ScanControlPanel and ScanVisualizationPanel instead.
    """
    def __init__(self, parent=None):
        super().__init__("2D Scan (Deprecated - Use Control + Visualization)", "#2196F3", parent)
