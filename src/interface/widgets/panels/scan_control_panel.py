from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QGroupBox, QFormLayout,
    QCheckBox, QFileDialog, QGridLayout, QTabWidget, QRadioButton, QButtonGroup, QToolButton
)
from PySide6.QtCore import Qt, Signal
from pathlib import Path

from interface.logic.ui_config_store import UIConfigStore


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
        # Always visible: what changes from one scan to the next (geometry,
        # Step/Fly mode, stabilization, averaging). Folded under "Réglages
        # avancés": what is set once (pattern, fast axis, differential mode).
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

        self.radio_step = QRadioButton("Step")
        self.radio_step.setToolTip("Arrêt, stabilisation et moyennage à chaque point : la mesure.")
        self.radio_fly = QRadioButton("Fly (exploration)")
        self.radio_fly.setToolTip(
            "Balaye chaque ligne de l'axe rapide d'une traite, sans arrêt par point.\n"
            "Chaque point est placé d'après les positions rapportées par le contrôleur\n"
            "pendant le mouvement : pour repérer une zone avant un step-scan, pas pour mesurer.\n"
            "Stabilization, Averaging et mesure différentielle ne s'appliquent pas.\n"
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

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode:"))
        mode_row.addWidget(self.radio_step)
        mode_row.addWidget(self.radio_fly)
        mode_row.addStretch()

        # Advanced settings, folded by default (state kept in the UI config).
        self.btn_toggle_advanced = self._fold_button("Réglages avancés")
        self.advanced_box = QWidget()
        advanced = QGridLayout(self.advanced_box)
        advanced.setContentsMargins(12, 0, 0, 0)
        advanced.addWidget(QLabel("Pattern:"), 0, 0)
        advanced.addWidget(self.combo_pattern, 0, 1)
        advanced.addWidget(QLabel("Axis (fast):"), 0, 2)
        advanced.addWidget(self.combo_axis, 0, 3)
        advanced.addWidget(self.checkbox_differential_mode, 1, 0, 1, 4)
        advanced.addWidget(QLabel("Diff. settle (ms):"), 2, 0)
        advanced.addWidget(self.input_differential_settle_delay, 2, 1)
        advanced.addWidget(self.btn_save_scan_defaults, 2, 2, 1, 2)
        self.advanced_box.setVisible(False)

        grid.addWidget(self.tabs_scan_kind, 0, 0, 1, 4)
        grid.addLayout(mode_row, 1, 0, 1, 4)
        grid.addWidget(QLabel("Stabilization (ms):"), 2, 0)
        grid.addWidget(self.input_stabilization, 2, 1)
        grid.addWidget(QLabel("Averaging:"), 2, 2)
        grid.addWidget(self.input_averaging, 2, 3)
        grid.addWidget(self.btn_toggle_advanced, 3, 0, 1, 4)
        grid.addWidget(self.advanced_box, 4, 0, 1, 4)

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
        self.btn_toggle_advanced.toggled.connect(
            lambda expanded: self._set_folded_section(self.btn_toggle_advanced, self.advanced_box, expanded, "advanced_expanded")
        )
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

    def _update_mode_dependent_fields(self, *_):
        """Settings a fly scan ignores are greyed; Fly is greyed on the Line tab."""
        self.radio_fly.setEnabled(self._scan_kind() == "grid")
        step_only = not self._is_fly_scan()
        for widget in (
            self.input_stabilization, self.input_averaging,
            self.checkbox_differential_mode, self.input_differential_settle_delay,
        ):
            widget.setEnabled(step_only)

    def _on_browse_export_directory(self):
        start_dir = self.input_export_directory.text() or str(Path.home() / "Desktop" / "AEFI_Acquisition_Exports")
        chosen = QFileDialog.getExistingDirectory(self, "Select export directory", start_dir)
        if chosen:
            self.input_export_directory.setText(chosen)

    def _on_start_clicked(self):
        """Gather parameters and emit signal."""
        params = {
            "scan_kind": self._scan_kind(),
            "line_center_x": self.input_line_center_x.text(),
            "line_center_y": self.input_line_center_y.text(),
            "line_length_mm": self.input_line_length.text(),
            "line_n_points": self.input_line_nb.text(),
            "line_theta_deg": self.input_line_theta.text(),
            "x_min": self.input_x_min.text(),
            "x_max": self.input_x_max.text(),
            "x_nb_points": self.input_x_nb.text(),
            "y_min": self.input_y_min.text(),
            "y_max": self.input_y_max.text(),
            "y_nb_points": self.input_y_nb.text(),
            "stabilization_delay_ms": self.input_stabilization.text(),
            "averaging_per_position": self.input_averaging.text(),
            "scan_pattern": self.combo_pattern.currentText(),
            "scan_axis": self.combo_axis.currentText(),
            "fly_scan": self._is_fly_scan(),
            "differential_mode": self.checkbox_differential_mode.isChecked(),
            "differential_settle_delay_ms": self.input_differential_settle_delay.text(),
            "export_enabled": self.checkbox_export_enabled.isChecked(),
            "export_output_directory": self.input_export_directory.text(),
            "export_filename_base": self.input_export_filename.text(),
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

    def _reset_buttons(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(False)
    
    def _load_config(self):
        """Populate the form from stored scan/export defaults, falling back to UI defaults."""
        scan_config = self._config_store.load_scan_config()
        if scan_config:
            self.input_x_min.setText(str(scan_config.get("x_min", 600.0)))
            self.input_x_max.setText(str(scan_config.get("x_max", 800.0)))
            self.input_x_nb.setText(str(scan_config.get("x_nb_points", 81)))
            self.input_y_min.setText(str(scan_config.get("y_min", 600.0)))
            self.input_y_max.setText(str(scan_config.get("y_max", 800.0)))
            self.input_y_nb.setText(str(scan_config.get("y_nb_points", 81)))
            self.input_stabilization.setText(str(scan_config.get("stabilization_delay_ms", 300)))
            self.input_averaging.setText(str(scan_config.get("averaging_per_position", 10)))
            self.checkbox_differential_mode.setChecked(scan_config.get("differential_mode", False))
            (self.radio_fly if scan_config.get("fly_scan", False) else self.radio_step).setChecked(True)
            self.input_differential_settle_delay.setText(str(scan_config.get("differential_settle_delay_ms", 50)))
            self.input_line_center_x.setText(str(scan_config.get("line_center_x", 700.0)))
            self.input_line_center_y.setText(str(scan_config.get("line_center_y", 700.0)))
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

            for button, key in (
                (self.btn_toggle_advanced, "advanced_expanded"),
                (self.btn_toggle_export_directory, "export_directory_expanded"),
            ):
                expanded = bool(scan_config.get(key, False))
                button.blockSignals(True)
                button.setChecked(expanded)
                button.blockSignals(False)
                box = self.advanced_box if button is self.btn_toggle_advanced else self.export_directory_box
                self._set_folded_section(button, box, expanded, key, save=False)
        self._update_mode_dependent_fields()

        export_config = self._config_store.load_export_config()
        if export_config:
            self.checkbox_export_enabled.setChecked(export_config.get("enabled", True))
            self.input_export_filename.setText(export_config.get("filename_base", "scan"))
            self.input_export_directory.setText(export_config.get("output_directory", ""))

    def _save_scan_defaults(self):
        """Persist the current scan settings (including differential mode) as the new defaults."""
        scan_config = {
            "x_min": float(self.input_x_min.text()),
            "x_max": float(self.input_x_max.text()),
            "x_nb_points": int(self.input_x_nb.text()),
            "y_min": float(self.input_y_min.text()),
            "y_max": float(self.input_y_max.text()),
            "y_nb_points": int(self.input_y_nb.text()),
            "scan_pattern": self.combo_pattern.currentText(),
            "scan_axis": self.combo_axis.currentText(),
            "fly_scan": self.radio_fly.isChecked(),
            "stabilization_delay_ms": int(self.input_stabilization.text()),
            "averaging_per_position": int(self.input_averaging.text()),
            "differential_mode": self.checkbox_differential_mode.isChecked(),
            "differential_settle_delay_ms": float(self.input_differential_settle_delay.text()),
            "scan_kind": self._scan_kind(),
            "line_center_x": float(self.input_line_center_x.text()),
            "line_center_y": float(self.input_line_center_y.text()),
            "line_length_mm": float(self.input_line_length.text()),
            "line_n_points": int(self.input_line_nb.text()),
            "line_theta_deg": float(self.input_line_theta.text()),
            "advanced_expanded": self.btn_toggle_advanced.isChecked(),
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