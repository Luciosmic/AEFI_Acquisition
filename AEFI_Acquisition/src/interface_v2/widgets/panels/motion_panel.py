from matplotlib.patches import StepPatch
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox, QDoubleSpinBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal

class MotionPanel(QWidget):
    """
    Widget for manual motion control.
    Migrated to Interface V2.
    """
    # Signals to be connected to a Presenter or used directly for now
    jog_requested = Signal(float, float) # dx, dy
    move_to_requested = Signal(str, float) # axis ('x' or 'y'), target_position
    home_requested = Signal(str)  # 'x', 'y', 'xy'
    stop_requested = Signal()
    estop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()

    # ... (UI build code remains same) ...

    def _connect_signals(self):
        # Absolute Moves
        self.btn_go_x.clicked.connect(lambda: self.move_to_requested.emit('x', self.spin_to_x.value()))
        self.btn_go_y.clicked.connect(lambda: self.move_to_requested.emit('y', self.spin_to_y.value()))
        
        # Jogging
        self.btn_up.clicked.connect(lambda: self._on_jog(0, 1))
        self.btn_down.clicked.connect(lambda: self._on_jog(0, -1))
        self.btn_left.clicked.connect(lambda: self._on_jog(-1, 0))
        self.btn_right.clicked.connect(lambda: self._on_jog(1, 0))
        
        # Actions
        self.btn_home_x.clicked.connect(lambda: self.home_requested.emit("x"))
        self.btn_home_y.clicked.connect(lambda: self.home_requested.emit("y"))
        self.btn_home_xy.clicked.connect(lambda: self.home_requested.emit("xy"))
        
        self.btn_stop.clicked.connect(self.stop_requested.emit)
        self.btn_estop.clicked.connect(self.estop_requested.emit)

    def _on_jog(self, dx_sign, dy_sign):
        step = self.spin_step.value()
        self.jog_requested.emit(dx_sign * step, dy_sign * step)

    def set_jog_enabled(self, enabled: bool):
        """Enable/disable jog buttons based on motion state."""
        if hasattr(self, 'btn_up'):
            self.btn_up.setEnabled(enabled)
        if hasattr(self, 'btn_down'):
            self.btn_down.setEnabled(enabled)
        if hasattr(self, 'btn_left'):
            self.btn_left.setEnabled(enabled)
        if hasattr(self, 'btn_right'):
            self.btn_right.setEnabled(enabled)

    def update_position(self, x: float, y: float):
        self.lbl_x.setText(f"X: {x:.2f} mm")
        self.lbl_y.setText(f"Y: {y:.2f} mm")

    def update_status(self, is_moving: bool):
        self.lbl_status.setText("MOVING" if is_moving else "IDLE")
        self.lbl_status.setStyleSheet(f"color: {'#FFC107' if is_moving else '#AAA'}; font-weight: bold;")
