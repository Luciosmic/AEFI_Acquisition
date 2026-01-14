from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QBrush, QPen, QColor

class PositionVisualizer(QWidget):
    """
    Visualizes the current position of the motion system within its travel limits.
    Draws a rectangle representing the bench workspace and a dot for the current position.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(100, 100)
        self.setStyleSheet("background-color: #222; border: 1px solid #444;")
        
        # Default limits (will be updated by presenter)
        self._max_x = 100.0
        self._max_y = 100.0
        
        # Current position
        self._current_x = 0.0
        self._current_y = 0.0
        
    def set_limits(self, max_x: float, max_y: float):
        """Set the physical dimensions of the workspace."""
        self._max_x = max(max_x, 1.0) # Avoid division by zero
        self._max_y = max(max_y, 1.0)
        self.update()

    def update_position(self, x: float, y: float):
        """Update the current position marker."""
        self._current_x = x
        self._current_y = y
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor("#222"))
        
        # Calculate scaling factors to fit workspace into widget
        # Maintain aspect ratio? For now, let's stretch to fill to maximize usage of small space
        # or maybe better to keep aspect ratio to not mislead user about geometry.
        # Let's try to keep aspect ratio.
        
        w_widget = self.width()
        h_widget = self.height()
        
        scale_x = w_widget / self._max_x
        scale_y = h_widget / self._max_y
        
        # Use the smaller scale to fit entirely
        scale = min(scale_x, scale_y)
        
        # Centering
        draw_w = self._max_x * scale
        draw_h = self._max_y * scale
        offset_x = (w_widget - draw_w) / 2
        offset_y = (h_widget - draw_h) / 2
        
        # Draw Workspace Boundary
        workspace_rect = QRectF(offset_x, offset_y, draw_w, draw_h)
        painter.setPen(QPen(QColor("#444"), 1, Qt.SolidLine))
        painter.setBrush(QBrush(QColor("#111")))
        painter.drawRect(workspace_rect)
        
        # Draw Grid Lines (optional, maybe 4 quadrants)
        painter.setPen(QPen(QColor("#333"), 1, Qt.DashLine))
        painter.drawLine(offset_x + draw_w/2, offset_y, offset_x + draw_w/2, offset_y + draw_h)
        painter.drawLine(offset_x, offset_y + draw_h/2, offset_x + draw_w, offset_y + draw_h/2)

        # Draw Current Position
        # Coordinate system: usually (0,0) is bottom-left for physical, but top-left for screen.
        # Let's assume (0,0) is bottom-left of the bench.
        # Screen Y = h_widget - (physical_y * scale) - offset_y ... wait
        # If we center the rect:
        # Screen X = offset_x + (physical_x * scale)
        # Screen Y = offset_y + (draw_h - (physical_y * scale))  <-- Invert Y for screen coords
        
        pos_screen_x = offset_x + (self._current_x * scale)
        pos_screen_y = offset_y + (draw_h - (self._current_y * scale))
        
        # Clamp to visual area (just in case)
        pos_screen_x = max(offset_x, min(pos_screen_x, offset_x + draw_w))
        pos_screen_y = max(offset_y, min(pos_screen_y, offset_y + draw_h))
        
        # Draw Point
        radius = 4
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#00E676"))) # Bright Green
        painter.drawEllipse(QRectF(pos_screen_x - radius, pos_screen_y - radius, radius*2, radius*2))
        
        # Draw Coordinates Text (optional, small)
        # painter.setPen(QColor("#AAA"))
        # painter.drawText(self.rect(), Qt.AlignBottom | Qt.AlignRight, f"({self._current_x:.1f}, {self._current_y:.1f})")
