from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox, QDoubleSpinBox, QComboBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PySide6.QtCore import Qt, Signal

class SphereVisualizationWidget(QWidget):
    """
    Visualization of 4 sphere outputs with coloring based on excitation mode.
    Shows phase relationships between OUT1-4 (DDS1, DDS1_bar, DDS2, DDS2_bar).
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(100, 80)
        self.setMaximumSize(130, 100)
        
        # Sphere states: mapping out1,2,3,4 → DDS outputs
        self.sphere_colors = {
            'out1': QColor(100, 100, 100),  # Out1 = DDS1 (Gray default)
            'out2': QColor(100, 100, 100),  # Out2 = DDS1_bar 
            'out3': QColor(100, 100, 100),  # Out3 = DDS2
            'out4': QColor(100, 100, 100)   # Out4 = DDS2_bar
        }
        
    def set_excitation_mode(self, mode: str):
        """Update colors based on excitation mode."""
        red = QColor(230, 57, 70)     # Red
        blue = QColor(46, 134, 171)   # Blue
        gray = QColor(120, 120, 120)  # Neutral gray
        
        if mode == "Y_DIR":
            # DDS1 and DDS2 in phase → Y excitation
            self.sphere_colors = {
                'out1': red,    # Out1=DDS1: Red (phase 0°)
                'out2': blue,   # Out2=DDS1_bar: Blue (phase 180°)
                'out3': blue,   # Out3=DDS2: Blue (phase 180°)
                'out4': red     # Out4=DDS2_bar: Red (phase 0°)
            }
        elif mode == "X_DIR":
            # DDS1 and DDS2 in opposition → X excitation
            self.sphere_colors = {
                'out1': red,    # Out1=DDS1: Red (phase 0°)
                'out2': blue,   # Out2=DDS1_bar: Blue (phase 180°)
                'out3': red,    # Out3=DDS2: Red (phase 0°)
                'out4': blue    # Out4=DDS2_bar: Blue (phase 180°)
            }
        elif mode == "CIRCULAR_PLUS":
            # Circular + excitation (DDS2 at +90° quadrature)
            light_red = QColor(255, 150, 150)
            light_blue = QColor(150, 150, 255)
            self.sphere_colors = {
                'out1': red,        # Out1=DDS1: Red (phase 0°)
                'out2': blue,       # Out2=DDS1_bar: Blue (phase 180°)
                'out3': light_red,  # Out3=DDS2: Light red (phase 90°)
                'out4': light_blue  # Out4=DDS2_bar: Light blue (phase 270°)
            }
        elif mode == "CIRCULAR_MINUS":
            # Circular - excitation (DDS2 at -90° quadrature)
            light_red = QColor(255, 150, 150)
            light_blue = QColor(150, 150, 255)
            self.sphere_colors = {
                'out1': red,        # Out1=DDS1: Red (phase 0°)
                'out2': blue,       # Out2=DDS1_bar: Blue (phase 180°)
                'out3': light_blue, # Out3=DDS2: Light blue (phase -90°)
                'out4': light_red   # Out4=DDS2_bar: Light red (phase 90°)
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
        
        # Sphere positions (1,2,3,4 mapping)
        positions = {
            'out1': (margin_x, margin_y + sphere_size + margin_y),               # Out1: Bottom left
            'out2': (margin_x + sphere_size + margin_x, margin_y),               # Out2: Top right  
            'out3': (margin_x, margin_y),                                        # Out3: Top left
            'out4': (margin_x + sphere_size + margin_x, margin_y + sphere_size + margin_y) # Out4: Bottom right
        }
        
        # Draw spheres
        for out_name, (x, y) in positions.items():
            color = self.sphere_colors[out_name]
            
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
        
        # Labels Out1, Out2, Out3, Out4
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        


class ExcitationPanel(QWidget):
    """
    Widget for configuring Excitation Parameters.
    Migrated to Interface V2 with proper domain model.
    """
    # Signals
    excitation_changed = Signal(str, float, float)  # mode, level, freq

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()
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
            QPushButton {
                background-color: #2E86AB;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1E6A8A;
            }
            QPushButton:pressed {
                background-color: #0E4A6A;
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

        # Level Control
        level_layout = QHBoxLayout()
        level_label = QLabel("Level:")
        level_label.setStyleSheet("font-weight: bold; color: white;")
        self.level_spin = QDoubleSpinBox()
        self.level_spin.setRange(0.0, 100.0)
        self.level_spin.setValue(0.0)
        self.level_spin.setDecimals(0)
        level_unit = QLabel("%")
        level_unit.setStyleSheet("color: #AAA;")
        level_layout.addWidget(level_label)
        level_layout.addWidget(self.level_spin)
        level_layout.addWidget(level_unit)
        level_layout.addStretch()
        v_layout.addLayout(level_layout)

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
        
        # Apply Button
        self.btn_apply = QPushButton("Apply")
        v_layout.addWidget(self.btn_apply)

        layout.addWidget(group)
        layout.addStretch()

    def _connect_signals(self):
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        self.btn_apply.clicked.connect(self._on_apply_clicked)

    def _on_mode_changed(self, mode_text: str):
        """Update visualization when mode changes."""
        mode_code = self._text_to_mode_code(mode_text)
        self.sphere_widget.set_excitation_mode(mode_code)

    def _on_apply_clicked(self):
        """Emit configuration change."""
        mode = self._text_to_mode_code(self.mode_combo.currentText())
        level = self.level_spin.value()
        freq = self.freq_spin.value()
        self.excitation_changed.emit(mode, level, freq)

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

    def set_state(self, mode_code: str, level: float, freq: float):
        """Update UI based on external state."""
        self.blockSignals(True)
        self.mode_combo.blockSignals(True)
        self.level_spin.blockSignals(True)
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
            
            self.level_spin.setValue(level)
            self.freq_spin.setValue(freq)
            
            # Update visualization
            self.sphere_widget.set_excitation_mode(mode_code)
        finally:
            self.mode_combo.blockSignals(False)
            self.level_spin.blockSignals(False)
            self.freq_spin.blockSignals(False)
            self.blockSignals(False)
