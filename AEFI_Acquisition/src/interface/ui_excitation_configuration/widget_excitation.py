"""
Excitation Configuration Widget - Interface Layer

Responsibility:
- UI for configuring field excitation (mode, level, frequency)
- Visual feedback for current excitation state
- Sphere visualization for excitation direction

Rationale:
- Provides intuitive interface for excitation control
- Separates UI concerns from business logic
- Reusable component for dashboard integration
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QGroupBox,
    QDoubleSpinBox, QPushButton, QGridLayout
)
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt6.QtCore import Qt, pyqtSignal
from .presenter_excitation import ExcitationPresenter
from domain.value_objects.excitation.excitation_mode import ExcitationMode


class SphereVisualizationWidget(QWidget):
    """Widget de visualisation des 4 sphères avec coloration selon excitation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(100, 80)
        self.setMaximumSize(130, 100)
        
        # État des sphères : mapping 1,2,3,4 → DDS1, DDS1_bar, DDS2, DDS2_bar
        self.sphere_colors = {
            'out1': QColor(100, 100, 100),  # Out1 = DDS1 (Gris par défaut)
            'out2': QColor(100, 100, 100),  # Out2 = DDS1_bar 
            'out3': QColor(100, 100, 100),  # Out3 = DDS2
            'out4': QColor(100, 100, 100)   # Out4 = DDS2_bar
        }
        
    def set_excitation_mode(self, mode: str):
        """Met à jour les couleurs selon le mode d'excitation"""
        red = QColor(230, 57, 70)    # Rouge
        blue = QColor(46, 134, 171)  # Bleu
        gray = QColor(120, 120, 120) # Gris neutre
        
        if mode == "Y_DIR":
            # DDS1 et DDS2 en phase → excitation Y
            self.sphere_colors = {
                'out1': red,     # Out1=DDS1 : Rouge (phase 0°)
                'out2': blue,   # Out2=DDS1_bar : Bleu (phase 180°)
                'out3': blue,   # Out3=DDS2 : Bleu (phase 180°)
                'out4': red     # Out4=DDS2_bar : Rouge (phase 0°)
            }
        elif mode == "X_DIR":
            # DDS1 et DDS2 en opposition → excitation X
            self.sphere_colors = {
                'out1': red,     # Out1=DDS1 : Rouge (phase 0°)
                'out2': blue,   # Out2=DDS1_bar : Bleu (phase 180°)
                'out3': red,     # Out3=DDS2 : Rouge (phase 0°)
                'out4': blue     # Out4=DDS2_bar : Bleu (phase 180°)
            }
        elif mode == "CIRCULAR_PLUS":
            # Excitation circulaire + (DDS2 en quadrature +90°)
            light_red = QColor(255, 150, 150)
            light_blue = QColor(150, 150, 255)
            self.sphere_colors = {
                'out1': red,        # Out1=DDS1 : Rouge (phase 0°)
                'out2': blue,       # Out2=DDS1_bar : Bleu (phase 180°)
                'out3': light_red,  # Out3=DDS2 : Rouge clair (phase 90°)
                'out4': light_blue  # Out4=DDS2_bar : Bleu clair (phase 270°)
            }
        elif mode == "CIRCULAR_MINUS":
            # Excitation circulaire - (DDS2 en quadrature -90°)
            light_red = QColor(255, 150, 150)
            light_blue = QColor(150, 150, 255)
            self.sphere_colors = {
                'out1': red,        # Out1=DDS1 : Rouge (phase 0°)
                'out2': blue,       # Out2=DDS1_bar : Bleu (phase 180°)
                'out3': light_blue, # Out3=DDS2 : Bleu clair (phase -90°)
                'out4': light_red   # Out4=DDS2_bar : Rouge clair (phase 90°)
            }
        elif mode == "CUSTOM":
            # Mode custom : couleurs neutres mais distinguées du mode off
            custom_color = QColor(180, 180, 120)  # Jaune-gris pour indiquer un mode personnalisé
            self.sphere_colors = {k: custom_color for k in self.sphere_colors.keys()}
        else:
            # Mode off ou inconnu
            self.sphere_colors = {k: gray for k in self.sphere_colors.keys()}
        
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Disposition 2x2 des sphères
        sphere_size = min(w//3, h//3)
        margin_x = (w - 2*sphere_size) // 3
        margin_y = (h - 2*sphere_size) // 3
        
        # Positions des sphères selon mapping 1,2,3,4
        positions = {
            'out1': (margin_x, margin_y + sphere_size + margin_y),               # Out1: Bas gauche
            'out2': (margin_x + sphere_size + margin_x, margin_y),               # Out2: Haut droite  
            'out3': (margin_x, margin_y),                                        # Out3: Haut gauche
            'out4': (margin_x + sphere_size + margin_x, margin_y + sphere_size + margin_y) # Out4: Bas droite
        }
        
        # Dessiner les sphères
        for out_name, (x, y) in positions.items():
            color = self.sphere_colors[out_name]
            
            # Sphère avec effet 3D
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.drawEllipse(x, y, sphere_size, sphere_size)
            
            # Highlight pour effet 3D
            highlight_color = QColor(255, 255, 255, 100)
            painter.setBrush(QBrush(highlight_color))
            painter.setPen(QPen(Qt.PenStyle.NoPen))
            painter.drawEllipse(x + sphere_size//4, y + sphere_size//4, 
                              sphere_size//3, sphere_size//3)
        
        # Labels Out1, Out2, Out3, Out4
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        
        for out_name, (x, y) in positions.items():
            label = out_name.upper()  # OUT1, OUT2, OUT3, OUT4
            painter.drawText(x + 5, y + sphere_size + 15, label)


class ExcitationWidget(QWidget):
    """
    Widget for excitation configuration.
    """

    def __init__(self, presenter: ExcitationPresenter, parent=None):
        super().__init__(parent)
        self.presenter = presenter
        
        self._build_ui()
        self._connect_signals()
        self._update_from_service()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        
        group = QGroupBox("Excitation Configuration")
        v_layout = QVBoxLayout(group)
        v_layout.setSpacing(4)
        v_layout.setContentsMargins(8, 8, 8, 8)
        
        # Mode Selection + Visualization
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(8)
        
        # Mode ComboBox
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
        self.mode_combo.setStyleSheet("""
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
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
            }
            QComboBox QAbstractItemView {
                background-color: #353535;
                color: white;
                selection-background-color: #2E86AB;
            }
        """)
        
        mode_selector_layout = QVBoxLayout()
        mode_selector_layout.setSpacing(2)
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
        self.level_spin.setDecimals(1)
        self.level_spin.setSuffix(" %")
        level_layout.addWidget(level_label)
        level_layout.addWidget(self.level_spin)
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
        self.freq_spin.setSuffix(" Hz")
        freq_layout.addWidget(freq_label)
        freq_layout.addWidget(self.freq_spin)
        freq_layout.addStretch()
        v_layout.addLayout(freq_layout)
        
        # Apply Button
        self.btn_apply = QPushButton("Apply")
        self.btn_apply.setStyleSheet("""
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
        v_layout.addWidget(self.btn_apply)
        
        layout.addWidget(group)
        layout.addStretch()

    def _connect_signals(self):
        """Connect UI signals to presenter methods."""
        self.btn_apply.clicked.connect(self._on_apply_clicked)
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        
        # Connect presenter signals to UI updates
        self.presenter.excitation_updated.connect(self._on_excitation_updated)
        self.presenter.excitation_error.connect(self._on_excitation_error)

    def _connect_presenter(self):
        """Connect presenter signals (already done in _connect_signals)."""
        pass

    def _on_apply_clicked(self):
        """Handle Apply button click."""
        mode = self._get_mode_from_combo()
        level = self.level_spin.value()
        frequency = self.freq_spin.value()
        
        self.presenter.set_excitation(mode, level, frequency)

    def _on_mode_changed(self, mode_text: str):
        """Handle mode combo change (update visualization)."""
        mode_code = self._text_to_mode_code(mode_text)
        self.sphere_widget.set_excitation_mode(mode_code)

    def _on_excitation_updated(self, mode_name: str, level_percent: float, frequency: float):
        """Handle excitation update from presenter."""
        # Update UI to reflect current state
        mode_text = self._mode_name_to_text(mode_name)
        if mode_text in [self.mode_combo.itemText(i) for i in range(self.mode_combo.count())]:
            self.mode_combo.setCurrentText(mode_text)
        
        self.level_spin.setValue(level_percent)
        self.freq_spin.setValue(frequency)
        
        # Update visualization
        self.sphere_widget.set_excitation_mode(mode_name)

    def _on_excitation_error(self, error_message: str):
        """Handle excitation error from presenter."""
        # Could show a message box or status label
        print(f"[ExcitationWidget] Error: {error_message}")

    def _update_from_service(self):
        """Update UI from current service state."""
        params = self.presenter.get_current_parameters()
        mode_name = params.mode.name
        level = params.level.value
        frequency = params.frequency
        
        self._on_excitation_updated(mode_name, level, frequency)

    def _get_mode_from_combo(self) -> ExcitationMode:
        """Get ExcitationMode enum from combo box selection."""
        text = self.mode_combo.currentText()
        mapping = {
            "X Direction": ExcitationMode.X_DIR,
            "Y Direction": ExcitationMode.Y_DIR,
            "Circular +": ExcitationMode.CIRCULAR_PLUS,
            "Circular -": ExcitationMode.CIRCULAR_MINUS,
            "Custom": ExcitationMode.CUSTOM
        }
        return mapping.get(text, ExcitationMode.X_DIR)

    def _text_to_mode_code(self, text: str) -> str:
        """Convert combo text to mode code for visualization."""
        mapping = {
            "X Direction": "X_DIR",
            "Y Direction": "Y_DIR",
            "Circular +": "CIRCULAR_PLUS",
            "Circular -": "CIRCULAR_MINUS",
            "Custom": "CUSTOM"
        }
        return mapping.get(text, "X_DIR")

    def _mode_name_to_text(self, mode_name: str) -> str:
        """Convert mode name to combo text."""
        mapping = {
            "X_DIR": "X Direction",
            "Y_DIR": "Y Direction",
            "CIRCULAR_PLUS": "Circular +",
            "CIRCULAR_MINUS": "Circular -",
            "CUSTOM": "Custom"
        }
        return mapping.get(mode_name, "X Direction")

