#!/usr/bin/env python3
"""
Composant DDSControl avancé pour l'onglet réglages avancés.
Réutilise le code de AD9106_ADS131A04_GUI.py avec adaptation pour l'interface v2.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QGroupBox, QSpinBox, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from typing import Tuple

# Couleurs modernes (cohérentes avec l'interface principale)
COLORS = {
    'primary_blue': '#2E86AB',
    'accent_red': '#E63946',
    'success_green': '#2A9D8F',
    'warning_orange': '#F77F00',
    'info_purple': '#A23B72',
    'dark_bg': '#353535',
    'darker_bg': '#252525',
    'text_white': '#FFFFFF',
    'border_gray': '#555555'
}


class DDSControlAdvanced(QWidget):
    """Widget de contrôle avancé pour un seul DDS."""

    # Signaux pour synchronisation avec l'onglet principal
    gain_changed = pyqtSignal(int, int)  # dds_number, gain_value
    phase_changed = pyqtSignal(int, int)  # dds_number, phase_value
    frequency_changed = pyqtSignal(float)  # frequency_hz

    def __init__(self, dds_number: int, acquisition_manager, parent: QWidget = None):
        super().__init__(parent)
        self.dds_number = dds_number
        self.acquisition_manager = acquisition_manager
        self.mode = "AC"  # Toujours AC pour compatibilité
        self.init_ui()
        # Initialisation automatique en mode AC
        self._init_dds_mode()

    def init_ui(self):
        """Interface moderne et sobre"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # Titre sobre
        title = QLabel(f"DDS {self.dds_number}")
        title.setStyleSheet(f"""
            font-weight: bold; 
            font-size: 18px; 
            color: {COLORS['text_white']};
            padding: 10px;
            border-bottom: 2px solid {COLORS['text_white']};
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Contrôles de paramètres
        self.gain_spin = self._create_parameter_box("Gain", 0, 16376, layout)
        self.gain_spin.setStyleSheet(self.gain_spin.styleSheet() + "\nQSpinBox::up-button, QSpinBox::down-button { width: 0; height: 0; border: none; }")
        self.phase_spin, self.phase_deg_spin = self._create_phase_box(layout)
        self.phase_spin.setStyleSheet(self.phase_spin.styleSheet() + "\nQSpinBox::up-button, QSpinBox::down-button { width: 0; height: 0; border: none; }")
        self.phase_deg_spin.setStyleSheet(self.phase_deg_spin.styleSheet() + "\nQSpinBox::up-button, QSpinBox::down-button { width: 0; height: 0; border: none; }")

    def _create_parameter_box(self, name: str, min_val: int, max_val: int, parent_layout: QVBoxLayout) -> QSpinBox:
        group = QGroupBox(name)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLORS['text_white']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                color: {COLORS['text_white']};
                background-color: {COLORS['darker_bg']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {COLORS['text_white']};
            }}
        """)
        
        layout = QGridLayout(group)
        spin_box = QSpinBox()
        spin_box.setRange(min_val, max_val)
        spin_box.setMinimumWidth(120)
        spin_box.setFixedHeight(36)
        spin_box.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS['dark_bg']};
                color: {COLORS['text_white']};
                border: 1px solid {COLORS['text_white']};
                border-radius: 4px;
                padding: 5px;
                font-size: 16px;
                min-width: 120px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {COLORS['text_white']};
                border-radius: 2px;
            }}
        """)
        spin_box.editingFinished.connect(self.apply_parameters)
        
        label_val = QLabel("Valeur:")
        label_val.setStyleSheet(f"color: {COLORS['text_white']};")
        layout.addWidget(label_val, 0, 0)
        layout.addWidget(spin_box, 0, 1)
        label_range = QLabel(f"({min_val}-{max_val})")
        label_range.setStyleSheet(f"color: {COLORS['text_white']};")
        layout.addWidget(label_range, 0, 2)
        parent_layout.addWidget(group)
        return spin_box

    def _create_phase_box(self, parent_layout: QVBoxLayout) -> Tuple[QSpinBox, QSpinBox]:
        group = QGroupBox("Phase")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLORS['text_white']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                color: {COLORS['text_white']};
                background-color: {COLORS['darker_bg']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {COLORS['text_white']};
            }}
        """)
        layout = QGridLayout(group)
        # SpinBox pour la valeur numérique
        spin_box = QSpinBox()
        spin_box.setRange(0, 65535)
        spin_box.setMinimumWidth(120)
        spin_box.setFixedHeight(36)
        spin_box.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS['dark_bg']};
                color: {COLORS['text_white']};
                border: 1px solid {COLORS['text_white']};
                border-radius: 4px;
                padding: 5px;
                font-size: 16px;
                min-width: 120px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {COLORS['text_white']};
                border-radius: 2px;
            }}
        """)
        spin_box.valueChanged.connect(self.on_phase_changed)
        spin_box.editingFinished.connect(self.apply_parameters)
        # SpinBox pour les degrés
        deg_spin_box = QSpinBox()
        deg_spin_box.setRange(0, 360)
        deg_spin_box.setSuffix("°")
        deg_spin_box.setMinimumWidth(80)
        deg_spin_box.setFixedHeight(36)
        deg_spin_box.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS['dark_bg']};
                color: {COLORS['text_white']};
                border: 1px solid {COLORS['text_white']};
                border-radius: 4px;
                padding: 5px;
                font-size: 16px;
                min-width: 80px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {COLORS['text_white']};
                border-radius: 2px;
            }}
        """)
        deg_spin_box.valueChanged.connect(self.on_deg_changed)
        deg_spin_box.editingFinished.connect(self.apply_parameters)
        # Layout compact, une seule ligne : Valeur | SpinBox | (0-65535) | Degrés | SpinBox | (0-360°)
        label_val = QLabel("Valeur :")
        label_val.setStyleSheet(f"color: {COLORS['text_white']};")
        layout.addWidget(label_val, 0, 0)
        layout.addWidget(spin_box, 0, 1)
        label_range = QLabel("(0-65535)")
        label_range.setStyleSheet(f"color: {COLORS['text_white']};")
        layout.addWidget(label_range, 0, 2)
        label_deg = QLabel("Degrés :")
        label_deg.setStyleSheet(f"color: {COLORS['text_white']};")
        layout.addWidget(label_deg, 0, 3)
        layout.addWidget(deg_spin_box, 0, 4)
        label_deg_range = QLabel("(0-360°)")
        label_deg_range.setStyleSheet(f"color: {COLORS['text_white']};")
        layout.addWidget(label_deg_range, 0, 5)
        parent_layout.addWidget(group)
        return spin_box, deg_spin_box

    def on_phase_changed(self, value: int):
        """Met à jour l'affichage des degrés quand la valeur numérique change."""
        degrees = round(value / 65535 * 360)
        self.phase_deg_spin.blockSignals(True)
        self.phase_deg_spin.setValue(degrees)
        self.phase_deg_spin.blockSignals(False)

    def on_deg_changed(self, degrees: int):
        """Met à jour la valeur numérique quand les degrés changent."""
        value = round(degrees * 65535 / 360)
        self.phase_spin.blockSignals(True)
        self.phase_spin.setValue(value)
        self.phase_spin.blockSignals(False)

    def _init_dds_mode(self):
        """Initialisation automatique en mode AC (centralisé via AcquisitionManager)"""
        # Note: L'initialisation du mode est maintenant gérée par AcquisitionManager
        # lors de la synchronisation initiale avec le hardware
        pass

    def apply_parameters(self):
        """Application des paramètres via AcquisitionManager (plus d'appel direct hardware)"""
        gain_value = self.gain_spin.value()
        phase_value = self.phase_spin.value()
        
        # Émission signaux pour synchronisation via AcquisitionManager
        self.gain_changed.emit(self.dds_number, gain_value)
        self.phase_changed.emit(self.dds_number, phase_value)

    def set_gain(self, gain_value: int):
        """Mise à jour externe du gain (pour synchronisation)"""
        self.gain_spin.blockSignals(True)
        self.gain_spin.setValue(gain_value)
        self.gain_spin.blockSignals(False)

    def set_phase(self, phase_value: int):
        """Mise à jour externe de la phase (pour synchronisation)"""
        self.phase_spin.blockSignals(True)
        self.phase_spin.setValue(phase_value)
        self.phase_spin.blockSignals(False)
        
        # Mise à jour manuelle de l'affichage des degrés
        degrees = round(phase_value / 65535 * 360)
        self.phase_deg_spin.blockSignals(True)
        self.phase_deg_spin.setValue(degrees)
        self.phase_deg_spin.blockSignals(False)

    def get_gain(self) -> int:
        """Récupération du gain actuel"""
        return self.gain_spin.value()

    def get_phase(self) -> int:
        """Récupération de la phase actuelle"""
        return self.phase_spin.value() 

    def set_interactive(self, enabled: bool):
        self.gain_spin.setEnabled(enabled)
        self.phase_spin.setEnabled(enabled)
        self.phase_deg_spin.setEnabled(enabled)
        # Désactive aussi le bouton appliquer si besoin
        for child in self.findChildren(QPushButton):
            child.setEnabled(enabled) 