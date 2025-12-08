#!/usr/bin/env python3
"""
Composant ADCControl avancé pour l'onglet réglages avancés.
Réutilise le code de AD9106_ADS131A04_GUI.py avec adaptation pour l'interface v2.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QGroupBox, QSpinBox, QGridLayout,
                             QCheckBox, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal

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


class ADCControlAdvanced(QWidget):
    """Widget de contrôle avancé pour les paramètres ADC."""

    # Signaux pour synchronisation
    gain_changed = pyqtSignal(int, int)  # channel, gain_value
    timing_changed = pyqtSignal(dict)  # timing_config
    reference_changed = pyqtSignal(dict)  # reference_config

    def __init__(self, acquisition_manager, parent: QWidget = None):
        super().__init__(parent)
        self.acquisition_manager = acquisition_manager
        self.init_ui()

    def init_ui(self):
        """Interface moderne avec thème sombre"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(15, 15, 15, 15)

        # # Titre
        # title = QLabel("⚙️ Configuration ADC ADS131A04")
        # title.setStyleSheet(f"""
        #     font-weight: bold; 
        #     font-size: 18px; 
        #     color: {COLORS['text_white']};
        #     padding: 10px;
        #     border-bottom: 2px solid {COLORS['text_white']};
        # """)
        # title.setAlignment(Qt.AlignCenter)
        # layout.addWidget(title)

        # Configuration principale des ADC
        layout.addWidget(self._create_timing_group())
        layout.addWidget(self._create_gain_group())
        layout.addWidget(self._create_reference_group())

        # Bouton d'application global
        apply_all_button = QPushButton("Appliquer la configuration complète")
        apply_all_button.setMinimumWidth(180)
        apply_all_button.setFixedHeight(32)
        apply_all_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['warning_orange']};
                color: {COLORS['text_white']};
                border: none;
                padding: 6px 12px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
                min-width: 180px;
            }}
            QPushButton:hover {{
                background-color: #e06b00;
            }}
            QPushButton:pressed {{
                background-color: #c55a00;
            }}
        """)
        apply_all_button.clicked.connect(self.apply_all_adc_config)
        layout.addWidget(apply_all_button)

        # Appliquer le style pour supprimer les flèches sur tous les QSpinBox
        for combo in self.gain_combos.values():
            combo.setStyleSheet(combo.styleSheet() + "\nQSpinBox::up-button, QSpinBox::down-button { width: 0; height: 0; border: none; }")

    def _create_timing_group(self) -> QGroupBox:
        """Groupe pour les paramètres de timing ADC"""
        group = QGroupBox("🕐 Paramètres de Timing")
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
        layout.setSpacing(15)

        # CLKIN divider ratio
        clkin_label = QLabel("CLKIN Divider Ratio:")
        clkin_label.setStyleSheet(f"color: {COLORS['text_white']}; font-weight: bold; font-size: 15px;")
        self.clkin_combo = QComboBox()
        self.clkin_combo.addItems(['2', '4', '6', '8', '10', '12', '14'])
        self.clkin_combo.setCurrentText('2')  # Valeur par défaut
        self.clkin_combo.setMinimumWidth(120)
        self.clkin_combo.setStyleSheet(self._combo_style(font_size=15))
        
        # ICLK divider ratio
        iclk_label = QLabel("ICLK Divider Ratio:")
        iclk_label.setStyleSheet(f"color: {COLORS['text_white']}; font-weight: bold; font-size: 15px;")
        self.iclk_combo = QComboBox()
        self.iclk_combo.addItems(['2', '4', '6', '8', '10', '12', '14'])
        self.iclk_combo.setCurrentText('2')  # Valeur par défaut
        self.iclk_combo.setMinimumWidth(120)
        self.iclk_combo.setStyleSheet(self._combo_style(font_size=15))

        # Oversampling ratio
        oversampling_label = QLabel("Oversampling Ratio:")
        oversampling_label.setStyleSheet(f"color: {COLORS['text_white']}; font-weight: bold; font-size: 15px;")
        self.oversampling_combo = QComboBox()
        oversampling_values = ['32', '48', '64', '96', '128', '192', '200', '256', '384', '400', '512', '768', '800', '1024', '2048', '4096']
        self.oversampling_combo.addItems(oversampling_values)
        self.oversampling_combo.setCurrentText('32')  # Valeur par défaut
        self.oversampling_combo.setMinimumWidth(120)
        self.oversampling_combo.setStyleSheet(self._combo_style(font_size=15))

        layout.addWidget(clkin_label, 0, 0)
        layout.addWidget(self.clkin_combo, 0, 1)
        layout.addWidget(iclk_label, 1, 0)
        layout.addWidget(self.iclk_combo, 1, 1)
        layout.addWidget(oversampling_label, 2, 0)
        layout.addWidget(self.oversampling_combo, 2, 1)

        return group

    def _create_gain_group(self) -> QGroupBox:
        """Groupe pour les gains des 4 canaux ADC"""
        group = QGroupBox("🔊 Gains ADC")
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
        layout.setSpacing(15)

        # Gains pour les 4 canaux
        self.gain_combos = {}
        gain_values = ['1', '2', '4', '8', '16']
        
        for i in range(1, 5):
            label = QLabel(f"ADC {i} Gain:")
            label.setStyleSheet(f"color: {COLORS['text_white']}; font-weight: bold; font-size: 15px;")
            
            combo = QComboBox()
            combo.addItems(gain_values)
            combo.setCurrentText('1')  # Gain par défaut
            combo.setMinimumWidth(100)
            combo.setStyleSheet(self._combo_style(font_size=15))
            combo.currentTextChanged.connect(lambda text, ch=i: self._on_gain_changed(ch, int(text)))
            
            self.gain_combos[i] = combo
            
            row = (i - 1) // 2
            col = ((i - 1) % 2) * 2
            layout.addWidget(label, row, col)
            layout.addWidget(combo, row, col + 1)

        return group

    def _create_reference_group(self) -> QGroupBox:
        """Groupe pour la configuration des références"""
        group = QGroupBox("🎯 Configuration Références")
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
        layout.setSpacing(15)

        # Negative Reference
        self.negative_ref_check = QCheckBox("Negative Reference")
        self.negative_ref_check.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS['text_white']};
                font-weight: bold;
                font-size: 15px;
                min-width: 160px;
            }}
            QCheckBox::indicator {{
                width: 22px;
                height: 22px;
            }}
            QCheckBox::indicator:unchecked {{
                background-color: {COLORS['dark_bg']};
                border: 2px solid {COLORS['text_white']};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS['accent_red']};
                border: 2px solid {COLORS['accent_red']};
                border-radius: 3px;
            }}
        """)

        # High Resolution
        self.high_res_check = QCheckBox("High Resolution")
        self.high_res_check.setChecked(True)  # Par défaut activé
        self.high_res_check.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS['text_white']};
                font-weight: bold;
                font-size: 15px;
                min-width: 160px;
            }}
            QCheckBox::indicator {{
                width: 22px;
                height: 22px;
            }}
            QCheckBox::indicator:unchecked {{
                background-color: {COLORS['dark_bg']};
                border: 2px solid {COLORS['text_white']};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS['accent_red']};
                border: 2px solid {COLORS['accent_red']};
                border-radius: 3px;
            }}
        """)

        # Reference Voltage
        ref_voltage_label = QLabel("Reference Voltage:")
        ref_voltage_label.setStyleSheet(f"color: {COLORS['text_white']}; font-weight: bold; font-size: 15px;")
        self.ref_voltage_combo = QComboBox()
        self.ref_voltage_combo.addItems(['2.442V', '4.0V'])
        self.ref_voltage_combo.setCurrentText('4.0V')  # Par défaut
        self.ref_voltage_combo.setMinimumWidth(120)
        self.ref_voltage_combo.setStyleSheet(self._combo_style(font_size=15))

        # Reference Selection
        ref_selection_label = QLabel("Reference Selection:")
        ref_selection_label.setStyleSheet(f"color: {COLORS['text_white']}; font-weight: bold; font-size: 15px;")
        self.ref_selection_combo = QComboBox()
        self.ref_selection_combo.addItems(['External', 'Internal'])
        self.ref_selection_combo.setCurrentText('Internal')  # Par défaut
        self.ref_selection_combo.setMinimumWidth(120)
        self.ref_selection_combo.setStyleSheet(self._combo_style(font_size=15))

        layout.addWidget(self.negative_ref_check, 0, 0, 1, 2)
        layout.addWidget(self.high_res_check, 1, 0, 1, 2)
        layout.addWidget(ref_voltage_label, 2, 0)
        layout.addWidget(self.ref_voltage_combo, 2, 1)
        layout.addWidget(ref_selection_label, 3, 0)
        layout.addWidget(self.ref_selection_combo, 3, 1)

        return group

    def _combo_style(self, font_size=13) -> str:
        """Style commun pour les ComboBox"""
        return f"""
            QComboBox {{
                background-color: {COLORS['darker_bg']};
                color: {COLORS['text_white']};
                border: 1px solid {COLORS['text_white']};
                border-radius: 4px;
                padding: 5px;
                min-width: 100px;
                font-size: {font_size}px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {COLORS['text_white']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['darker_bg']};
                color: {COLORS['text_white']};
                selection-background-color: {COLORS['warning_orange']};
                font-size: {font_size}px;
            }}
        """

    def _on_gain_changed(self, channel: int, gain: int):
        """Callback pour changement de gain ADC (centralisé via AcquisitionManager)"""
        # Émission signal pour synchronisation via AcquisitionManager
        self.gain_changed.emit(channel, gain)

    def apply_all_adc_config(self):
        """Applique toute la configuration ADC (centralisé via AcquisitionManager)"""
        try:
            # 1. Configuration CLKIN divider
            clkin_value = int(self.clkin_combo.currentText())
            
            # 2. Configuration ICLK divider et Oversampling
            iclk_value = int(self.iclk_combo.currentText())
            oversampling_value = int(self.oversampling_combo.currentText())
            
            # 3. Configuration des gains
            gains = {}
            for channel, combo in self.gain_combos.items():
                gain_value = int(combo.currentText())
                gains[channel] = gain_value
            
            # 4. Configuration des références
            negative_ref = self.negative_ref_check.isChecked()
            high_res = self.high_res_check.isChecked()
            ref_voltage = 1 if self.ref_voltage_combo.currentText() == '4.0V' else 0
            ref_selection = 1 if self.ref_selection_combo.currentText() == 'Internal' else 0

            # Émission signaux pour synchronisation via AcquisitionManager
            timing_config = {
                'clkin': clkin_value,
                'iclk': iclk_value,
                'oversampling': oversampling_value
            }
            self.timing_changed.emit(timing_config)

            reference_config = {
                'negative_ref': negative_ref,
                'high_res': high_res,
                'ref_voltage': ref_voltage,
                'ref_selection': ref_selection
            }
            self.reference_changed.emit(reference_config)
            
            # Émission des gains ADC
            for channel, gain in gains.items():
                self.gain_changed.emit(channel, gain)

            # Message de succès
            QMessageBox.information(self, "✅ Succès", "Configuration ADC envoyée à AcquisitionManager!")
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Erreur", f"Erreur lors de l'application: {str(e)}")

    def set_gain(self, channel: int, gain: int):
        """Mise à jour externe du gain (pour synchronisation)"""
        if channel in self.gain_combos:
            self.gain_combos[channel].blockSignals(True)
            self.gain_combos[channel].setCurrentText(str(gain))
            self.gain_combos[channel].blockSignals(False)

    def get_gains(self) -> dict:
        """Récupération de tous les gains actuels"""
        return {channel: int(combo.currentText()) for channel, combo in self.gain_combos.items()}

    def set_enabled(self, enabled: bool):
        """Active/désactive tous les contrôles"""
        for combo in self.gain_combos.values():
            combo.setEnabled(enabled)
        self.clkin_combo.setEnabled(enabled)
        self.iclk_combo.setEnabled(enabled)
        self.oversampling_combo.setEnabled(enabled)
        self.negative_ref_check.setEnabled(enabled)
        self.high_res_check.setEnabled(enabled)
        self.ref_voltage_combo.setEnabled(enabled)
        self.ref_selection_combo.setEnabled(enabled) 

    def set_interactive(self, enabled: bool):
        # Désactive tous les QComboBox, QSpinBox, QCheckBox, QPushButton
        for child in self.findChildren((QComboBox, QSpinBox, QCheckBox, QPushButton)):
            child.setEnabled(enabled) 