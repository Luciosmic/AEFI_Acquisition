from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox, QDoubleSpinBox, QGridLayout, QComboBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from interface.widgets.motion.position_visualizer import PositionVisualizer
from interface.logic.ui_config_store import UIConfigStore

class MotionPanelCompact(QWidget):
    """
    Compact, square version of motion control panel.
    Optimized for smaller spaces while maintaining all essential controls.
    """
    SPEED_MODES = ("slow", "medium", "fast")
    DEFAULT_SPEED_MODE = "medium"
    REFERENTIAL_MODES = ("limit_switch", "centered")
    UNIT_MM = "mm"
    UNIT_INCREMENTS = "incréments"
    MAX_INCREMENTS = 1_000_000  # spinbox ceiling only; the service refuses a setpoint beyond the travel
    DEFAULT_REFERENTIAL_MODE = "limit_switch"
    REFERENTIAL_LABELS = {"limit_switch": "Butées", "centered": "Centré"}
    DEFAULT_JOG_STEP = {"mm": 50.0, "incréments": 1000.0}

    # Signals to be connected to a Presenter
    jog_requested = Signal(float, float)  # dx, dy (mm)
    jog_increments_requested = Signal(int, int)  # dx, dy (controller increments)
    referential_changed = Signal(str)  # 'limit_switch' or 'centered'
    move_to_requested = Signal(str, float)  # axis ('x' or 'y'), target_position
    move_both_requested = Signal(float, float)  # target_x, target_y
    move_to_increments_requested = Signal(object, object)  # x, y in increments; None = axis left alone
    move_to_center_requested = Signal()  # move to center of bench
    home_requested = Signal(str)  # 'x', 'y', 'xy'
    stop_requested = Signal()
    estop_requested = Signal()
    speed_mode_changed = Signal(str)  # 'slow', 'medium', 'fast'

    def __init__(self, parent=None, config_store: UIConfigStore = None):
        super().__init__(parent)
        self._config_store = config_store or UIConfigStore()
        self._max_x = 1270.0
        self._max_y = 1270.0
        self._last_x = 0.0
        self._last_y = 0.0
        self._last_increments = (0, 0)
        self._unit = self.UNIT_MM
        self._jog_step = dict(self.DEFAULT_JOG_STEP)  # remembered per unit: 50 mm is not 50 increments
        self._mm_position_known = False  # the mm position only exists once the bench is calibrated
        self._jog_idle = True  # no motion in progress
        self._referential_mode = self._load_referential_mode()
        self._not_calibrated = False
        self._build_ui()
        self._connect_signals()
        self._load_speed_mode()

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
        
        # --- Readout: the position in the panel's unit, the other unit underneath ---
        pos_layout = QHBoxLayout()
        self.lbl_x = QLabel("X: 0.00")
        self.lbl_y = QLabel("Y: 0.00")
        self.lbl_x.setStyleSheet("font-weight: bold; font-size: 14px; color: #4CAF50;")
        self.lbl_y.setStyleSheet("font-weight: bold; font-size: 14px; color: #2196F3;")
        pos_layout.addWidget(self.lbl_x)
        pos_layout.addSpacing(12)
        pos_layout.addWidget(self.lbl_y)
        pos_layout.addStretch()
        self.lbl_status = QLabel("IDLE")
        self.lbl_status.setStyleSheet("color: #AAA; font-size: 10px; font-weight: bold;")
        pos_layout.addWidget(self.lbl_status)
        v_layout.addLayout(pos_layout)

        # The other unit, small: the controller's pulse count is always from the homing switch, the mm
        # follow the referential chosen below.
        self.lbl_increments = QLabel("Incréments  X: —   Y: —")
        self.lbl_increments.setToolTip(
            "Compteur d'incréments du contrôleur (référentiel butées), indépendant du facteur µm/incrément"
        )
        self.lbl_increments.setStyleSheet("color: #AAA; font-size: 10px;")
        v_layout.addWidget(self.lbl_increments)

        # --- Modes: the three choices that change how everything below reads or moves ---
        self.combo_unit = QComboBox()
        self.combo_unit.addItems([self.UNIT_MM, self.UNIT_INCREMENTS])
        self.combo_unit.setToolTip(
            "Unité de tout le panneau : position affichée, consignes et pas du jog.\n"
            "mm : demande le facteur µm/incrément ; incréments : l'unité du contrôleur, toujours disponible."
        )
        self.combo_referential = QComboBox()
        for mode in self.REFERENTIAL_MODES:
            self.combo_referential.addItem(self.REFERENTIAL_LABELS[mode], mode)
        self.combo_referential.setCurrentIndex(self.REFERENTIAL_MODES.index(self._referential_mode))
        self.combo_referential.setToolTip(
            "Butées : 0 = butée de homing. Centré : (0,0) = milieu du banc. Ne joue que pour les mm."
        )
        self.combo_speed_mode = QComboBox()
        self.combo_speed_mode.addItems([m.capitalize() for m in self.SPEED_MODES])
        modes_layout = QHBoxLayout()
        modes_layout.setSpacing(6)
        for caption, combo in (
            ("Unité", self.combo_unit), ("Référentiel", self.combo_referential), ("Vitesse", self.combo_speed_mode)
        ):
            modes_layout.addWidget(QLabel(caption))
            modes_layout.addWidget(combo)
            modes_layout.addSpacing(6)
        modes_layout.addStretch()
        v_layout.addWidget(self._separator())
        v_layout.addLayout(modes_layout)
        v_layout.addWidget(self._separator())

        # --- Go to: one target per axis, in the panel's unit (shown as the spinbox suffix) ---
        goto = QGridLayout()
        goto.setHorizontalSpacing(6)
        goto.setVerticalSpacing(6)
        self.lbl_target_x = QLabel("Cible X")
        self.lbl_target_y = QLabel("Cible Y")
        self.spin_to_x = QDoubleSpinBox()
        self.spin_to_y = QDoubleSpinBox()
        for spin in (self.spin_to_x, self.spin_to_y):
            spin.setRange(0.0, 1270.0)
            spin.setDecimals(1)
            spin.setSuffix(" mm")
            spin.setMinimumWidth(110)
        self.btn_go_x = QPushButton("X→")
        self.btn_go_y = QPushButton("Y→")
        self.btn_go_both = QPushButton("XY→")
        self.btn_go_both.setToolTip("Move both axes to target")
        self.btn_to_center = QPushButton("To Center")
        self.btn_to_center.setToolTip("Move to center of bench")
        for button in (self.btn_go_x, self.btn_go_y):
            button.setFixedSize(36, 26)
        self.btn_go_both.setFixedSize(60, 26)
        self.btn_to_center.setFixedSize(76, 26)
        goto.addWidget(self.lbl_target_x, 0, 0)
        goto.addWidget(self.spin_to_x, 0, 1)
        goto.addWidget(self.btn_go_x, 0, 2)
        goto.addWidget(self.btn_go_both, 0, 3)
        goto.addWidget(self.lbl_target_y, 1, 0)
        goto.addWidget(self.spin_to_y, 1, 1)
        goto.addWidget(self.btn_go_y, 1, 2)
        goto.addWidget(self.btn_to_center, 1, 3)
        goto.setColumnStretch(4, 1)
        v_layout.addLayout(goto)
        v_layout.addWidget(self._separator())

        # --- Jog (left) and where the bench is (right) ---
        middle = QHBoxLayout()
        middle.setSpacing(14)

        jog_grid = QGridLayout()
        jog_grid.setSpacing(4)
        self.btn_up = QPushButton("▲")
        self.btn_left = QPushButton("◀")
        self.btn_right = QPushButton("▶")
        self.btn_down = QPushButton("▼")
        for button, row, col in ((self.btn_up, 0, 1), (self.btn_left, 1, 0), (self.btn_right, 1, 2), (self.btn_down, 2, 1)):
            button.setFixedSize(38, 38)
            jog_grid.addWidget(button, row, col)
        middle.addLayout(jog_grid)

        # The jog step, in the panel's unit
        step_layout = QVBoxLayout()
        step_layout.setSpacing(4)
        step_layout.addStretch()
        step_layout.addWidget(QLabel("Pas du jog"))
        step_row = QHBoxLayout()
        self.spin_step = QDoubleSpinBox()
        self.spin_step.setRange(1, 500)
        self.spin_step.setValue(50)
        self.spin_step.setSingleStep(10)
        self.spin_step.setDecimals(0)
        self.spin_step.setMinimumWidth(70)
        self.lbl_step_unit = QLabel("mm")
        step_row.addWidget(self.spin_step)
        step_row.addWidget(self.lbl_step_unit)
        step_layout.addLayout(step_row)
        step_layout.addStretch()
        middle.addLayout(step_layout)
        middle.addStretch()

        self.visualizer = PositionVisualizer()
        self.visualizer.setFixedSize(130, 130)
        middle.addWidget(self.visualizer)
        v_layout.addLayout(middle)
        v_layout.addWidget(self._separator())

        # --- Origin (slow) on the left, stops (urgent, coloured) on the right ---
        actions = QHBoxLayout()
        actions.setSpacing(6)
        self.btn_home_x = QPushButton("Home X")
        self.btn_home_y = QPushButton("Home Y")
        self.btn_home_xy = QPushButton("Home XY")
        for button in (self.btn_home_x, self.btn_home_y, self.btn_home_xy):
            button.setFixedHeight(30)
            actions.addWidget(button)
        actions.addStretch()
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setStyleSheet("background-color: #FBC02D; color: black; font-weight: bold; font-size: 11px;")
        self.btn_estop = QPushButton("E-STOP")
        self.btn_estop.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; font-size: 11px;")
        for button in (self.btn_stop, self.btn_estop):
            button.setFixedSize(75, 30)
            actions.addWidget(button)
        v_layout.addLayout(actions)
        v_layout.addStretch()

        # "Bench not calibrated" banner: hidden until the presenter says so.
        self.lbl_calibration_banner = QLabel()
        self.lbl_calibration_banner.setWordWrap(True)
        self.lbl_calibration_banner.setStyleSheet(
            "background-color: #4E3B00; color: #FFD54F; border: 1px solid #FFC107; "
            "border-radius: 4px; padding: 4px; font-size: 11px; font-weight: bold;"
        )
        self.lbl_calibration_banner.setVisible(False)
        layout.addWidget(self.lbl_calibration_banner)

        layout.addWidget(group)

        self._apply_axis_range()
        self._render_position()

    @staticmethod
    def _separator() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #333;")
        return line

    def _connect_signals(self):
        # Absolute Moves (spinbox values are in the active referential; convert to raw before emitting)
        self.btn_go_x.clicked.connect(self._on_go_x)
        self.btn_go_y.clicked.connect(self._on_go_y)
        self.btn_go_both.clicked.connect(self._on_go_both)
        self.combo_unit.currentTextChanged.connect(self._on_unit_changed)
        self.combo_referential.activated.connect(self._on_referential_chosen)
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

        self.combo_speed_mode.currentTextChanged.connect(self._on_speed_mode_changed)

    def _in_increments(self) -> bool:
        return self._unit == self.UNIT_INCREMENTS

    def _on_go_x(self):
        if self._in_increments():
            self.move_to_increments_requested.emit(int(self.spin_to_x.value()), None)
        else:
            self.move_to_requested.emit('x', self._display_to_raw_x(self.spin_to_x.value()))

    def _on_go_y(self):
        if self._in_increments():
            self.move_to_increments_requested.emit(None, int(self.spin_to_y.value()))
        else:
            self.move_to_requested.emit('y', self._display_to_raw_y(self.spin_to_y.value()))

    def _on_go_both(self):
        if self._in_increments():
            self.move_to_increments_requested.emit(int(self.spin_to_x.value()), int(self.spin_to_y.value()))
        else:
            self.move_both_requested.emit(
                self._display_to_raw_x(self.spin_to_x.value()), self._display_to_raw_y(self.spin_to_y.value())
            )

    def _on_unit_changed(self, unit: str):
        """Switch the whole panel (position, target fields, jog step) between mm and increments; the
        targets start at the current position."""
        self._jog_step[self._unit] = self.spin_step.value()
        self._unit = unit
        self._apply_jog_step_unit()
        self._render_position()
        self.combo_referential.setEnabled(not self._in_increments())
        self.combo_referential.setToolTip(
            "Les incréments se comptent toujours depuis la butée de homing : le référentiel ne joue que pour les mm."
            if self._in_increments() else ""
        )
        if self._in_increments():
            for spin in (self.spin_to_x, self.spin_to_y):
                spin.setSuffix(" inc")
                spin.setDecimals(0)
                spin.setRange(0, self.MAX_INCREMENTS)
                spin.setSingleStep(100)
            self.spin_to_x.setValue(self._last_increments[0])
            self.spin_to_y.setValue(self._last_increments[1])
        else:
            for spin in (self.spin_to_x, self.spin_to_y):
                spin.setSuffix(" mm")
                spin.setDecimals(1)
                spin.setSingleStep(1)
            self._apply_axis_range()
            disp_x, disp_y = self._raw_to_display(self._last_x, self._last_y)
            self.spin_to_x.setValue(disp_x)
            self.spin_to_y.setValue(disp_y)
        self._refresh_go_enabled()
        self._refresh_jog_enabled()

    def _apply_jog_step_unit(self):
        if self._in_increments():
            self.spin_step.setRange(1, 200_000)
            self.spin_step.setSingleStep(100)
            self.lbl_step_unit.setText("inc")
        else:
            self.spin_step.setRange(1, 500)
            self.spin_step.setSingleStep(10)
            self.lbl_step_unit.setText("mm")
        self.spin_step.setValue(self._jog_step[self._unit])

    def _refresh_go_enabled(self):
        """mm moves need the conversion; increment moves do not. To Center stays in mm."""
        for widget in (self.btn_go_x, self.btn_go_y, self.btn_go_both):
            widget.setEnabled(self._in_increments() or not self._not_calibrated)
        self.btn_to_center.setEnabled(not self._not_calibrated)

    def _on_jog(self, dx_sign, dy_sign):
        step = self.spin_step.value()
        if self._in_increments():
            self.jog_increments_requested.emit(int(dx_sign * step), int(dy_sign * step))
        else:
            self.jog_requested.emit(dx_sign * step, dy_sign * step)

    def _load_speed_mode(self):
        """Restore the last-selected speed mode, defaulting to medium."""
        saved_mode = self._config_store.load_motion_config().get("speed_mode", self.DEFAULT_SPEED_MODE)
        if saved_mode not in self.SPEED_MODES:
            saved_mode = self.DEFAULT_SPEED_MODE
        self.combo_speed_mode.setCurrentText(saved_mode.capitalize())

    def _on_speed_mode_changed(self, text: str):
        mode = text.lower()
        self._save_motion_config_key("speed_mode", mode)
        self.speed_mode_changed.emit(mode)

    def get_current_speed_mode(self) -> str:
        """Current speed mode ('slow', 'medium', or 'fast')."""
        return self.combo_speed_mode.currentText().lower()

    def _save_motion_config_key(self, key: str, value: str):
        """Merge a single key into motion_last_config.json (it's shared with other settings)."""
        config = self._config_store.load_motion_config()
        config[key] = value
        self._config_store.save_motion_config(config)

    def _load_referential_mode(self) -> str:
        saved_mode = self._config_store.load_motion_config().get("referential_mode", self.DEFAULT_REFERENTIAL_MODE)
        return saved_mode if saved_mode in self.REFERENTIAL_MODES else self.DEFAULT_REFERENTIAL_MODE

    def set_referential_mode(self, mode: str):
        """Switch between 'limit_switch' (raw, current behavior) and 'centered' (0,0 = bench center).

        Persisted so the Settings panel choice survives restarts. Only the displayed labels and
        the target spinbox range/values are affected — moves are always sent to the service in the
        raw limit-switch referential.
        """
        if mode not in self.REFERENTIAL_MODES or mode == self._referential_mode:
            return
        self._referential_mode = mode
        self._save_motion_config_key("referential_mode", mode)
        self.combo_referential.blockSignals(True)
        self.combo_referential.setCurrentIndex(self.REFERENTIAL_MODES.index(mode))
        self.combo_referential.blockSignals(False)
        self._apply_axis_range()
        self.update_position(self._last_x, self._last_y)

    def _on_referential_chosen(self, index: int):
        """The operator picked a referential here: it also tells the scan configuration."""
        mode = self.combo_referential.itemData(index)
        self.set_referential_mode(mode)
        self.referential_changed.emit(mode)

    def _center_offset(self):
        return self._max_x / 2.0, self._max_y / 2.0

    def _raw_to_display(self, x: float, y: float):
        if self._referential_mode != "centered":
            return x, y
        cx, cy = self._center_offset()
        return x - cx, y - cy

    def _display_to_raw_x(self, x: float) -> float:
        return x + self._center_offset()[0] if self._referential_mode == "centered" else x

    def _display_to_raw_y(self, y: float) -> float:
        return y + self._center_offset()[1] if self._referential_mode == "centered" else y

    def _apply_axis_range(self):
        if self._in_increments():
            return  # the increment range is the controller's, not the bench travel in mm
        if self._referential_mode == "centered":
            half_x, half_y = self._center_offset()
            self.spin_to_x.setRange(-half_x, half_x)
            self.spin_to_y.setRange(-half_y, half_y)
        else:
            self.spin_to_x.setRange(0.0, self._max_x)
            self.spin_to_y.setRange(0.0, self._max_y)

    def set_calibration_banner(self, banner):
        """Show/hide the "bench not calibrated" banner and block every
        command that moves the bench in mm (stop, emergency stop and homing —
        pulses on the limit switches — stay usable)."""
        self._not_calibrated = banner.visible
        self.lbl_calibration_banner.setText(banner.text)
        self.lbl_calibration_banner.setVisible(banner.visible)
        self._refresh_go_enabled()
        self._refresh_jog_enabled()

    def set_jog_enabled(self, enabled: bool):
        """Enable/disable jog buttons based on motion state."""
        self._jog_idle = enabled
        self._refresh_jog_enabled()

    def _refresh_jog_enabled(self):
        """No jog while the axes move; a jog in mm also needs the mm conversion, a jog in increments does not."""
        enabled = self._jog_idle and (self._in_increments() or not self._not_calibrated)
        for button in (self.btn_up, self.btn_down, self.btn_left, self.btn_right):
            button.setEnabled(enabled)

    def update_position(self, x: float, y: float):
        """x, y are raw (limit-switch referential), as reported by the presenter."""
        self._last_x, self._last_y = x, y
        self._mm_position_known = True
        self._render_position()
        self.visualizer.update_position(x, y)  # visualizer always shows raw/physical position

    def update_increments(self, x_increments: int, y_increments: int):
        self._last_increments = (x_increments, y_increments)
        self._render_position()

    def _render_position(self):
        """The big readout is in the panel's unit, the small line below gives the other one: the
        increments are the controller's count (always from the homing switch), the mm follow the
        referential chosen here."""
        inc_x, inc_y = self._last_increments
        if self._mm_position_known:
            disp_x, disp_y = self._raw_to_display(self._last_x, self._last_y)
            mm_text = (f"X: {disp_x:.2f}", f"Y: {disp_y:.2f}")
        else:
            mm_text = ("X: —", "Y: —")  # no mm position before the bench is calibrated
        if self._in_increments():
            self.lbl_x.setText(f"X: {inc_x}")
            self.lbl_y.setText(f"Y: {inc_y}")
            self.lbl_increments.setText(f"mm  {mm_text[0]}   {mm_text[1]}")
        else:
            self.lbl_x.setText(mm_text[0])
            self.lbl_y.setText(mm_text[1])
            self.lbl_increments.setText(f"Incréments  X: {inc_x}   Y: {inc_y}")

    def update_status(self, is_moving: bool):
        self.lbl_status.setText("MOVING" if is_moving else "IDLE")
        self.lbl_status.setStyleSheet(f"color: {'#FFC107' if is_moving else '#AAA'}; font-size: 10px; font-weight: bold;")

    def set_axis_limits(self, max_x: float, max_y: float):
        """Update the maximum range for position spinboxes."""
        self._max_x, self._max_y = max_x, max_y
        self._apply_axis_range()
        self.visualizer.set_limits(max_x, max_y)
