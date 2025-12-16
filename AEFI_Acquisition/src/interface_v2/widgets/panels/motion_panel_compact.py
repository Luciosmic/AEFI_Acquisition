from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox, QDoubleSpinBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from interface_v2.widgets.motion.position_visualizer import PositionVisualizer

class MotionPanelCompact(QWidget):
    """
    Compact, square version of motion control panel.
    Optimized for smaller spaces while maintaining all essential controls.
    """
    # Signals to be connected to a Presenter
    jog_requested = Signal(float, float)  # dx, dy
    move_to_requested = Signal(str, float)  # axis ('x' or 'y'), target_position
    move_both_requested = Signal(float, float)  # target_x, target_y
    move_to_center_requested = Signal()  # move to center of bench
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
        
        # Row 0: X Target Position
        main_grid.addWidget(QLabel("X Target Position (mm):"), 0, 0)
        self.spin_to_x = QDoubleSpinBox()
        self.spin_to_x.setRange(0.0, 1270.0)
        self.spin_to_x.setDecimals(1)
        self.spin_to_x.setMaximumWidth(75)
        self.btn_go_x = QPushButton("X→")
        self.btn_go_x.setFixedSize(32, 26)
        main_grid.addWidget(self.spin_to_x, 0, 1)
        main_grid.addWidget(self.btn_go_x, 0, 2)
        
        # Row 1: Y Target Position
        main_grid.addWidget(QLabel("Y Target Position (mm):"), 1, 0)
        self.spin_to_y = QDoubleSpinBox()
        self.spin_to_y.setRange(0.0, 1270.0)
        self.spin_to_y.setDecimals(1)
        self.spin_to_y.setMaximumWidth(75)
        self.btn_go_y = QPushButton("Y→")
        self.btn_go_y.setFixedSize(32, 26)
        main_grid.addWidget(self.spin_to_y, 1, 1)
        main_grid.addWidget(self.btn_go_y, 1, 2)

        # Both Move (on same row as Y)
        self.btn_go_both = QPushButton("XY→")
        self.btn_go_both.setFixedSize(36, 26)
        self.btn_go_both.setToolTip("Move both axes to target")
        main_grid.addWidget(self.btn_go_both, 1, 3)
        
        # To Center button (on same row as Y)
        self.btn_to_center = QPushButton("To Center")
        self.btn_to_center.setFixedSize(70, 26)
        self.btn_to_center.setToolTip("Move to center of bench")
        main_grid.addWidget(self.btn_to_center, 1, 4)
        
        # Row 2: Step Size
        main_grid.addWidget(QLabel("Jog To Step:"), 2, 0)
        self.spin_step = QDoubleSpinBox()
        self.spin_step.setRange(1, 500)
        self.spin_step.setValue(50)
        self.spin_step.setSingleStep(10)
        self.spin_step.setDecimals(0)
        self.spin_step.setMaximumWidth(50)
        main_grid.addWidget(self.spin_step, 2, 1)
        main_grid.addWidget(QLabel("mm"), 2, 2)
        
        # Row 3-4: Stop Buttons (Left side, stacked)
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setStyleSheet("background-color: #FBC02D; color: black; font-weight: bold; font-size: 11px;")
        self.btn_stop.setFixedSize(75, 38)
        main_grid.addWidget(self.btn_stop, 3, 0, 1, 2)
        
        self.btn_estop = QPushButton("E-STOP")
        self.btn_estop.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; font-size: 11px;")
        self.btn_estop.setFixedSize(75, 38)
        main_grid.addWidget(self.btn_estop, 4, 0, 1, 2)
        
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
        
        home_column.addStretch()  # Balance spacing
        
        main_h_layout.addLayout(home_column)

        # Right side: Position Visualizer (REMOVED from here)
        # self.visualizer = PositionVisualizer()
        # self.visualizer.setFixedSize(120, 120) 
        # main_h_layout.addWidget(self.visualizer)
        
        v_layout.addLayout(main_h_layout)
        
        # Bottom: Jog Buttons + Position Visualizer (side by side)
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(15)
        
        # Left: Jog Buttons (Diamond Layout in a grid)
        jog_container = QWidget()
        jog_grid = QGridLayout(jog_container)
        jog_grid.setSpacing(6)
        jog_grid.setContentsMargins(0, 0, 0, 0)
        
        # Up (Y+)
        self.btn_up = QPushButton("▲")
        self.btn_up.setFixedSize(42, 42)
        jog_grid.addWidget(self.btn_up, 0, 1)
        
        # Left (X-)
        self.btn_left = QPushButton("◀")
        self.btn_left.setFixedSize(42, 42)
        jog_grid.addWidget(self.btn_left, 1, 0)
        
        # Right (X+)
        self.btn_right = QPushButton("▶")
        self.btn_right.setFixedSize(42, 42)
        jog_grid.addWidget(self.btn_right, 1, 2)
        
        # Down (Y-)
        self.btn_down = QPushButton("▼")
        self.btn_down.setFixedSize(42, 42)
        jog_grid.addWidget(self.btn_down, 2, 1)
        
        bottom_layout.addWidget(jog_container)
        bottom_layout.addStretch()
        
        # Right: Position Visualizer
        self.visualizer = PositionVisualizer()
        self.visualizer.setFixedSize(150, 150)
        bottom_layout.addWidget(self.visualizer)
        
        v_layout.addLayout(bottom_layout)
        v_layout.addStretch()
        
        layout.addWidget(group)

    def _connect_signals(self):
        # Absolute Moves
        self.btn_go_x.clicked.connect(lambda: self.move_to_requested.emit('x', self.spin_to_x.value()))
        self.btn_go_y.clicked.connect(lambda: self.move_to_requested.emit('y', self.spin_to_y.value()))
        self.btn_go_both.clicked.connect(lambda: self.move_both_requested.emit(self.spin_to_x.value(), self.spin_to_y.value()))
        self.btn_to_center.clicked.connect(self.move_to_center_requested.emit)
        
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
        self.btn_up.setEnabled(enabled)
        self.btn_down.setEnabled(enabled)
        self.btn_left.setEnabled(enabled)
        self.btn_right.setEnabled(enabled)

    def update_position(self, x: float, y: float):
        self.lbl_x.setText(f"X: {x:.2f}")
        self.lbl_y.setText(f"Y: {y:.2f}")
        self.visualizer.update_position(x, y)

    def update_status(self, is_moving: bool):
        self.lbl_status.setText("MOVING" if is_moving else "IDLE")
        self.lbl_status.setStyleSheet(f"color: {'#FFC107' if is_moving else '#AAA'}; font-size: 10px; font-weight: bold;")

    def set_axis_limits(self, max_x: float, max_y: float):
        """Update the maximum range for position spinboxes."""
        self.spin_to_x.setRange(0.0, max_x)
        self.spin_to_y.setRange(0.0, max_y)
        self.visualizer.set_limits(max_x, max_y)
