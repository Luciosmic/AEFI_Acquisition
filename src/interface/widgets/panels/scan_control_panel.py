from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QGroupBox, QFormLayout,
    QCheckBox, QFileDialog, QGridLayout, QTabWidget, QRadioButton, QButtonGroup, QToolButton
)
from interface.widgets.operator_selector.operator_selector import OperatorSelector
from interface.widgets.lift_off_input.lift_off_input import LIFT_OFF_LABEL, LIFT_OFF_TOOLTIP, LiftOffInput
from PySide6.QtCore import Qt, Signal
from pathlib import Path

from interface.logic.ui_config_store import UIConfigStore
from interface.presentation.bench_referential import BenchReferential

# Scan zone fields, per scan shape, with the bench axis each one reads: shown in the
# referential chosen in Settings, always sent and saved in the limit-switch one.
_ZONE_FIELD_AXES = {
    "x_min": "x", "x_max": "x", "y_min": "y", "y_max": "y",
    "line_center_x": "x", "line_center_y": "y",
}
_REFERENTIAL_LABELS = {
    "limit_switch": "Référentiel : butées (0 = butée de homing)",
    "centered": "Référentiel : centré (0,0 = centre du banc)",
}


class ScanControlPanel(QWidget):
    """
    Panel for configuring and controlling 2D scans.
    Migrated to Interface V2.
    """
    # Signals
    scan_start_requested = Signal(dict)  # parameters
    scan_stop_requested = Signal()
    scan_pause_requested = Signal()
    scan_resume_requested = Signal()

    def __init__(self, parent=None, config_store: UIConfigStore = None):
        super().__init__(parent)
        self._config_store = config_store or UIConfigStore()
        self._start_blocked = False
        saved_mode = self._config_store.load_motion_config().get("referential_mode", "limit_switch")
        self._referential = BenchReferential().with_mode(saved_mode)
        # Canonical zone, limit-switch referential: the fields are a view of it.
        self._raw_zone = {"x_min": 600.0, "x_max": 800.0, "y_min": 600.0, "y_max": 800.0,
                          "line_center_x": 700.0, "line_center_y": 700.0}
        self._build_ui()
        self._connect_signals()
        self._load_config()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Same compact metrics as MotionPanelCompact / ExcitationPanel so the
        # three panels end up the same height when docked side by side.
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
                padding: 0 5px;
            }
            QLabel { color: #DDD; font-size: 11px; }
            QLineEdit, QComboBox {
                background-color: #222;
                color: #FFF;
                border: 1px solid #444;
                padding: 2px;
                border-radius: 3px;
                font-size: 11px;
            }
            QCheckBox, QRadioButton { color: #DDD; font-size: 11px; }
            QToolButton { color: #AAA; border: none; font-size: 11px; }
            QToolButton:hover { color: #FFF; }
            QTabWidget::pane { border: 1px solid #333; border-radius: 3px; }
            QTabBar::tab {
                background-color: #222;
                color: #AAA;
                border: 1px solid #444;
                padding: 2px 10px;
                font-size: 11px;
            }
            QTabBar::tab:selected { background-color: #333; color: #FFF; }
            QPushButton {
                background-color: #333;
                color: #EEE;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #444; }
            QPushButton:disabled {
                background-color: #222;
                color: #666;
            }
            QPushButton#btn_start {
                background-color: #2E7D32;
                border: 1px solid #43A047;
            }
            QPushButton#btn_start:hover { background-color: #388E3C; }
            QPushButton#btn_stop {
                background-color: #C62828;
                border: 1px solid #E53935;
            }
            QPushButton#btn_stop:hover { background-color: #D32F2F; }
        """)

        # --- Scan Configuration Group ---
        # Geometry and Step/Fly mode, then the settings common to both modes
        # (pattern, main axis, stabilization), then the step-scan-only ones
        # (averaging, differential measurement folded), hidden in a fly scan.
        config_group = QGroupBox("Scan Configuration")
        grid = QGridLayout(config_group)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(8)
        grid.setContentsMargins(10, 15, 10, 10)

        self.input_x_min = QLineEdit("600.0")
        self.input_x_max = QLineEdit("800.0")
        self.input_x_nb = QLineEdit("81")

        self.input_y_min = QLineEdit("600.0")
        self.input_y_max = QLineEdit("800.0")
        self.input_y_nb = QLineEdit("81")

        self.input_stabilization = QLineEdit("300") # ms
        self.input_averaging = QLineEdit("10") # samples

        self.combo_pattern = QComboBox()
        self.combo_pattern.addItems(["SERPENTINE", "RASTER"])

        self.combo_axis = QComboBox()
        self.combo_axis.addItems(["Y", "X"])  # Y = columns-first (preferred)

        self.radio_step = QRadioButton("STEP-SCAN")
        self.radio_step.setToolTip("Arrêt, stabilisation et moyennage à chaque point : la mesure.")
        self.radio_fly = QRadioButton("FLY-SCAN")
        self.radio_fly.setToolTip(
            "Balaye chaque ligne de l'axe rapide d'une traite, sans arrêt par point.\n"
            "Chaque point est placé d'après les positions rapportées par le contrôleur\n"
            "pendant le mouvement : pour repérer une zone avant un step-scan, pas pour mesurer.\n"
            "La stabilisation s'attend au début de chaque ligne ;\n"
            "Averaging et mesure différentielle ne s'appliquent pas.\n"
            "Grille uniquement."
        )
        self.radio_step.setChecked(True)
        mode_group = QButtonGroup(self)
        mode_group.addButton(self.radio_step)
        mode_group.addButton(self.radio_fly)

        self.checkbox_differential_mode = QCheckBox("Mesure différentielle (baseline sans excitation)")
        self.input_differential_settle_delay = QLineEdit("50")  # ms

        self.btn_save_scan_defaults = QPushButton("Set as default")

        # Line scan geometry: theta=0 -> along X, 90 -> along Y.
        self.input_line_center_x = QLineEdit("700.0")
        self.input_line_center_y = QLineEdit("700.0")
        self.input_line_length = QLineEdit("200.0")
        self.input_line_nb = QLineEdit("81")
        self.input_line_theta = QLineEdit("0.0")

        for field in (
            self.input_x_min, self.input_x_max, self.input_x_nb,
            self.input_y_min, self.input_y_max, self.input_y_nb,
            self.input_stabilization, self.input_averaging,
            self.input_differential_settle_delay,
            self.input_line_center_x, self.input_line_center_y,
            self.input_line_length, self.input_line_nb, self.input_line_theta,
        ):
            field.setFixedWidth(70)

        # Geometry depends on the scan shape (one tab per shape); per-point
        # settings below the tabs are shared by every shape.
        self.tabs_scan_kind = QTabWidget()

        grid_tab = QWidget()
        grid_tab_layout = QGridLayout(grid_tab)
        grid_tab_layout.setContentsMargins(4, 6, 4, 4)
        for col, text in enumerate(("Min (mm)", "Max (mm)", "Points"), start=1):
            grid_tab_layout.addWidget(QLabel(text), 0, col)
        for row, (name, widgets) in enumerate((
            ("X:", (self.input_x_min, self.input_x_max, self.input_x_nb)),
            ("Y:", (self.input_y_min, self.input_y_max, self.input_y_nb)),
        ), start=1):
            grid_tab_layout.addWidget(QLabel(name), row, 0)
            for col, w in enumerate(widgets, start=1):
                grid_tab_layout.addWidget(w, row, col)
        self.tabs_scan_kind.addTab(grid_tab, "Grid")

        line_tab = QWidget()
        line_tab_layout = QGridLayout(line_tab)
        line_tab_layout.setContentsMargins(4, 6, 4, 4)
        line_tab_layout.addWidget(QLabel("Center X (mm):"), 0, 0)
        line_tab_layout.addWidget(self.input_line_center_x, 0, 1)
        line_tab_layout.addWidget(QLabel("Center Y (mm):"), 0, 2)
        line_tab_layout.addWidget(self.input_line_center_y, 0, 3)
        line_tab_layout.addWidget(QLabel("Length (mm):"), 1, 0)
        line_tab_layout.addWidget(self.input_line_length, 1, 1)
        line_tab_layout.addWidget(QLabel("Points:"), 1, 2)
        line_tab_layout.addWidget(self.input_line_nb, 1, 3)
        line_tab_layout.addWidget(QLabel("Theta (°):"), 2, 0)
        line_tab_layout.addWidget(self.input_line_theta, 2, 1)
        line_tab_layout.addWidget(QLabel("0° = X, 90° = Y"), 2, 2, 1, 2)
        self.tabs_scan_kind.addTab(line_tab, "Line")

        # Step/Fly mode, top right of the panel, beside the Grid/Line tabs.
        mode_box = QWidget()
        mode_row = QHBoxLayout(mode_box)
        mode_row.setContentsMargins(0, 0, 4, 0)
        mode_row.addWidget(self.radio_step)
        mode_row.addWidget(self.radio_fly)
        self.tabs_scan_kind.setCornerWidget(mode_box, Qt.TopRightCorner)

        self.combo_axis.setToolTip("Axe parcouru le long de chaque ligne ; l'autre axe avance d'une ligne à la suivante.")
        self.lbl_stabilization = QLabel("Stabilization (ms):")
        self.lbl_averaging = QLabel("Averaging:")

        # Differential measurement, step scan only, folded (state kept in the UI config).
        self.btn_toggle_differential = self._fold_button("Mesure différentielle")
        self.differential_box = QWidget()
        differential = QGridLayout(self.differential_box)
        differential.setContentsMargins(12, 0, 0, 0)
        differential.addWidget(self.checkbox_differential_mode, 0, 0, 1, 4)
        differential.addWidget(QLabel("Diff. settle (ms):"), 1, 0)
        differential.addWidget(self.input_differential_settle_delay, 1, 1)
        self.differential_box.setVisible(False)

        self.lbl_referential = QLabel()
        self.lbl_referential.setStyleSheet("color: #AAA; font-style: italic;")
        self.lbl_referential.setToolTip(
            "Les positions de la zone se lisent dans le référentiel choisi dans Settings ; "
            "le scan part toujours dans le référentiel des butées."
        )
        kind_box = QWidget()
        kind_layout = QVBoxLayout(kind_box)
        kind_layout.setContentsMargins(0, 0, 0, 0)
        kind_layout.setSpacing(2)
        kind_layout.addWidget(self.lbl_referential)
        kind_layout.addWidget(self.tabs_scan_kind)
        grid.addWidget(kind_box, 0, 0, 1, 4)
        # Common to step and fly scans.
        grid.addWidget(QLabel("Pattern:"), 2, 0)
        grid.addWidget(self.combo_pattern, 2, 1)
        grid.addWidget(QLabel("Main Axis:"), 2, 2)
        grid.addWidget(self.combo_axis, 2, 3)
        grid.addWidget(self.lbl_stabilization, 3, 0)
        grid.addWidget(self.input_stabilization, 3, 1)
        # Step scan only: hidden in a fly scan.
        grid.addWidget(self.lbl_averaging, 3, 2)
        grid.addWidget(self.input_averaging, 3, 3)
        grid.addWidget(self.btn_toggle_differential, 4, 0, 1, 4)
        grid.addWidget(self.differential_box, 5, 0, 1, 4)
        grid.addWidget(self.btn_save_scan_defaults, 6, 2, 1, 2)

        layout.addWidget(config_group)

        # --- Export Configuration Group ---
        export_group = QGroupBox("Export Configuration")
        export_grid = QGridLayout(export_group)
        export_grid.setHorizontalSpacing(6)
        export_grid.setVerticalSpacing(8)
        export_grid.setContentsMargins(10, 15, 10, 10)

        self.checkbox_export_enabled = QCheckBox("Enable export")
        self.checkbox_export_enabled.setChecked(True)

        self.input_export_filename = QLineEdit("scan")
        self.input_export_directory = QLineEdit("")
        self.input_export_directory.setPlaceholderText("~/Desktop/AEFI_Acquisition_Exports")

        self.input_export_filename.setFixedWidth(90)
        self.btn_browse_export_directory = QPushButton("Browse...")
        self.btn_save_export_defaults = QPushButton("Set as default")

        # Output directory, folded like the advanced scan settings.
        self.btn_toggle_export_directory = self._fold_button("Dossier")
        self.export_directory_box = QWidget()
        export_directory = QGridLayout(self.export_directory_box)
        export_directory.setContentsMargins(12, 0, 0, 0)
        export_directory.addWidget(QLabel("Output dir:"), 0, 0)
        export_directory.addWidget(self.input_export_directory, 0, 1, 1, 2)
        export_directory.addWidget(self.btn_browse_export_directory, 0, 3)
        export_directory.addWidget(self.btn_save_export_defaults, 1, 3)
        self.export_directory_box.setVisible(False)

        export_grid.addWidget(self.checkbox_export_enabled, 0, 0)
        export_grid.addWidget(QLabel("Filename base:"), 0, 1)
        export_grid.addWidget(self.input_export_filename, 0, 2)
        export_grid.addWidget(self.btn_toggle_export_directory, 0, 3)
        export_grid.addWidget(self.export_directory_box, 1, 0, 1, 4)

        # Traceability, written in acquisition-parameters.json; empty = flagged
        # as missing in the document. Kept for the session, never saved.
        # The operator is chosen from the registry (wired to OperatorPresenter).
        self.input_measured_object = QLineEdit("")
        self.input_measured_object.setPlaceholderText("ex. bouteille d'eau, 8 mm des sphères, 350 kΩ")
        self.input_measured_object.setToolTip("Objet mesuré — écrit dans acquisition-parameters.json (feature_of_interest)")
        self.input_lift_off = LiftOffInput()
        self.input_lift_off.setFixedWidth(70)
        lbl_lift_off = QLabel(LIFT_OFF_LABEL)
        lbl_lift_off.setToolTip(LIFT_OFF_TOOLTIP)
        self.operator_selector = OperatorSelector()
        export_grid.addWidget(QLabel("Objet mesuré:"), 2, 0)
        export_grid.addWidget(self.input_measured_object, 2, 1, 1, 3)
        export_grid.addWidget(lbl_lift_off, 3, 0)
        export_grid.addWidget(self.input_lift_off, 3, 1)
        export_grid.addWidget(QLabel("Opérateur:"), 4, 0)
        export_grid.addWidget(self.operator_selector, 4, 1, 1, 3)

        layout.addWidget(export_group)

        # --- Control Group ---
        control_group = QGroupBox("Control")
        btn_layout = QHBoxLayout(control_group)
        btn_layout.setSpacing(6)
        btn_layout.setContentsMargins(10, 15, 10, 10)

        self.btn_start = QPushButton("START")
        self.btn_start.setObjectName("btn_start")
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setObjectName("btn_stop")
        self.btn_pause = QPushButton("Pause")
        self.btn_resume = QPushButton("Resume")

        self.btn_stop.setEnabled(False)
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(False)

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_pause)
        btn_layout.addWidget(self.btn_resume)
        btn_layout.addWidget(self.btn_stop)

        layout.addWidget(control_group)

        # --- "Bench not calibrated" banner (START refused until calibrated) ---
        self.lbl_start_blocked = QLabel()
        self.lbl_start_blocked.setWordWrap(True)
        self.lbl_start_blocked.setStyleSheet(
            "background-color: #4E3B00; color: #FFD54F; border: 1px solid #FFC107; "
            "border-radius: 4px; padding: 4px; font-size: 11px; font-weight: bold;"
        )
        self.lbl_start_blocked.setVisible(False)
        layout.addWidget(self.lbl_start_blocked)

        # --- Status ---
        self.lbl_status = QLabel("Status: Ready")
        self.lbl_status.setStyleSheet("color: #AAA; font-size: 11px;")
        layout.addWidget(self.lbl_status)

        layout.addStretch()

    def _connect_signals(self):
        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_stop.clicked.connect(self.scan_stop_requested)
        self.btn_pause.clicked.connect(self.scan_pause_requested)
        self.btn_resume.clicked.connect(self.scan_resume_requested)
        self.btn_browse_export_directory.clicked.connect(self._on_browse_export_directory)
        self.btn_save_export_defaults.clicked.connect(self._save_export_defaults)
        self.btn_save_scan_defaults.clicked.connect(self._save_scan_defaults)
        self.radio_fly.toggled.connect(self._update_mode_dependent_fields)
        self.tabs_scan_kind.currentChanged.connect(self._update_mode_dependent_fields)
        self.btn_toggle_differential.toggled.connect(self._on_differential_toggled)
        self.btn_toggle_export_directory.toggled.connect(
            lambda expanded: self._set_folded_section(
                self.btn_toggle_export_directory, self.export_directory_box, expanded, "export_directory_expanded"
            )
        )

    @staticmethod
    def _fold_button(text: str) -> QToolButton:
        button = QToolButton()
        button.setText(text)
        button.setCheckable(True)
        button.setArrowType(Qt.RightArrow)
        button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        return button

    def _set_folded_section(self, button: QToolButton, box: QWidget, expanded: bool, ui_key: str, save: bool = True):
        """Show/hide a folded section; its state is kept in the UI config."""
        button.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
        box.setVisible(expanded)
        if save:
            try:
                scan_config = self._config_store.load_scan_config()
                scan_config[ui_key] = expanded
                self._config_store.save_scan_config(scan_config)
            except (OSError, ValueError):
                pass  # a display preference: not worth failing the panel

    def _is_fly_scan(self) -> bool:
        """Fly scan exists for the grid only."""
        return self.radio_fly.isChecked() and self._scan_kind() == "grid"

    def _on_differential_toggled(self, expanded: bool):
        self._set_folded_section(self.btn_toggle_differential, self.differential_box, expanded, "differential_expanded")
        self._update_mode_dependent_fields()

    def _update_mode_dependent_fields(self, *_):
        """Step-scan-only settings are hidden in a fly scan; Fly is greyed on the Line tab."""
        self.radio_fly.setEnabled(self._scan_kind() == "grid")
        step = not self._is_fly_scan()
        for widget in (self.lbl_averaging, self.input_averaging, self.btn_toggle_differential):
            widget.setVisible(step)
        self.differential_box.setVisible(step and self.btn_toggle_differential.isChecked())
        stabilization_tip = (
            "Délai après chaque déplacement, avant la mesure du point." if step
            else "Délai à l'arrivée au début de chaque ligne, avant de la balayer."
        )
        self.lbl_stabilization.setToolTip(stabilization_tip)
        self.input_stabilization.setToolTip(stabilization_tip)

    def _on_browse_export_directory(self):
        start_dir = self.input_export_directory.text() or str(Path.home() / "Desktop" / "AEFI_Acquisition_Exports")
        chosen = QFileDialog.getExistingDirectory(self, "Select export directory", start_dir)
        if chosen:
            self.input_export_directory.setText(chosen)

    # -- referential ----------------------------------------------------------
    def _zone_field(self, key: str) -> QLineEdit:
        return getattr(self, f"input_{key}")

    def _to_raw(self, key: str, displayed: float) -> float:
        convert = self._referential.to_raw_x if _ZONE_FIELD_AXES[key] == "x" else self._referential.to_raw_y
        return convert(displayed)

    def _to_display(self, key: str, raw: float) -> float:
        convert = self._referential.to_display_x if _ZONE_FIELD_AXES[key] == "x" else self._referential.to_display_y
        return convert(raw)

    def _read_zone_fields(self) -> None:
        """Keep the canonical zone up to date with what the operator typed (unreadable text is left alone)."""
        for key in _ZONE_FIELD_AXES:
            try:
                self._raw_zone[key] = self._to_raw(key, float(self._zone_field(key).text()))
            except ValueError:
                pass

    def _render_zone_fields(self) -> None:
        for key in _ZONE_FIELD_AXES:
            text = f"{self._to_display(key, self._raw_zone[key]):.3f}".rstrip("0").rstrip(".")
            self._zone_field(key).setText("0" if text in ("", "-0") else text)
        self.lbl_referential.setText(_REFERENTIAL_LABELS[self._referential.mode])

    def _change_referential(self, referential: BenchReferential) -> None:
        """The same physical zone, written in the new referential."""
        self._read_zone_fields()
        self._referential = referential
        self._render_zone_fields()

    def set_referential_mode(self, mode: str) -> None:
        """Settings panel choice: 'limit_switch' or 'centered'."""
        self._change_referential(self._referential.with_mode(mode))

    def set_axis_limits(self, max_x: float, max_y: float) -> None:
        """The bench travel in mm (its half is the centre) follows the µm-per-increment factor."""
        self._change_referential(self._referential.with_limits(max_x, max_y))

    def _raw_zone_text(self, key: str) -> str:
        """Value sent to the scan: the zone in the limit-switch referential (the text itself if unreadable)."""
        try:
            return repr(round(self._to_raw(key, float(self._zone_field(key).text())), 6))
        except ValueError:
            return self._zone_field(key).text()

    def _on_start_clicked(self):
        """Gather parameters and emit signal."""
        self._read_zone_fields()
        operator = self.operator_selector.current_operator()
        params = {
            "scan_kind": self._scan_kind(),
            "line_center_x": self._raw_zone_text("line_center_x"),
            "line_center_y": self._raw_zone_text("line_center_y"),
            "line_length_mm": self.input_line_length.text(),
            "line_n_points": self.input_line_nb.text(),
            "line_theta_deg": self.input_line_theta.text(),
            "x_min": self._raw_zone_text("x_min"),
            "x_max": self._raw_zone_text("x_max"),
            "x_nb_points": self.input_x_nb.text(),
            "y_min": self._raw_zone_text("y_min"),
            "y_max": self._raw_zone_text("y_max"),
            "y_nb_points": self.input_y_nb.text(),
            "stabilization_delay_ms": self.input_stabilization.text(),
            "averaging_per_position": self.input_averaging.text(),
            "scan_pattern": self.combo_pattern.currentText(),
            "scan_axis": self.combo_axis.currentText(),
            "fly_scan": self._is_fly_scan(),
            # Hidden in a fly scan, which refuses it: a box left checked must not be sent.
            "differential_mode": self.checkbox_differential_mode.isChecked() and not self._is_fly_scan(),
            "differential_settle_delay_ms": self.input_differential_settle_delay.text(),
            "export_enabled": self.checkbox_export_enabled.isChecked(),
            "export_output_directory": self.input_export_directory.text(),
            "export_filename_base": self.input_export_filename.text(),
            "measured_object": self.input_measured_object.text(),
            "lift_off_mm": self.input_lift_off.lift_off_mm(),
            "operator_id": operator.operator_id if operator else "",
            "operator": operator.name if operator else "",
        }
        self.scan_start_requested.emit(params)

    def _scan_kind(self) -> str:
        return "line" if self.tabs_scan_kind.currentIndex() == 1 else "grid"

    def update_status(self, status: str):
        """Update status label."""
        self.lbl_status.setText(f"Status: {status}")

    def on_scan_started(self, scan_id: str):
        """Called when scan starts."""
        self.lbl_status.setText(f"Status: Running (ID: {scan_id})")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_pause.setEnabled(True)
        self.btn_resume.setEnabled(False)

    def on_scan_completed(self, total_points: int):
        """Called when scan completes."""
        self.lbl_status.setText(f"Status: Completed ({total_points} points)")
        self._reset_buttons()

    def on_scan_failed(self, reason: str):
        """Called when scan fails."""
        self.lbl_status.setText(f"Status: Failed ({reason})")
        self._reset_buttons()

    def on_scan_cancelled(self, scan_id: str):
        """Called when scan is cancelled/stopped."""
        self.lbl_status.setText(f"Status: Cancelled")
        self._reset_buttons()

    def on_scan_paused(self, scan_id: str, current_point: int):
        """Called when scan is paused."""
        self.lbl_status.setText(f"Status: Paused (at point {current_point})")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(True)

    def on_scan_resumed(self, scan_id: str, resume_point: int):
        """Called when scan is resumed."""
        self.lbl_status.setText(f"Status: Running (resumed from point {resume_point})")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_pause.setEnabled(True)
        self.btn_resume.setEnabled(False)

    def set_start_availability(self, banner):
        """Block START (with the reason shown) while the bench is not calibrated."""
        self._start_blocked = banner.visible
        self.lbl_start_blocked.setText(banner.text)
        self.lbl_start_blocked.setVisible(banner.visible)
        if banner.visible or not self.btn_stop.isEnabled():
            self.btn_start.setEnabled(not banner.visible)

    def _reset_buttons(self):
        self.btn_start.setEnabled(not self._start_blocked)
        self.btn_stop.setEnabled(False)
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(False)
    
    def _load_config(self):
        """Populate the form from stored scan/export defaults, falling back to UI defaults."""
        scan_config = self._config_store.load_scan_config()
        if scan_config:
            for key in _ZONE_FIELD_AXES:
                self._raw_zone[key] = float(scan_config.get(key, self._raw_zone[key]))
            self.input_x_nb.setText(str(scan_config.get("x_nb_points", 81)))
            self.input_y_nb.setText(str(scan_config.get("y_nb_points", 81)))
            self.input_stabilization.setText(str(scan_config.get("stabilization_delay_ms", 300)))
            self.input_averaging.setText(str(scan_config.get("averaging_per_position", 10)))
            self.checkbox_differential_mode.setChecked(scan_config.get("differential_mode", False))
            (self.radio_fly if scan_config.get("fly_scan", False) else self.radio_step).setChecked(True)
            self.input_differential_settle_delay.setText(str(scan_config.get("differential_settle_delay_ms", 50)))
            self.input_line_length.setText(str(scan_config.get("line_length_mm", 200.0)))
            self.input_line_nb.setText(str(scan_config.get("line_n_points", 81)))
            self.input_line_theta.setText(str(scan_config.get("line_theta_deg", 0.0)))
            self.tabs_scan_kind.setCurrentIndex(1 if scan_config.get("scan_kind") == "line" else 0)

            pattern_index = self.combo_pattern.findText(scan_config.get("scan_pattern", "SERPENTINE"))
            if pattern_index >= 0:
                self.combo_pattern.setCurrentIndex(pattern_index)

            axis_index = self.combo_axis.findText(scan_config.get("scan_axis", "Y"))
            if axis_index >= 0:
                self.combo_axis.setCurrentIndex(axis_index)

            for button, box, key in (
                (self.btn_toggle_differential, self.differential_box, "differential_expanded"),
                (self.btn_toggle_export_directory, self.export_directory_box, "export_directory_expanded"),
            ):
                expanded = bool(scan_config.get(key, False))
                button.blockSignals(True)
                button.setChecked(expanded)
                button.blockSignals(False)
                self._set_folded_section(button, box, expanded, key, save=False)
        self._render_zone_fields()
        self._update_mode_dependent_fields()

        export_config = self._config_store.load_export_config()
        if export_config:
            self.checkbox_export_enabled.setChecked(export_config.get("enabled", True))
            self.input_export_filename.setText(export_config.get("filename_base", "scan"))
            self.input_export_directory.setText(export_config.get("output_directory", ""))

    def _save_scan_defaults(self):
        """Persist the current scan settings (including differential mode) as the new defaults."""
        self._read_zone_fields()
        scan_config = {
            "x_min": self._raw_zone["x_min"],
            "x_max": self._raw_zone["x_max"],
            "x_nb_points": int(self.input_x_nb.text()),
            "y_min": self._raw_zone["y_min"],
            "y_max": self._raw_zone["y_max"],
            "y_nb_points": int(self.input_y_nb.text()),
            "scan_pattern": self.combo_pattern.currentText(),
            "scan_axis": self.combo_axis.currentText(),
            "fly_scan": self.radio_fly.isChecked(),
            "stabilization_delay_ms": int(self.input_stabilization.text()),
            "averaging_per_position": int(self.input_averaging.text()),
            "differential_mode": self.checkbox_differential_mode.isChecked(),
            "differential_settle_delay_ms": float(self.input_differential_settle_delay.text()),
            "scan_kind": self._scan_kind(),
            "line_center_x": self._raw_zone["line_center_x"],
            "line_center_y": self._raw_zone["line_center_y"],
            "line_length_mm": float(self.input_line_length.text()),
            "line_n_points": int(self.input_line_nb.text()),
            "line_theta_deg": float(self.input_line_theta.text()),
            "differential_expanded": self.btn_toggle_differential.isChecked(),
            "export_directory_expanded": self.btn_toggle_export_directory.isChecked(),
        }
        try:
            self._config_store.save_scan_config(scan_config)
            self.lbl_status.setText("Status: Scan defaults saved")
        except (OSError, ValueError) as e:
            self.lbl_status.setText(f"Status: Failed to save scan defaults ({e})")

    def _save_export_defaults(self):
        """Persist the current export settings as the new defaults."""
        export_config = {
            "enabled": self.checkbox_export_enabled.isChecked(),
            "filename_base": self.input_export_filename.text(),
            "output_directory": self.input_export_directory.text(),
        }
        try:
            self._config_store.save_export_config(export_config)
            self.lbl_status.setText("Status: Export defaults saved")
        except OSError as e:
            self.lbl_status.setText(f"Status: Failed to save export defaults ({e})")