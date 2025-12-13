
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox, QDoubleSpinBox, QGridLayout
)
from PyQt6.QtCore import Qt
from .presenter_motion_control import MotionControlPresenter

class MotionControlWidget(QWidget):
    """
    Widget for manual motion control.
    """

    def __init__(self, presenter: MotionControlPresenter, parent=None):
        super().__init__(parent)
        self.presenter = presenter
        
        self._build_ui()
        self._connect_signals()
        self._connect_presenter()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        
        group = QGroupBox("Motion Control")
        v_layout = QVBoxLayout(group)
        v_layout.setSpacing(4)
        v_layout.setContentsMargins(8, 8, 8, 8)
        
        # Position Display
        pos_layout = QHBoxLayout()
        self.lbl_x = QLabel("X: 0.00 mm")
        self.lbl_y = QLabel("Y: 0.00 mm")
        self.lbl_x.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.lbl_y.setStyleSheet("font-weight: bold; font-size: 14px;")
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
        
        # Step Size (Moved here)
        row_step = QHBoxLayout()
        row_step.addWidget(QLabel("Step:"))
        self.spin_step = QDoubleSpinBox()
        self.spin_step.setRange(0.01, 100.0)
        self.spin_step.setValue(1.0)
        self.spin_step.setSingleStep(1.0)
        row_step.addWidget(self.spin_step)
        left_panel.addLayout(row_step)
        
        controls_layout.addLayout(left_panel)
        
        # Jog Buttons (Diamond Layout)
        btn_layout = QGridLayout()
        
        # Up (Y+) -> Row 0, Col 1
        self.btn_up = QPushButton("▲")
        self.btn_up.setFixedSize(40, 40)
        btn_layout.addWidget(self.btn_up, 0, 1)
        
        # Left (X-) -> Row 1, Col 0
        self.btn_left = QPushButton("◀")
        self.btn_left.setFixedSize(40, 40)
        btn_layout.addWidget(self.btn_left, 1, 0)
        
        # Right (X+) -> Row 1, Col 2
        self.btn_right = QPushButton("▶")
        self.btn_right.setFixedSize(40, 40)
        btn_layout.addWidget(self.btn_right, 1, 2)
        
        # Down (Y-) -> Row 2, Col 1
        self.btn_down = QPushButton("▼")
        self.btn_down.setFixedSize(40, 40)
        btn_layout.addWidget(self.btn_down, 2, 1)
        
        # Center spacing/alignment
        btn_layout.setRowStretch(0, 0)
        btn_layout.setRowStretch(1, 0)
        btn_layout.setRowStretch(2, 0)
        
        controls_layout.addLayout(btn_layout)
        
        # Action Buttons
        action_layout = QVBoxLayout()
        
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
        
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setStyleSheet("background-color: #F1C40F; color: black; font-weight: bold; height: 40px; font-size: 14px;")
        
        self.btn_estop = QPushButton("E-STOP")
        self.btn_estop.setStyleSheet("background-color: #E74C3C; color: white; font-weight: bold; height: 40px; font-size: 14px;")
        
        stop_layout.addWidget(self.btn_stop)
        stop_layout.addWidget(self.btn_estop)
        
        action_layout.addLayout(stop_layout)
        
        controls_layout.addLayout(action_layout)
        
        v_layout.addLayout(controls_layout)
        layout.addWidget(group)

    def _connect_signals(self):
        # Absolute Moves
        self.btn_go_x.clicked.connect(lambda: self.presenter.move_to_x(self.spin_to_x.value()))
        self.btn_go_y.clicked.connect(lambda: self.presenter.move_to_y(self.spin_to_y.value()))
        
        # Jogging
        self.btn_up.clicked.connect(lambda: self._on_jog(0, 1))
        self.btn_down.clicked.connect(lambda: self._on_jog(0, -1))
        self.btn_left.clicked.connect(lambda: self._on_jog(-1, 0))
        self.btn_right.clicked.connect(lambda: self._on_jog(1, 0))
        
        # Actions
        self.btn_home_x.clicked.connect(self.presenter.go_home_x)
        self.btn_home_y.clicked.connect(self.presenter.go_home_y)
        self.btn_home_xy.clicked.connect(self.presenter.go_home_xy)
        
        self.btn_stop.clicked.connect(self.presenter.stop_motion)
        self.btn_estop.clicked.connect(self.presenter.emergency_stop)

    def _connect_presenter(self):
        self.presenter.position_updated.connect(self._on_position_updated)
        self.presenter.status_updated.connect(self._on_status_updated)

    def _on_jog(self, dx_sign, dy_sign):
        step = self.spin_step.value()
        self.presenter.move_relative(dx_sign * step, dy_sign * step)

    def _on_position_updated(self, x: float, y: float):
        self.lbl_x.setText(f"X: {x:.2f} mm")
        self.lbl_y.setText(f"Y: {y:.2f} mm")

    def _on_status_updated(self, is_moving: bool):
        self.lbl_status.setText("Moving..." if is_moving else "Idle")
        # Could disable buttons while moving if desired, but jogging often allows sequential clicks
