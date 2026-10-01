from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QDoubleSpinBox, QComboBox, QCheckBox,
    QPushButton,
)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygon
from PySide6.QtCore import Qt, Signal, QRectF, QPoint

def phase_to_sphere_color(phase_degrees: "float | None") -> QColor:
    """Color of a sphere from its APPLIED phase (derived from the DDS
    registers), not from the mode selected in the combo — so a DDS that
    didn't follow the requested direction shows up as a color mismatch.
    Canonical phases keep the historical palette; anything else (manual
    Hardware Config edit, failed write) gets a distinct yellow-gray."""
    if phase_degrees is None:
        return QColor(120, 120, 120)  # no hardware reading yet
    palette = {
        0: QColor(230, 57, 70),      # red
        90: QColor(255, 150, 150),   # light red
        180: QColor(46, 134, 171),   # blue
        270: QColor(150, 150, 255),  # light blue
    }
    for canonical, color in palette.items():
        # circular distance, 1° tolerance (register resolution is ~0.0055°)
        if abs((phase_degrees - canonical + 180.0) % 360.0 - 180.0) < 1.0:
            return color
    return QColor(180, 180, 120)  # non-canonical phase


class SphereVisualizationWidget(QWidget):
    """
    Visualization of the 4 excitation spheres. Each sphere (S1-S4) is colored
    from its live applied phase (see phase_to_sphere_color and
    domain.shared_kernel.excitation.value_objects.sphere_id.SphereId for the
    confirmed DDS-channel/direct-output wiring).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # Slightly larger than before: each sphere now shows its phase value
        # on a second line under the S1-S4 label.
        self.setMinimumSize(140, 110)
        self.setMaximumSize(190, 150)

        # Live phase (degrees), None until the first SynchronousDetectionService
        # refresh — set via set_sphere_phases(), read in paintEvent (drives
        # both the displayed number and the sphere color).
        self.sphere_phases: dict[str, "float | None"] = {'S1': None, 'S2': None, 'S3': None, 'S4': None}

    def set_sphere_phases(self, s1: float, s2: float, s3: float, s4: float) -> None:
        self.sphere_phases = {'S1': s1, 'S2': s2, 'S3': s3, 'S4': s4}
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # 2x2 layout of spheres
        sphere_size = min(w//3, h//3)
        margin_x = (w - 2*sphere_size) // 3
        margin_y = (h - 2*sphere_size) // 3
        
        # Sphere positions, same quadrant convention as Motion Control's
        # position_visualizer.py (top-left=S1, top-right=S3, bottom-left=S4,
        # bottom-right=S2 — S1/S2 and S3/S4 are the diagonal pairs).
        positions = {
            'S4': (margin_x, margin_y + sphere_size + margin_y),               # Bottom left
            'S3': (margin_x + sphere_size + margin_x, margin_y),               # Top right
            'S1': (margin_x, margin_y),                                        # Top left
            'S2': (margin_x + sphere_size + margin_x, margin_y + sphere_size + margin_y) # Bottom right
        }

        # Origin = center of the 4 sphere centers, Y axis pointing up (screen-up),
        # X axis pointing right — physical convention, not screen convention.
        centers = [(x + sphere_size / 2, y + sphere_size / 2) for x, y in positions.values()]
        origin_x = sum(cx for cx, _ in centers) / len(centers)
        origin_y = sum(cy for _, cy in centers) / len(centers)

        axis_pen = QPen(QColor(120, 120, 120), 1, Qt.PenStyle.DashLine)
        painter.setPen(axis_pen)
        painter.drawLine(int(origin_x), 2, int(origin_x), h - 2)  # Y axis
        painter.drawLine(2, int(origin_y), w - 2, int(origin_y))  # X axis

        arrow = 4
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        painter.setBrush(QBrush(QColor(150, 150, 150)))
        # Y+ arrowhead at the top (screen-up = physical Y+)
        painter.drawPolygon(QPolygon([
            QPoint(int(origin_x) - arrow, arrow * 2),
            QPoint(int(origin_x) + arrow, arrow * 2),
            QPoint(int(origin_x), 0),
        ]))
        # X+ arrowhead at the right
        painter.drawPolygon(QPolygon([
            QPoint(w - arrow * 2, int(origin_y) - arrow),
            QPoint(w - arrow * 2, int(origin_y) + arrow),
            QPoint(w, int(origin_y)),
        ]))

        painter.setFont(QFont("Arial", 7))
        painter.setPen(QColor(160, 160, 160))
        painter.drawText(int(origin_x) + 3, 10, "y")
        painter.drawText(w - 10, int(origin_y) - 3, "x")

        # Draw spheres
        for sphere_id, (x, y) in positions.items():
            color = phase_to_sphere_color(self.sphere_phases.get(sphere_id))

            # Sphere with 3D effect
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.drawEllipse(x, y, sphere_size, sphere_size)

            # Highlight for 3D effect
            highlight_color = QColor(255, 255, 255, 100)
            painter.setBrush(QBrush(highlight_color))
            painter.setPen(QPen(Qt.PenStyle.NoPen))
            painter.drawEllipse(x + sphere_size//4, y + sphere_size//4,
                              sphere_size//3, sphere_size//3)

            # S1-S4 label (upper half) + live phase value (lower half)
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.drawText(
                QRectF(x, y + sphere_size * 0.12, sphere_size, sphere_size * 0.5),
                Qt.AlignmentFlag.AlignCenter,
                sphere_id,
            )
            phase = self.sphere_phases.get(sphere_id)
            if phase is not None:
                painter.setFont(QFont("Arial", 6))
                painter.drawText(
                    QRectF(x, y + sphere_size * 0.58, sphere_size, sphere_size * 0.35),
                    Qt.AlignmentFlag.AlignCenter,
                    f"{phase:.0f}°",
                )

class ExcitationPanel(QWidget):
    """
    Widget for configuring Excitation Parameters.
    Migrated to Interface V2 with proper domain model.
    """
    # Signals
    excitation_changed = Signal(str, float, float, float)  # mode, level_s1_s2, level_s3_s4, freq
    link_toggled = Signal(bool)  # linked
    lock_in_detection_toggled = Signal(bool)  # enabled
    compensation_toggle_requested = Signal(bool)  # enabled
    lock_in_phase_offset_changed = Signal(float)  # degrees
    lock_in_phase_offset_reset_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Style — same compact metrics as MotionPanelCompact so both panels
        # end up the same height when docked side by side.
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
            QLabel {
                color: #DDD;
                font-size: 11px;
            }
            QCheckBox { font-size: 11px; }
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
            QComboBox {
                background-color: #353535;
                color: white;
                border: 1px solid #2E86AB;
                border-radius: 3px;
                padding: 2px;
                font-size: 11px;
                min-width: 100px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #353535;
                color: white;
                selection-background-color: #2E86AB;
            }
            QDoubleSpinBox {
                background-color: #222;
                color: #FFF;
                border: 1px solid #444;
                padding: 2px;
                font-size: 11px;
            }
        """)

        group = QGroupBox("Excitation Configuration")
        v_layout = QVBoxLayout(group)
        v_layout.setSpacing(8)
        v_layout.setContentsMargins(10, 15, 10, 10)

        # Top row: Mode + Frequency selection
        top_row = QHBoxLayout()
        top_row.setSpacing(20)

        mode_selector_layout = QVBoxLayout()
        mode_selector_layout.setSpacing(2)
        mode_label = QLabel("Mode:")
        mode_label.setStyleSheet("font-weight: bold; color: white;")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "X Direction",
            "Y Direction",
            "Circular +",
            "Circular -",
            "Custom"
        ])
        mode_selector_layout.addWidget(mode_label)
        mode_selector_layout.addWidget(self.mode_combo)
        top_row.addLayout(mode_selector_layout)

        freq_selector_layout = QVBoxLayout()
        freq_selector_layout.setSpacing(2)
        freq_label = QLabel("Frequency:")
        freq_label.setStyleSheet("font-weight: bold; color: white;")
        freq_row = QHBoxLayout()
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(0.0, 1000000.0)
        self.freq_spin.setValue(1000.0)
        self.freq_spin.setDecimals(0)
        freq_unit = QLabel("Hz")
        freq_unit.setStyleSheet("color: #AAA;")
        freq_row.addWidget(self.freq_spin)
        freq_row.addWidget(freq_unit)
        freq_selector_layout.addWidget(freq_label)
        freq_selector_layout.addLayout(freq_row)
        top_row.addLayout(freq_selector_layout)
        top_row.addStretch()

        v_layout.addLayout(top_row)

        # Main column: excitation levels, then the sphere visualization, then
        # the Lock-In Detection controls — stacked vertically so the panel
        # stays narrow (it used to be three side-by-side columns).
        main_column = QVBoxLayout()
        main_column.setSpacing(8)

        # --- Level Control — S1/S2 and S3/S4 (same S1..S4 naming as
        # Motion Control) are each an independent DDS differential pair.
        levels_column = QVBoxLayout()
        levels_column.setSpacing(8)

        s1_s2_layout = QHBoxLayout()
        s1_s2_label = QLabel("Level S1-S2:")
        s1_s2_label.setStyleSheet("font-weight: bold; color: white;")
        self.level_s1_s2_spin = QDoubleSpinBox()
        self.level_s1_s2_spin.setRange(0.0, 100.0)
        self.level_s1_s2_spin.setValue(0.0)
        self.level_s1_s2_spin.setDecimals(0)
        s1_s2_unit = QLabel("%")
        s1_s2_unit.setStyleSheet("color: #AAA;")
        s1_s2_layout.addWidget(s1_s2_label)
        s1_s2_layout.addWidget(self.level_s1_s2_spin)
        s1_s2_layout.addWidget(s1_s2_unit)
        s1_s2_layout.addStretch()
        levels_column.addLayout(s1_s2_layout)

        s3_s4_layout = QHBoxLayout()
        s3_s4_label = QLabel("Level S3-S4:")
        s3_s4_label.setStyleSheet("font-weight: bold; color: white;")
        self.level_s3_s4_spin = QDoubleSpinBox()
        self.level_s3_s4_spin.setRange(0.0, 100.0)
        self.level_s3_s4_spin.setValue(0.0)
        self.level_s3_s4_spin.setDecimals(0)
        s3_s4_unit = QLabel("%")
        s3_s4_unit.setStyleSheet("color: #AAA;")
        s3_s4_layout.addWidget(s3_s4_label)
        s3_s4_layout.addWidget(self.level_s3_s4_spin)
        s3_s4_layout.addWidget(s3_s4_unit)
        s3_s4_layout.addStretch()
        levels_column.addLayout(s3_s4_layout)

        # Checked by default: reproduces the previous single-"Level" behavior
        # (one shared value applied to both DDS).
        self.link_checkbox = QCheckBox("Link S1-S2 = S3-S4")
        self.link_checkbox.setChecked(True)
        levels_column.addWidget(self.link_checkbox)

        main_column.addLayout(levels_column)

        # --- Sphere Visualization (now also shows each S1-S4 phase), centered
        self.sphere_widget = SphereVisualizationWidget()
        main_column.addWidget(
            self.sphere_widget, alignment=Qt.AlignmentFlag.AlignHCenter
        )

        # --- Lock-In Detection command controls, with the phase
        # offset display below them.
        lock_in_column = QVBoxLayout()
        lock_in_column.setSpacing(8)

        lock_in_header = QHBoxLayout()
        lock_in_header.setSpacing(6)
        self.lock_in_checkbox = QCheckBox("Enable Lock-In Detection")
        self.lock_in_checkbox.setChecked(True)
        lock_in_header.addWidget(self.lock_in_checkbox)

        # Small warning symbol, hidden unless the synchronous-detection
        # (ch3/ch4) gain is below the recommended default — kept minimal
        # (a single glyph + tooltip) rather than a verbose inline message.
        self.lock_in_gain_warning_label = QLabel("⚠")
        self.lock_in_gain_warning_label.setStyleSheet(
            "color: #E6B800; font-weight: bold; font-size: 14px;"
        )
        self.lock_in_gain_warning_label.setToolTip(
            "Le gain de l'excitation synchrone (DDS3/DDS4) est en dessous "
            "de la valeur recommandée par défaut."
        )
        self.lock_in_gain_warning_label.setVisible(False)
        lock_in_header.addWidget(self.lock_in_gain_warning_label)
        lock_in_header.addStretch()
        lock_in_column.addLayout(lock_in_header)

        self.compensation_checkbox = QCheckBox("Compensation active")
        lock_in_column.addWidget(self.compensation_checkbox)

        # Editable in degrees (not raw registers) — lets the user tune the
        # lock-in reference directly from this panel instead of going
        # through Hardware Advanced Config's raw phase field. Locked
        # (disabled) unless compensation is active — see set_compensation_state.
        offset_layout = QHBoxLayout()
        offset_label = QLabel("Lock-in Detection Phase Offset:")
        offset_label.setStyleSheet("font-weight: bold; color: white;")
        self.lock_in_offset_spin = QDoubleSpinBox()
        self.lock_in_offset_spin.setRange(0.0, 360.0)
        # AD9106 phase register is 16-bit over 360° -> 1 register increment =
        # 360/65536 ~= 0.0055°. 3 decimals is the coarsest display precision
        # that still reflects a single hardware step (2 decimals can round
        # two adjacent register values to the same displayed number).
        self.lock_in_offset_spin.setDecimals(3)
        self.lock_in_offset_spin.setSingleStep(360.0 / 65536)
        self.lock_in_offset_spin.setWrapping(True)
        self.lock_in_offset_spin.setEnabled(False)
        offset_unit = QLabel("°")
        offset_unit.setStyleSheet("color: #AAA;")
        self.lock_in_offset_reset_btn = QPushButton("Reset")
        self.lock_in_offset_reset_btn.setToolTip(
            "Réinitialiser au point de calibration enregistré pour la fréquence courante."
        )
        offset_layout.addWidget(self.lock_in_offset_spin)
        offset_layout.addWidget(offset_unit)
        offset_layout.addWidget(self.lock_in_offset_reset_btn)
        offset_layout.addStretch()
        # Label above its controls rather than beside them: the label is long
        # and was the widest single row of the panel.
        lock_in_column.addWidget(offset_label)
        lock_in_column.addLayout(offset_layout)

        main_column.addLayout(lock_in_column)

        v_layout.addLayout(main_column)

        layout.addWidget(group)
        layout.addStretch()

    def _connect_signals(self):
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        self.level_s1_s2_spin.valueChanged.connect(self._on_level_s1_s2_value_changed)
        self.level_s3_s4_spin.valueChanged.connect(self._on_level_s3_s4_value_changed)
        self.level_s1_s2_spin.editingFinished.connect(self._emit_changed)
        self.level_s3_s4_spin.editingFinished.connect(self._emit_changed)
        self.link_checkbox.toggled.connect(self._on_link_toggled)
        self.freq_spin.editingFinished.connect(self._emit_changed)
        self.lock_in_checkbox.toggled.connect(self._on_lock_in_detection_toggled)
        self.compensation_checkbox.toggled.connect(self._on_compensation_toggled)
        self.lock_in_offset_spin.editingFinished.connect(self._on_lock_in_offset_editing_finished)
        self.lock_in_offset_reset_btn.clicked.connect(self.lock_in_phase_offset_reset_requested.emit)

    def _on_mode_changed(self, mode_text: str):
        self._emit_changed()

    def _on_level_s1_s2_value_changed(self, value: float):
        if self.link_checkbox.isChecked():
            self._set_spin_value(self.level_s3_s4_spin, value)

    def _on_level_s3_s4_value_changed(self, value: float):
        if self.link_checkbox.isChecked():
            self._set_spin_value(self.level_s1_s2_spin, value)

    def _set_spin_value(self, spin: QDoubleSpinBox, value: float):
        """Set a spinbox value without re-triggering the link mirroring (recursion guard)."""
        if spin.value() == value:
            return
        spin.blockSignals(True)
        spin.setValue(value)
        spin.blockSignals(False)

    def _on_link_toggled(self, checked: bool):
        self.link_toggled.emit(checked)
        if not checked:
            return
        s1_s2 = self.level_s1_s2_spin.value()
        s3_s4 = self.level_s3_s4_spin.value()
        if s1_s2 != s3_s4:
            aligned = min(s1_s2, s3_s4)
            self._set_spin_value(self.level_s1_s2_spin, aligned)
            self._set_spin_value(self.level_s3_s4_spin, aligned)
            self._emit_changed()

    def set_link_state(self, linked: bool):
        """Update the "Link" checkbox from external state (Hardware Advanced
        Config tab) without re-emitting link_toggled — same blockSignals
        pattern as set_state()."""
        if self.link_checkbox.isChecked() == linked:
            return
        self.link_checkbox.blockSignals(True)
        self.link_checkbox.setChecked(linked)
        self.link_checkbox.blockSignals(False)

    def _on_lock_in_detection_toggled(self, checked: bool):
        self.lock_in_detection_toggled.emit(checked)

    def _set_lock_in_checkbox_state(self, enabled: bool):
        """Sync the "Enable Lock-In Detection" checkbox from service state
        (gain at/above default) without re-emitting lock_in_detection_toggled."""
        if self.lock_in_checkbox.isChecked() == enabled:
            return
        self.lock_in_checkbox.blockSignals(True)
        self.lock_in_checkbox.setChecked(enabled)
        self.lock_in_checkbox.blockSignals(False)

    def _on_compensation_toggled(self, checked: bool):
        self.compensation_toggle_requested.emit(checked)

    def set_compensation_state(self, enabled: bool):
        """Sync the "Compensation active" checkbox from external state
        (Hardware Advanced Config's own compensation checkbox, or service
        state) without re-emitting compensation_toggle_requested. Also locks
        the phase offset field: it's only meaningful to hand-edit while
        compensation is actively managing ch3 — otherwise use Hardware
        Advanced Config directly."""
        if self.compensation_checkbox.isChecked() != enabled:
            self.compensation_checkbox.blockSignals(True)
            self.compensation_checkbox.setChecked(enabled)
            self.compensation_checkbox.blockSignals(False)
        self.lock_in_offset_spin.setEnabled(enabled)

    def _on_lock_in_offset_editing_finished(self):
        self.lock_in_phase_offset_changed.emit(self.lock_in_offset_spin.value())

    def _emit_changed(self):
        mode = self._text_to_mode_code(self.mode_combo.currentText())
        level_s1_s2 = self.level_s1_s2_spin.value()
        level_s3_s4 = self.level_s3_s4_spin.value()
        freq = self.freq_spin.value()
        self.excitation_changed.emit(mode, level_s1_s2, level_s3_s4, freq)

    def _text_to_mode_code(self, text: str) -> str:
        """Convert combo text to mode code."""
        mapping = {
            "X Direction": "X_DIR",
            "Y Direction": "Y_DIR",
            "Circular +": "CIRCULAR_PLUS",
            "Circular -": "CIRCULAR_MINUS",
            "Custom": "CUSTOM"
        }
        return mapping.get(text, "X_DIR")

    def set_state(self, mode_code: str, level_s1_s2: float, level_s3_s4: float, freq: float):
        """Update UI based on external state. Does not touch the "Link" checkbox —
        that's a local UI preference, not part of the domain state."""
        self.blockSignals(True)
        self.mode_combo.blockSignals(True)
        self.level_s1_s2_spin.blockSignals(True)
        self.level_s3_s4_spin.blockSignals(True)
        self.freq_spin.blockSignals(True)

        try:
            # Convert mode code to text
            mode_text_mapping = {
                "X_DIR": "X Direction",
                "Y_DIR": "Y Direction",
                "CIRCULAR_PLUS": "Circular +",
                "CIRCULAR_MINUS": "Circular -",
                "CUSTOM": "Custom"
            }
            mode_text = mode_text_mapping.get(mode_code, "X Direction")

            current_idx = self.mode_combo.findText(mode_text)
            if current_idx >= 0:
                self.mode_combo.setCurrentIndex(current_idx)

            self.level_s1_s2_spin.setValue(level_s1_s2)
            self.level_s3_s4_spin.setValue(level_s3_s4)
            self.freq_spin.setValue(freq)
        finally:
            self.mode_combo.blockSignals(False)
            self.level_s1_s2_spin.blockSignals(False)
            self.level_s3_s4_spin.blockSignals(False)
            self.freq_spin.blockSignals(False)
            self.blockSignals(False)

    def set_synchronous_detection_state(
        self, s1, s2, s3, s4, delta_phi_corrige, lock_in_gain_below_default
    ) -> None:
        """Update the Lock-In Detection display/controls. Pure primitives in —
        no domain/application types cross into this view."""
        self.sphere_widget.set_sphere_phases(s1, s2, s3, s4)
        if delta_phi_corrige is not None and self.lock_in_offset_spin.value() != delta_phi_corrige % 360.0:
            self.lock_in_offset_spin.setValue(delta_phi_corrige % 360.0)
        self.lock_in_gain_warning_label.setVisible(lock_in_gain_below_default)
        self._set_lock_in_checkbox_state(not lock_in_gain_below_default)
