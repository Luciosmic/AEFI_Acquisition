from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QDoubleSpinBox, QComboBox, QCheckBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygon
from PySide6.QtCore import Qt, Signal, QRectF, QPoint

class SphereVisualizationWidget(QWidget):
    """
    Visualization of the 4 excitation spheres, coloring each sphere (S1-S4)
    based on excitation mode (see domain.shared_kernel.excitation.value_objects
    .sphere_id.SphereId for the confirmed DDS-channel/direct-output wiring).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(100, 80)
        self.setMaximumSize(130, 100)

        # Sphere states, keyed by sphere id (S1-S4, matches domain SphereId)
        self.sphere_colors = {
            'S1': QColor(100, 100, 100),  # Gray default
            'S2': QColor(100, 100, 100),
            'S3': QColor(100, 100, 100),
            'S4': QColor(100, 100, 100)
        }

    def set_excitation_mode(self, mode: str):
        """Update colors based on excitation mode."""
        red = QColor(230, 57, 70)     # Red
        blue = QColor(46, 134, 171)   # Blue
        gray = QColor(120, 120, 120)  # Neutral gray
        
        # Colors reflect the real, oscilloscope-confirmed phase at each sphere
        # (see SphereId): S4 and S3 are channel 1 (DDS1 generator, phase
        # always hardcoded to 0° by the adapter regardless of mode) — they
        # never change. Only S1 and S2 (channel 2, DDS2 generator) vary with mode.
        if mode == "Y_DIR":
            # channel 2 phase=0° → S1(complementary)=180°, S2(direct)=0°
            self.sphere_colors = {
                'S4': red,    # 0°
                'S3': blue,   # 180°
                'S1': blue,   # 180°
                'S2': red     # 0°
            }
        elif mode == "X_DIR":
            # channel 2 phase=180° → S1(complementary)=0°, S2(direct)=180°
            self.sphere_colors = {
                'S4': red,    # 0°
                'S3': blue,   # 180°
                'S1': red,    # 0°
                'S2': blue    # 180°
            }
        elif mode == "CIRCULAR_PLUS":
            # channel 2 phase=90° → S1(complementary)=270°, S2(direct)=90°
            light_red = QColor(255, 150, 150)
            light_blue = QColor(150, 150, 255)
            self.sphere_colors = {
                'S4': red,        # 0°
                'S3': blue,       # 180°
                'S1': light_blue, # 270°
                'S2': light_red   # 90°
            }
        elif mode == "CIRCULAR_MINUS":
            # channel 2 phase=270° → S1(complementary)=90°, S2(direct)=270°
            light_red = QColor(255, 150, 150)
            light_blue = QColor(150, 150, 255)
            self.sphere_colors = {
                'S4': red,        # 0°
                'S3': blue,       # 180°
                'S1': light_red,  # 90°
                'S2': light_blue  # 270°
            }
        elif mode == "CUSTOM":
            # Custom mode: neutral but distinct from off
            custom_color = QColor(180, 180, 120)  # Yellow-gray
            self.sphere_colors = {k: custom_color for k in self.sphere_colors.keys()}
        else:
            # Off or unknown mode
            self.sphere_colors = {k: gray for k in self.sphere_colors.keys()}
        
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
            color = self.sphere_colors[sphere_id]

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

            # S1-S4 label, centered in the sphere
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.drawText(
                QRectF(x, y, sphere_size, sphere_size),
                Qt.AlignmentFlag.AlignCenter,
                sphere_id,
            )

class ExcitationPanel(QWidget):
    """
    Widget for configuring Excitation Parameters.
    Migrated to Interface V2 with proper domain model.
    """
    # Signals
    excitation_changed = Signal(str, float, float, float)  # mode, level_s1_s2, level_s3_s4, freq

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()
        
        # Initialize sphere visualization with default mode
        default_mode = self._text_to_mode_code(self.mode_combo.currentText())
        self.sphere_widget.set_excitation_mode(default_mode)

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
            QComboBox {
                background-color: #353535;
                color: white;
                border: 1px solid #2E86AB;
                border-radius: 4px;
                padding: 5px;
                min-width: 120px;
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
                padding: 4px;
            }
        """)

        group = QGroupBox("Excitation Configuration")
        v_layout = QVBoxLayout(group)
        v_layout.setSpacing(10)
        v_layout.setContentsMargins(15, 20, 15, 15)

        # Mode Selection + Visualization
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(8)
        
        # Mode Selection
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
        mode_layout.addLayout(mode_selector_layout)
        
        # Sphere Visualization
        self.sphere_widget = SphereVisualizationWidget()
        mode_layout.addWidget(self.sphere_widget, stretch=1)
        
        v_layout.addLayout(mode_layout)

        # Level Control — S1/S2 and S3/S4 (same S1..S4 naming as Motion Control)
        # are each an independent DDS differential pair — two independent gains.
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
        v_layout.addLayout(s1_s2_layout)

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
        v_layout.addLayout(s3_s4_layout)

        # Checked by default: reproduces the previous single-"Level" behavior
        # (one shared value applied to both DDS).
        self.link_checkbox = QCheckBox("Link S1-S2 = S3-S4")
        self.link_checkbox.setChecked(True)
        v_layout.addWidget(self.link_checkbox)

        # Frequency Control
        freq_layout = QHBoxLayout()
        freq_label = QLabel("Frequency:")
        freq_label.setStyleSheet("font-weight: bold; color: white;")
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(0.0, 1000000.0)
        self.freq_spin.setValue(1000.0)
        self.freq_spin.setDecimals(0)
        freq_unit = QLabel("Hz")
        freq_unit.setStyleSheet("color: #AAA;")
        freq_layout.addWidget(freq_label)
        freq_layout.addWidget(self.freq_spin)
        freq_layout.addWidget(freq_unit)
        freq_layout.addStretch()
        v_layout.addLayout(freq_layout)
        
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

    def _on_mode_changed(self, mode_text: str):
        mode_code = self._text_to_mode_code(mode_text)
        self.sphere_widget.set_excitation_mode(mode_code)
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
        if not checked:
            return
        s1_s2 = self.level_s1_s2_spin.value()
        s3_s4 = self.level_s3_s4_spin.value()
        if s1_s2 != s3_s4:
            aligned = min(s1_s2, s3_s4)
            self._set_spin_value(self.level_s1_s2_spin, aligned)
            self._set_spin_value(self.level_s3_s4_spin, aligned)
            self._emit_changed()

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

            # Update visualization
            self.sphere_widget.set_excitation_mode(mode_code)
        finally:
            self.mode_combo.blockSignals(False)
            self.level_s1_s2_spin.blockSignals(False)
            self.level_s3_s4_spin.blockSignals(False)
            self.freq_spin.blockSignals(False)
            self.blockSignals(False)
