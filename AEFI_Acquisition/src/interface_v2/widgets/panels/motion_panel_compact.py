from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox, QDoubleSpinBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal

class MotionPanelCompact(QWidget):
    """
    Compact, square version of motion control panel.
    Optimized for smaller spaces while maintaining all essential controls.
    """
    # Signals to be connected to a Presenter
    jog_requested = Signal(float, float)  # dx, dy
    move_to_requested = Signal(float, float)  # x, y
    home_requested = Signal(str)  # 'x', 'y', 'xy'
    stop_requested = Signal()
    estop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # Compact style
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #333;
                border-radius: 4px;
                margin-top: 6px;
                font-weight: bold;
                font-size: 11px;
                color: #CCC;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 4px;
            }
            QLabel { 
                color: #DDD; 
                font-size: 11px;
            }
            QPushButton {
                background-color: #333;
                color: #EEE;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 3px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #444; }
            QPushButton:pressed { background-color: #222; }
            QDoubleSpinBox {
                background-color: #222;
                color: #FFF;
                border: 1px solid #444;
                padding: 2px;
                font-size: 11px;
            }
        """)
        
        group = QGroupBox("Motion Control")
        v_layout = QVBoxLayout(group)
        v_layout.setSpacing(8)
        v_layout.setContentsMargins(10, 15, 10, 10)
        
        # --- Position Display ---
        pos_layout = QHBoxLayout()
        self.lbl_x = QLabel("X: 0.00")
        self.lbl_y = QLabel("Y: 0.00")
        self.lbl_x.setStyleSheet("font-weight: bold; font-size: 12px; color: #4CAF50;")
        self.lbl_y.setStyleSheet("font-weight: bold; font-size: 12px; color: #2196F3;")
        pos_layout.addWidget(self.lbl_x)
        pos_layout.addWidget(self.lbl_y)
        pos_layout.addStretch()
        
        # Status Label
        self.lbl_status = QLabel("IDLE")
        self.lbl_status.setStyleSheet("color: #AAA; font-size: 10px; font-weight: bold;")
        pos_layout.addWidget(self.lbl_status)
        
        v_layout.addLayout(pos_layout)
        
        # --- Main Controls: Grid + Home Buttons Column ---
        main_h_layout = QHBoxLayout()
        main_h_layout.setSpacing(10)
        
        # Left side: Main Controls Grid
        main_grid = QGridLayout()
        main_grid.setSpacing(6)
        
        # Row 0: Absolute Move Controls
        # X Move
        main_grid.addWidget(QLabel("X:"), 0, 0)
        self.spin_to_x = QDoubleSpinBox()
        self.spin_to_x.setRange(-1000.0, 1000.0)
        self.spin_to_x.setDecimals(1)
        self.spin_to_x.setMaximumWidth(75)
        self.btn_go_x = QPushButton("→")
        self.btn_go_x.setFixedSize(32, 26)
        main_grid.addWidget(self.spin_to_x, 0, 1)
        main_grid.addWidget(self.btn_go_x, 0, 2)
        
        # Y Move
        main_grid.addWidget(QLabel("Y:"), 0, 3)
        self.spin_to_y = QDoubleSpinBox()
        self.spin_to_y.setRange(-1000.0, 1000.0)
        self.spin_to_y.setDecimals(1)
        self.spin_to_y.setMaximumWidth(75)
        self.btn_go_y = QPushButton("→")
        self.btn_go_y.setFixedSize(32, 26)
        main_grid.addWidget(self.spin_to_y, 0, 4)
        main_grid.addWidget(self.btn_go_y, 0, 5)
        
        # Row 1: Step Size
        main_grid.addWidget(QLabel("Step:"), 1, 0)
        self.spin_step = QDoubleSpinBox()
        self.spin_step.setRange(1, 100)
        self.spin_step.setValue(1)
        self.spin_step.setSingleStep(10)
        self.spin_step.setDecimals(0)
        self.spin_step.setMaximumWidth(50)
        main_grid.addWidget(self.spin_step, 1, 1)
        main_grid.addWidget(QLabel("mm"), 1, 2)
        
        # Row 2-4: Jog Buttons (Diamond Layout)
        # Up (Y+)
        self.btn_up = QPushButton("▲")
        self.btn_up.setFixedSize(42, 42)
        main_grid.addWidget(self.btn_up, 2, 3)
        
        # Left (X-)
        self.btn_left = QPushButton("◀")
        self.btn_left.setFixedSize(42, 42)
        main_grid.addWidget(self.btn_left, 3, 2)
        
        # Right (X+)
        self.btn_right = QPushButton("▶")
        self.btn_right.setFixedSize(42, 42)
        main_grid.addWidget(self.btn_right, 3, 4)
        
        # Down (Y-)
        self.btn_down = QPushButton("▼")
        self.btn_down.setFixedSize(42, 42)
        main_grid.addWidget(self.btn_down, 4, 3)
        
        # Row 2-4: Stop Buttons (Left side, stacked)
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setStyleSheet("background-color: #FBC02D; color: black; font-weight: bold; font-size: 11px;")
        self.btn_stop.setFixedSize(75, 38)
        main_grid.addWidget(self.btn_stop, 2, 0, 1, 2)
        
        self.btn_estop = QPushButton("E-STOP")
        self.btn_estop.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; font-size: 11px;")
        self.btn_estop.setFixedSize(75, 38)
        main_grid.addWidget(self.btn_estop, 3, 0, 1, 2)
        
        main_h_layout.addLayout(main_grid)
        
        # Right side: Home Buttons Column
        home_column = QVBoxLayout()
        home_column.setSpacing(6)
        home_column.addStretch()  # Push buttons to top
        
        self.btn_home_x = QPushButton("Home X")
        self.btn_home_x.setFixedWidth(80)
        self.btn_home_x.setFixedHeight(30)
        home_column.addWidget(self.btn_home_x)
        
        self.btn_home_y = QPushButton("Home Y")
        self.btn_home_y.setFixedWidth(80)
        self.btn_home_y.setFixedHeight(30)
        home_column.addWidget(self.btn_home_y)
        
        self.btn_home_xy = QPushButton("Home XY")
        self.btn_home_xy.setFixedWidth(80)
        self.btn_home_xy.setFixedHeight(30)
        home_column.addWidget(self.btn_home_xy)
        
        home_column.addStretch()  # Balance spacing
        
        main_h_layout.addLayout(home_column)
        
        v_layout.addLayout(main_h_layout)
        v_layout.addStretch()
        
        layout.addWidget(group)

    def _connect_signals(self):
        # Absolute Moves
        self.btn_go_x.clicked.connect(lambda: self.move_to_requested.emit(self.spin_to_x.value(), 0))
        self.btn_go_y.clicked.connect(lambda: self.move_to_requested.emit(0, self.spin_to_y.value()))
        
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
        self.lbl_x.setText(f"X: {x:.2f}")
        self.lbl_y.setText(f"Y: {y:.2f}")

    def update_status(self, is_moving: bool):
        self.lbl_status.setText("MOVING" if is_moving else "IDLE")
        self.lbl_status.setStyleSheet(f"color: {'#FFC107' if is_moving else '#AAA'}; font-size: 10px; font-weight: bold;")

