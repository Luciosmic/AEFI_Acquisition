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
    move_to_requested = Signal(float, float) # x, y
    home_requested = Signal(str) # 'x', 'y', 'xy'
    stop_requested = Signal()
    estop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Style
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #333;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                color: #CCC;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
            QLabel { color: #DDD; }
            QPushButton {
                background-color: #333;
                color: #EEE;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover { background-color: #444; }
            QPushButton:pressed { background-color: #222; }
            QDoubleSpinBox {
                background-color: #222;
                color: #FFF;
                border: 1px solid #444;
                padding: 4px;
            }
        """)
        
        group = QGroupBox("Motion Control")
        v_layout = QVBoxLayout(group)
        v_layout.setSpacing(10)
        v_layout.setContentsMargins(15, 20, 15, 15)
        
        # Position Display
        pos_layout = QHBoxLayout()
        self.lbl_x = QLabel("X: 0.00 mm")
        self.lbl_y = QLabel("Y: 0.00 mm")
        self.lbl_x.setStyleSheet("font-weight: bold; font-size: 16px; color: #4CAF50;")
        self.lbl_y.setStyleSheet("font-weight: bold; font-size: 16px; color: #2196F3;")
        pos_layout.addWidget(self.lbl_x)
        pos_layout.addWidget(self.lbl_y)
        pos_layout.addStretch()
        
        # Status Label
        self.lbl_status = QLabel("Idle")
        pos_layout.addWidget(self.lbl_status)
        
        v_layout.addLayout(pos_layout)
        
        # Controls Layout (Grid-like using HBox/VBox)
        controls_layout = QHBoxLayout()
        
        # Left Panel: Move To & Step
        left_panel = QVBoxLayout()
        left_panel.setSpacing(8)
        
        # Absolute Move X
        row_abs_x = QHBoxLayout()
        row_abs_x.addWidget(QLabel("To X:"))
        self.spin_to_x = QDoubleSpinBox()
        self.spin_to_x.setRange(-1000.0, 1000.0)
        self.spin_to_x.setDecimals(1)
        self.btn_go_x = QPushButton("Go")
        self.btn_go_x.setFixedWidth(40)
        row_abs_x.addWidget(self.spin_to_x)
        row_abs_x.addWidget(self.btn_go_x)
        left_panel.addLayout(row_abs_x)
        
        # Absolute Move Y
        row_abs_y = QHBoxLayout()
        row_abs_y.addWidget(QLabel("To Y:"))
        self.spin_to_y = QDoubleSpinBox()
        self.spin_to_y.setRange(-1000.0, 1000.0)
        self.spin_to_y.setDecimals(1)
        self.btn_go_y = QPushButton("Go")
        self.btn_go_y.setFixedWidth(40)
        row_abs_y.addWidget(self.spin_to_y)
        row_abs_y.addWidget(self.btn_go_y)
        left_panel.addLayout(row_abs_y)
        
        # Step Size
        row_step = QHBoxLayout()
        row_step.addWidget(QLabel("Step:"))
        self.spin_step = QDoubleSpinBox()
        self.spin_step.setRange(1, 100)
        self.spin_step.setValue(1)
        self.spin_step.setSingleStep(10)
        self.spin_step.setDecimals(0)  # No decimals
        step_unit = QLabel("mm")
        step_unit.setStyleSheet("color: #AAA;")
        row_step.addWidget(self.spin_step)
        row_step.addWidget(step_unit)
        left_panel.addLayout(row_step)
        
        controls_layout.addLayout(left_panel)
        
        # Jog Buttons (Diamond Layout)
        btn_layout = QGridLayout()
        btn_layout.setSpacing(5)
        
        # Up (Y+) -> Row 0, Col 1
        self.btn_up = QPushButton("▲")
        self.btn_up.setFixedSize(50, 50)
        btn_layout.addWidget(self.btn_up, 0, 1)
        
        # Left (X-) -> Row 1, Col 0
        self.btn_left = QPushButton("◀")
        self.btn_left.setFixedSize(50, 50)
        btn_layout.addWidget(self.btn_left, 1, 0)
        
        # Right (X+) -> Row 1, Col 2
        self.btn_right = QPushButton("▶")
        self.btn_right.setFixedSize(50, 50)
        btn_layout.addWidget(self.btn_right, 1, 2)
        
        # Down (Y-) -> Row 2, Col 1
        self.btn_down = QPushButton("▼")
        self.btn_down.setFixedSize(50, 50)
        btn_layout.addWidget(self.btn_down, 2, 1)
        
        controls_layout.addLayout(btn_layout)
        
        # Action Buttons
        action_layout = QVBoxLayout()
        action_layout.setSpacing(8)
        
        # Homing Row
        home_layout = QHBoxLayout()
        self.btn_home_x = QPushButton("Home X")
        self.btn_home_y = QPushButton("Home Y")
        self.btn_home_xy = QPushButton("Home XY")
        
        home_layout.addWidget(self.btn_home_x)
        home_layout.addWidget(self.btn_home_y)
        home_layout.addWidget(self.btn_home_xy)
        
        action_layout.addLayout(home_layout)
        
        # Stop Controls
        stop_layout = QHBoxLayout()
        
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setStyleSheet("background-color: #FBC02D; color: black; font-weight: bold; height: 40px; font-size: 14px; border: none;")
        
        self.btn_estop = QPushButton("E-STOP")
        self.btn_estop.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; height: 40px; font-size: 14px; border: none;")
        
        stop_layout.addWidget(self.btn_stop)
        stop_layout.addWidget(self.btn_estop)
        
        action_layout.addLayout(stop_layout)
        
        controls_layout.addLayout(action_layout)
        
        v_layout.addLayout(controls_layout)
        
        # Add Stretch to push everything up
        v_layout.addStretch()
        
        layout.addWidget(group)

    def _connect_signals(self):
        # Absolute Moves
        # Note: In a real app we would use values, but here we just verify UI
        self.btn_go_x.clicked.connect(lambda: self.move_to_requested.emit(self.spin_to_x.value(), 0)) # Y ignored
        self.btn_go_y.clicked.connect(lambda: self.move_to_requested.emit(0, self.spin_to_y.value())) # X ignored
        
        # Jogging
        self.btn_up.clicked.connect(lambda: self._on_jog(0, 1))
        self.btn_down.clicked.connect(lambda: self._on_jog(0, -1))
        self.btn_left.clicked.connect(lambda: self._on_jog(-1, 0))
        self.btn_right.clicked.connect(lambda: self._on_jog(1, 0))
        
        # Actions
        self.btn_home_x.clicked.connect(lambda: self.home_requested.emit("x"))
        self.btn_home_y.clicked.connect(lambda: self.home_requested.emit("y"))
        self.btn_home_xy.clicked.connect(lambda: self.home_requested.emit("xy"))
        
        self.btn_stop.clicked.connect(self.stop_requested)
        self.btn_estop.clicked.connect(self.estop_requested)

    def _on_jog(self, dx_sign, dy_sign):
        step = self.spin_step.value()
        self.jog_requested.emit(dx_sign * step, dy_sign * step)

    def update_position(self, x: float, y: float):
        self.lbl_x.setText(f"X: {x:.2f} mm")
        self.lbl_y.setText(f"Y: {y:.2f} mm")

    def update_status(self, is_moving: bool):
        self.lbl_status.setText("MOVING" if is_moving else "IDLE")
        self.lbl_status.setStyleSheet(f"color: {'#FFC107' if is_moving else '#AAA'}; font-weight: bold;")
