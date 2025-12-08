#!/usr/bin/env python3
"""
Interface d'Acquisition AD9106/ADS131A04 - Phase 1
Interface moderne avec 2 modes : Temps Réel (Exploration) vs Export (Mesures)

Backend validé avec AcquisitionManager et ModeController.
Interface 3 paramètres : Gain DDS, Fréq Hz, N_avg
"""

# =========================
# Imports & Constantes Globales
# =========================

import sys, os

from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QComboBox, QTabWidget,
                             QPushButton, QGroupBox, QSpinBox, QStatusBar,
                             QDoubleSpinBox, QMessageBox, QGridLayout, QStyle,
                             QCheckBox, QProgressBar, QFileDialog, QLineEdit)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPalette, QColor, QFont
import pyqtgraph as pg
from contextlib import contextmanager
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog



# Import des composants backend validés
try:
    # Import du Manager
    from components.AD9106_ADS131A04_acquisition_manager import AcquisitionManager

    # Import des widgets pour le contrôle des DDS et ADC
    from components.AD9106_AdvancedControl_Widget import DDSControlAdvanced
    from components.ADS131A04_AdvancedControl_Widget import ADCControlAdvanced

    # Import des sous-modules à instancier et passer en paramètre à l'AcquisitionManager
    from components.ADS131A04_Converter_Module import ADCConverter
    from instruments.AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator
    from components.AD9106_ADS131A04_DataBuffer_Module import AdaptiveDataBuffer, AcquisitionSample
    from components.AD9106_ADS131A04_CSVexporter_Module import CSVExporter

except ImportError as e:
    print(f"Impossible d'importer les composants backend : {e}")
    sys.exit(1)

# Couleurs modernes
COLORS = {
    'primary_blue': '#2E86AB',
    'accent_red': '#E63946',
    'success_green': '#2A9D8F',
    'warning_orange': '#F77F00',
    'info_purple': '#A23B72',
    'dark_bg': '#353535',
    'darker_bg': '#252525',
    'text_white': '#FFFFFF',
    'border_gray': '#555555',
    'adc1_blue': '#4A90E2',
    'adc2_green': '#7ED321'
}

# =========================
# WIDGETS DE CONFIGURATION
# =========================

# --- MainParametersMainParametersConfigWidget ---
class MainParametersConfigWidget(QWidget):
    """Widget de configuration 3 paramètres (Gain DDS, Fréq Hz, N_avg)
    Toute synchronisation passe par le modèle central AcquisitionManager (plus de signaux croisés).
    """
    
    # Signal communication UI → Manager
    configuration_changed = pyqtSignal(dict)
    
    # Bornes et valeurs par défaut (à adapter si besoin)
    GAIN_MIN, GAIN_MAX = 0, 16376
    FREQ_MIN, FREQ_MAX = 0.1, 1_000_000.0
    NAVG_MIN, NAVG_MAX = 1, 1000 

    # =========================
    # Initialisation de l'UI
    # =========================
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """Interface inspirée LabVIEW"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Titre
        title = QLabel("Configuration Acquisition")
        title.setStyleSheet(f"""
            font-weight: bold; 
            font-size: 16px; 
            color: {COLORS['text_white']};
            padding: 10px;
            border-bottom: 2px solid {COLORS['primary_blue']};
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Groupe configuration
        config_group = QGroupBox()
        config_group.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid {COLORS['border_gray']};
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
                background-color: {COLORS['darker_bg']};
            }}
        """)
        
        config_layout = QGridLayout(config_group)
        config_layout.setSpacing(15)
        
        # Gain DDS
        gain_label = QLabel("Gain DDS 1 & 2:")
        gain_label.setStyleSheet(f"color: {COLORS['text_white']}; font-weight: bold;")
        self.gain_spinbox = QSpinBox()
        self.gain_spinbox.setRange(self.GAIN_MIN, self.GAIN_MAX)
        self.gain_spinbox.setValue(5000)
        self.gain_spinbox.setStyleSheet(self._spinbox_style())
        self.gain_spinbox.valueChanged.connect(self._on_config_changed)
        self.gain_spinbox.setStyleSheet(self.gain_spinbox.styleSheet() + "\nQSpinBox::up-button, QSpinBox::down-button { width: 0; height: 0; border: none; }")
        
        # Label warning DDS
        self.gain_warning_label = QLabel("")
        self.gain_warning_label.setStyleSheet(f"color: {COLORS['accent_red']}; font-weight: bold;")
        self.gain_warning_label.setVisible(False)
        
        # Fréquence
        freq_label = QLabel("Fréq (Hz):")
        freq_label.setStyleSheet(f"color: {COLORS['text_white']}; font-weight: bold;")
        self.freq_spinbox = QDoubleSpinBox()
        self.freq_spinbox.setRange(self.FREQ_MIN, self.FREQ_MAX)
        self.freq_spinbox.setValue(1000)
        self.freq_spinbox.setDecimals(0)
        self.freq_spinbox.setStyleSheet(self._spinbox_style())
        self.freq_spinbox.valueChanged.connect(self._on_config_changed)
        self.freq_spinbox.setStyleSheet(self.freq_spinbox.styleSheet() + "\nQDoubleSpinBox::up-button, QDoubleSpinBox::down-button { width: 0; height: 0; border: none; }")
        
        # N_avg
        navg_label = QLabel("N_avg:")
        navg_label.setStyleSheet(f"color: {COLORS['text_white']}; font-weight: bold;")
        self.navg_spinbox = QSpinBox()
        self.navg_spinbox.setRange(self.NAVG_MIN, self.NAVG_MAX)
        self.navg_spinbox.setValue(10)
        self.navg_spinbox.setStyleSheet(self._spinbox_style())
        self.navg_spinbox.valueChanged.connect(self._on_config_changed)
        self.navg_spinbox.setStyleSheet(self.navg_spinbox.styleSheet() + "\nQSpinBox::up-button, QSpinBox::down-button { width: 0; height: 0; border: none; }")
        
        # Layout
        config_layout.addWidget(gain_label, 0, 0)
        config_layout.addWidget(self.gain_spinbox, 0, 1)
        config_layout.addWidget(self.gain_warning_label, 1, 0, 1, 3)
        config_layout.addWidget(freq_label, 2, 0)
        config_layout.addWidget(self.freq_spinbox, 2, 1)
        config_layout.addWidget(navg_label, 3, 0)
        config_layout.addWidget(self.navg_spinbox, 3, 1)
        
        layout.addWidget(config_group)
        
    def _spinbox_style(self) -> str:
        """Style pour les SpinBox"""
        return f"""
            QSpinBox, QDoubleSpinBox {{
                background-color: {COLORS['dark_bg']};
                border: 2px solid {COLORS['border_gray']};
                border-radius: 5px;
                padding: 8px;
                color: {COLORS['text_white']};
                font-weight: bold;
                font-size: 14px;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border-color: {COLORS['primary_blue']};
            }}
            QSpinBox:disabled, QDoubleSpinBox:disabled {{
                background-color: {COLORS['darker_bg']};
                color: {COLORS['border_gray']};
                border-color: {COLORS['border_gray']};
            }}
        """

    # =========================
    # LOGIQUE MONTANTE UI --> MANAGER
    # =========================
    def _on_config_changed(self):
        """Émission signal configuration changée vers le modèle central"""
        config = {
            'gain_dds': self.gain_spinbox.value(),
            'freq_hz': self.freq_spinbox.value(),
            'n_avg': self.navg_spinbox.value()
        }
        if self.validate_config(config):
            self.configuration_changed.emit(config)
    
    def _on_frequency_changed(self):
        """Application de la fréquence à tous les DDS (centralisé via AcquisitionManager, aucun appel direct hardware)"""
        freq_hz = self.freq_spinbox.value()
        config = {'freq_hz': freq_hz}
        if self.validate_config(config):
            if hasattr(self, 'acquisition_manager') and self.acquisition_manager is not None:
                self.acquisition_manager.update_configuration({'freq_hz': freq_hz})

    # =========================
    # LOGIQUE DESCENDANTE MANAGER --> UI
    # =========================

    def set_configuration(self, config: dict):
        """Aucune propagation, MAJ UI uniquement, jamais de signal ni de callback ici."""
        with self._block_all_signals():
            if 'gain_dds' in config:
                self.gain_spinbox.setValue(config['gain_dds'])
            if 'freq_hz' in config:
                self.freq_spinbox.setValue(config['freq_hz'])
            if 'n_avg' in config:
                self.navg_spinbox.setValue(config['n_avg'])
    
    def set_enabled(self, enabled: bool):
        """Active/désactive les widgets selon le mode"""
        self.gain_spinbox.setEnabled(enabled)
        self.freq_spinbox.setEnabled(enabled)
        self.navg_spinbox.setEnabled(enabled)

    def show_gain_warning(self, show: bool):
        """Affiche ou masque le warning DDS1/DDS2"""
        if show:
            self.gain_warning_label.setText("Les gains DDS1 et DDS2 sont différents !")
            self.gain_warning_label.setVisible(True)
        else:
            self.gain_warning_label.setVisible(False)

    # =========================
    # UTILITAIRES INTERNES WIDGET
    # =========================
    
    @contextmanager
    def _block_all_signals(self):
        """Context manager pour bloquer tous les signaux des spinbox."""
        self.gain_spinbox.blockSignals(True)
        self.freq_spinbox.blockSignals(True)
        self.navg_spinbox.blockSignals(True)
        try:
            yield
        finally:
            self.gain_spinbox.blockSignals(False)
            self.freq_spinbox.blockSignals(False)
            self.navg_spinbox.blockSignals(False)
    
    def validate_config(self, config: dict) -> bool:
        """Valide la configuration, affiche une erreur si invalide."""
        gain = config.get('gain_dds', self.gain_spinbox.value())
        freq = config.get('freq_hz', self.freq_spinbox.value())
        n_avg = config.get('n_avg', self.navg_spinbox.value())
        if not (self.GAIN_MIN <= gain <= self.GAIN_MAX):
            QMessageBox.critical(self, "Erreur configuration", f"Gain DDS hors bornes [{self.GAIN_MIN}, {self.GAIN_MAX}] : {gain}")
            return False
        if not (self.FREQ_MIN <= freq <= self.FREQ_MAX):
            QMessageBox.critical(self, "Erreur configuration", f"Fréquence hors bornes [{self.FREQ_MIN}, {self.FREQ_MAX}] : {freq}")
            return False
        if not (self.NAVG_MIN <= n_avg <= self.NAVG_MAX):
            QMessageBox.critical(self, "Erreur configuration", f"N_avg hors bornes [{self.NAVG_MIN}, {self.NAVG_MAX}] : {n_avg}")
            return False
        return True
    
    def get_configuration(self) -> dict:
        """Retourne la configuration actuelle"""
        return {
            'gain_dds': self.gain_spinbox.value(),
            'freq_hz': self.freq_spinbox.value(),
            'n_avg': self.navg_spinbox.value()
        }
    
# --- AdvancedSettingsWidget ---
class AdvancedSettingsWidget(QWidget):
    """Widget principal pour l'onglet réglages avancés
    Toute synchronisation passe par le modèle central AcquisitionManager (plus de signaux croisés).
    """
    
    # Bornes et valeurs par défaut (à adapter si besoin)
    GAIN_MIN, GAIN_MAX = 0, 16376
    FREQ_MIN, FREQ_MAX = 0.1, 1_000_000.0
    PHASE_MIN, PHASE_MAX = 0, 360
    

    def __init__(self, acquisition_manager, parent=None):
        super().__init__(parent)
        self.acquisition_manager = acquisition_manager
        self.dds_controls = {}
        self.init_ui()
        
    # =========================
    # Initialisation de l'UI
    # =========================
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        # Zone DDS (gauche)
        dds_group = QGroupBox("Configuration AD9106")
        dds_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLORS['primary_blue']};
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
                color: {COLORS['text_white']};
                background-color: {COLORS['darker_bg']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {COLORS['primary_blue']};
            }}
        """)
        dds_vlayout = QVBoxLayout(dds_group)
        dds_vlayout.setSpacing(8)
        dds_vlayout.setContentsMargins(8, 8, 8, 8)
        # Ajout du contrôle de fréquence directement en haut, sans QGroupBox supplémentaire
        freq_bar = self._create_control_bar()
        freq_bar.setStyleSheet("margin-bottom: 0px; margin-top: 0px; border: none; background: transparent;")
        dds_vlayout.addWidget(freq_bar)
        dds_layout = QGridLayout()
        dds_layout.setSpacing(8)
        for i in range(1, 5):
            dds_control = DDSControlAdvanced(i, self.acquisition_manager)
            self.dds_controls[i] = dds_control
            # Connexion des signaux DDS vers AcquisitionManager
            dds_control.gain_changed.connect(self._on_dds_gain_changed)
            dds_control.phase_changed.connect(self._on_dds_phase_changed)
            row = (i - 1) // 2
            col = (i - 1) % 2
            dds_layout.addWidget(dds_control, row, col)
        dds_vlayout.addLayout(dds_layout)
        layout.addWidget(dds_group, 2)

        # Zone ADC (droite)
        adc_group = QGroupBox("Configuration ADS131A04")
        adc_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLORS['accent_red']};
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
                color: {COLORS['text_white']};
                background-color: {COLORS['darker_bg']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {COLORS['accent_red']};
            }}
        """)
        adc_vlayout = QVBoxLayout(adc_group)
        adc_vlayout.setSpacing(8)
        adc_vlayout.setContentsMargins(8, 8, 8, 8)
        # Correction : création de adc_control avant ajout
        self.adc_control = ADCControlAdvanced(self.acquisition_manager)
        # Connexion du signal ADC vers AcquisitionManager
        self.adc_control.gain_changed.connect(self._on_adc_gain_changed)
        adc_vlayout.addWidget(self.adc_control)
        layout.addWidget(adc_group, 1)
        
    def _create_control_bar(self) -> QGroupBox:
        """Barre de contrôle partagée"""
        group = QGroupBox("🎮 Contrôles Principaux")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLORS['primary_blue']};
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
                color: {COLORS['text_white']};
                background-color: {COLORS['darker_bg']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {COLORS['primary_blue']};
            }}
        """)
        
        layout = QHBoxLayout(group)
        layout.setSpacing(15)
        
        # Contrôle de fréquence globale
        freq_label = QLabel("📡 Fréquence globale:")
        freq_label.setStyleSheet(f"color: {COLORS['text_white']}; font-weight: bold;")
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(0.1, 1_000_000)
        self.freq_spin.setValue(1000)
        self.freq_spin.setSuffix(" Hz")
        self.freq_spin.setStyleSheet(f"""
            QDoubleSpinBox {{
                background-color: {COLORS['dark_bg']};
                color: {COLORS['text_white']};
                border: 1px solid {COLORS['border_gray']};
                border-radius: 4px;
                padding: 5px;
                min-width: 120px;
            }}
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                background-color: {COLORS['primary_blue']};
                border-radius: 2px;
            }}
        """)
        self.freq_spin.editingFinished.connect(self._on_frequency_changed)
        
        self.set_freq_button = QPushButton("✅ Appliquer à tous DDS")
        self.set_freq_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary_blue']};
                color: {COLORS['text_white']};
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #1e6b8a;
            }}
        """)
        self.set_freq_button.clicked.connect(self._on_frequency_changed)
        
        layout.addWidget(freq_label)
        layout.addWidget(self.freq_spin)
        layout.addWidget(self.set_freq_button)
        layout.addStretch()
        
        return group
    
    # =========================
    # SIGNAUX MONTANT UI --> MANAGER
    # =========================
    def _on_frequency_changed(self):
        """Application de la fréquence à tous les DDS (centralisé via AcquisitionManager, aucun appel direct hardware)"""
        freq_hz = self.freq_spin.value()
        config = {'freq_hz': freq_hz}
        if self.validate_config(config):
            if hasattr(self, 'acquisition_manager') and self.acquisition_manager is not None:
                self.acquisition_manager.update_configuration({'freq_hz': freq_hz})
    
    def _on_dds_gain_changed(self, dds_number: int, gain_value: int):
        """Gestion du changement de gain DDS (centralisé via AcquisitionManager)"""
        if hasattr(self, 'acquisition_manager') and self.acquisition_manager is not None:
            if dds_number == 1:
                self.acquisition_manager.update_configuration({'gain_dds': gain_value})
            elif dds_number == 2:
                self.acquisition_manager.update_configuration({'gain_dds': gain_value})
            elif dds_number == 3:
                self.acquisition_manager.update_configuration({'gain_dds3': gain_value})
            elif dds_number == 4:
                self.acquisition_manager.update_configuration({'gain_dds4': gain_value})
    
    def _on_dds_phase_changed(self, dds_number: int, phase_value: int):
        """Gestion du changement de phase DDS (centralisé via AcquisitionManager)"""
        if hasattr(self, 'acquisition_manager') and self.acquisition_manager is not None:
            if dds_number == 1:
                self.acquisition_manager.update_configuration({'phase_dds1': phase_value})
            elif dds_number == 2:
                self.acquisition_manager.update_configuration({'phase_dds2': phase_value})
            elif dds_number == 3:
                self.acquisition_manager.update_configuration({'phase_dds3': phase_value})
            elif dds_number == 4:
                self.acquisition_manager.update_configuration({'phase_dds4': phase_value})
    
    def _on_adc_gain_changed(self, channel: int, gain_value: int):
        """Callback pour changement de gain ADC : passe par update_configuration du manager."""
        self.acquisition_manager.update_configuration({f'adc_gain_ch{channel}': gain_value})
    
    # =========================
    # SIGNAUX DESCENDANT MANAGER --> UI
    # =========================

    def set_frequency(self, freq_hz: float):
        """Mise à jour externe de la fréquence (Aucune synchronisation croisée, tout passe par le modèle central)"""
        with self._block_all_signals():
            self.freq_spin.setValue(freq_hz)
    
    def set_dds_gain(self, dds_number: int, gain_value: int):
        """Mise à jour externe du gain DDS (centralisé via AcquisitionManager, aucun appel direct hardware)"""
        if dds_number in self.dds_controls:
            with self._block_all_signals():
                self.dds_controls[dds_number].set_gain(gain_value)
        # Toute modification utilisateur doit passer par update_configuration si besoin
    
    def set_dds_phase(self, dds_number: int, phase_value: int):
        """Mise à jour externe de la phase DDS (centralisé via AcquisitionManager, aucun appel direct hardware)"""
        if dds_number in self.dds_controls:
            with self._block_all_signals():
                self.dds_controls[dds_number].set_phase(phase_value)
        # Toute modification utilisateur doit passer par update_configuration si besoin
    
    def set_adc_gain(self, channel: int, gain_value: int):
        """Mise à jour externe du gain ADC (centralisé via AcquisitionManager, aucun appel direct hardware)"""
        with self._block_all_signals():
            self.adc_control.set_gain(channel, gain_value)
        # Toute modification utilisateur doit passer par update_configuration si besoin
    
    def set_enabled(self, enabled: bool):
        """Active/désactive tous les contrôles selon le mode"""
        for dds_control in self.dds_controls.values():
            dds_control.set_interactive(enabled)
        self.adc_control.set_interactive(enabled)
        self.freq_spin.setEnabled(enabled)
        self.set_freq_button.setEnabled(enabled)

    # =========================
    # UTILITAIRES INTERNES WIDGETS
    # =========================
    @contextmanager
    def _block_all_signals(self):
        """Context manager pour bloquer tous les signaux des widgets avancés."""
        self.freq_spin.blockSignals(True)
        for dds_control in self.dds_controls.values():
            dds_control.blockSignals(True)
        self.adc_control.blockSignals(True)
        try:
            yield
        finally:
            self.freq_spin.blockSignals(False)
            for dds_control in self.dds_controls.values():
                dds_control.blockSignals(False)
            self.adc_control.blockSignals(False)

    def validate_config(self, config: dict) -> bool:
        """Valide la configuration avancée, affiche une erreur si invalide."""
        gain = config.get('gain_dds', None)
        freq = config.get('freq_hz', None)
        phase = config.get('phase', None)
        if gain is not None and not (self.GAIN_MIN <= gain <= self.GAIN_MAX):
            QMessageBox.critical(self, "Erreur configuration avancée", f"Gain DDS hors bornes [{self.GAIN_MIN}, {self.GAIN_MAX}] : {gain}")
            return False
        if freq is not None and not (self.FREQ_MIN <= freq <= self.FREQ_MAX):
            QMessageBox.critical(self, "Erreur configuration avancée", f"Fréquence hors bornes [{self.FREQ_MIN}, {self.FREQ_MAX}] : {freq}")
            return False
        if phase is not None and not (self.PHASE_MIN <= phase <= self.PHASE_MAX):
            QMessageBox.critical(self, "Erreur configuration avancée", f"Phase DDS hors bornes [{self.PHASE_MIN}, {self.PHASE_MAX}] : {phase}")
            return False
        return True
    
# --- ExportWidget
class ExportWidget(QWidget):
    """Widget complet de gestion de l'export : contrôles + configuration chemin/nom de fichier + statut."""
    start_export = pyqtSignal(dict)  # dict de config export
    stop_export = pyqtSignal()
    config_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    # =========================
    # Initialisation de l'UI
    # =========================
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Groupe boutons export
        self.export_group = QGroupBox("Export CSV")
        self.export_group.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid {COLORS['primary_blue']};
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
                background-color: {COLORS['darker_bg']};
                color: {COLORS['text_white']};
                font-weight: bold;
            }}
        """)
        export_layout = QVBoxLayout(self.export_group)  # Changer en QVBoxLayout pour empiler boutons + configs
        # Ligne boutons
        btns_layout = QHBoxLayout()
        self.start_btn = QPushButton("🟢 Démarrer Export")
        self.start_btn.setStyleSheet(self._button_style(COLORS['warning_orange']))
        self.start_btn.clicked.connect(self._emit_start_export)
        self.stop_btn = QPushButton("🔴 Arrêter Export")
        self.stop_btn.setStyleSheet(self._button_style(COLORS['accent_red']))
        self.stop_btn.clicked.connect(self.stop_export.emit)
        btns_layout.addWidget(self.start_btn)
        btns_layout.addWidget(self.stop_btn)
        btns_layout.addStretch()
        export_layout.addLayout(btns_layout)
        # Configuration chemin/nom fichier (directement dans le QGroupBox)
        config_layout = QVBoxLayout()
        config_layout.setSpacing(8)
        config_layout.setContentsMargins(0, 0, 0, 0)
        # Data Path
        path_layout = QHBoxLayout()
        path_label = QLabel("Data Path")
        path_label.setStyleSheet("color: white; background: transparent; font-weight: bold;")
        self.path_edit = QLineEdit(os.path.expanduser("~\\Documents\\Data"))
        from PyQt5.QtWidgets import QStyle
        browse_btn = QPushButton()
        browse_btn.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        browse_btn.setFixedWidth(32)
        def browse():
            d = QFileDialog.getExistingDirectory(self, "Choisir le dossier d'export", self.path_edit.text())
            if d:
                self.path_edit.setText(d)
                self.emit_config()
        browse_btn.clicked.connect(browse)
        self.path_edit.editingFinished.connect(self.emit_config)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        # File Name
        file_layout = QHBoxLayout()
        file_label = QLabel("File Name")
        file_label.setStyleSheet("color: white; background: transparent; font-weight: bold;")
        self.file_edit = QLineEdit("Default")
        self.file_edit.editingFinished.connect(self.emit_config)
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_edit)
        # Assemble config
        config_layout.addLayout(path_layout)
        config_layout.addLayout(file_layout)
        export_layout.addLayout(config_layout)
        layout.addWidget(self.export_group)
        # Statut (en dehors du QGroupBox)
        self.export_status_label = QLabel("Export: ARRÊTÉ")
        self.export_status_label.setStyleSheet("color: white; font-weight: bold; font-size: 13px; padding: 4px;")
        self.export_status_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.export_status_label)

    def _button_style(self, color: str) -> str:
        return f"""
            QPushButton {{
                background-color: {color};
                color: {COLORS['text_white']};
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
            QPushButton:pressed {{
                background-color: {color}aa;
            }}
            QPushButton:disabled {{
                background-color: {COLORS['border_gray']};
                color: {COLORS['border_gray']};
            }}
        """

    # =========================
    # LOGIQUE MONTANTE UI --> MANAGER
    # =========================
    def _emit_start_export(self):
        self.start_export.emit(self.get_config())

    def get_config(self):
        return {
            'output_dir': self.path_edit.text().strip(),
            'filename_base': self.file_edit.text().strip(),
        }

    def emit_config(self):
        self.config_changed.emit(self.get_config())

    # =========================
    # LOGIQUE DESCENDANTE MANAGER --> UI
    # =========================

    def set_export_status(self, status: str):
        self.export_status_label.setText(f"Export: {status}")

    def set_enabled(self, enabled: bool):
        self.start_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(True)  # On doit toujours pouvoir arrêter l'export
        self.path_edit.setEnabled(enabled)
        self.file_edit.setEnabled(enabled)


# =========================
# WIDGETS D'AFFICHAGE EN DIRECT
# =========================

# --- NumericDisplayWidget ---
class NumericDisplayWidget(QWidget):
    """
    Real-time 8-channel numeric display widget.
    Displays live ADC values with unit conversion and sliding statistics.
    """

    # --- Constants ---
    DEFAULT_UNIT = "mV"
    DEFAULT_V_TO_VM_FACTOR = 63_600.0

    # Centralized channel metadata
    CHANNELS = [
        dict(name="ADC1_Ch1", index=1, color=COLORS['adc1_blue'], attr="adc1_ch1"),
        dict(name="ADC1_Ch2", index=2, color=COLORS['adc1_blue'], attr="adc1_ch2"),
        dict(name="ADC1_Ch3", index=3, color=COLORS['adc1_blue'], attr="adc1_ch3"),
        dict(name="ADC1_Ch4", index=4, color=COLORS['adc1_blue'], attr="adc1_ch4"),
        dict(name="ADC2_Ch1", index=5, color=COLORS['adc2_green'], attr="adc2_ch1"),
        dict(name="ADC2_Ch2", index=6, color=COLORS['adc2_green'], attr="adc2_ch2"),
        dict(name="ADC2_Ch3", index=7, color=COLORS['adc2_green'], attr="adc2_ch3"),
        dict(name="ADC2_Ch4", index=8, color=COLORS['adc2_green'], attr="adc2_ch4"),
    ]

    UNITS = ["Codes ADC", "V", "mV", "µV", "V/m"]

    # --- Initialization ---
    def __init__(self, acquisition_manager, parent=None):
        super().__init__(parent)
        self.acquisition_manager = acquisition_manager
        # self.adc_converter = ADCConverter()  # SUPPRIMÉ
        self.current_unit = self.DEFAULT_UNIT
        self.v_to_vm_factor = self.DEFAULT_V_TO_VM_FACTOR
        self._build_ui()

    # --- UI Construction ---
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addLayout(self._build_header())
        layout.addLayout(self._build_grid())

    def _build_header(self):
        title = QLabel("Valeurs Live")
        title.setStyleSheet(
            f"font-weight: bold; font-size: 16px; color: {COLORS['text_white']};"
        )

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(self.UNITS)
        self.unit_combo.setCurrentText(self.current_unit)
        self.unit_combo.setStyleSheet(self._combo_style())
        self.unit_combo.currentTextChanged.connect(self._on_unit_changed)

        factor_label = QLabel("Facteur V→V/m:")
        factor_label.setStyleSheet(f"color: {COLORS['text_white']};")

        self.factor_spinbox = QDoubleSpinBox()
        self.factor_spinbox.setRange(1.0, 1_000_000.0)
        self.factor_spinbox.setValue(self.v_to_vm_factor)
        self.factor_spinbox.setStyleSheet(self._spinbox_style())
        self.factor_spinbox.valueChanged.connect(self._on_factor_changed)

        h_layout = QHBoxLayout()
        for w in (title, self.unit_combo, factor_label, self.factor_spinbox):
            h_layout.addWidget(w)
        h_layout.addStretch()
        return h_layout

    def _build_grid(self):
        grid = QGridLayout()
        grid.setSpacing(10)

        self.channel_labels = {}
        self.channel_stats_labels = {}

        for idx, ch in enumerate(self.CHANNELS):
            row, col = divmod(idx, 4)

            name_lbl = QLabel(ch["name"])
            name_lbl.setStyleSheet(
                f"color: {ch['color']}; font-weight: bold; font-size: 12px;"
            )
            name_lbl.setAlignment(Qt.AlignCenter)

            val_lbl = QLabel("0.000")
            val_lbl.setStyleSheet(
                f"""
                background-color: {COLORS['darker_bg']};
                border: 2px solid {ch['color']};
                border-radius: 5px;
                padding: 8px;
                color: {COLORS['text_white']};
                font-family: 'Courier New', monospace;
                font-weight: bold;
                font-size: 14px;
                min-width: 80px;
                """
            )
            val_lbl.setAlignment(Qt.AlignCenter)
            self.channel_labels[ch["name"]] = val_lbl

            stats_lbl = QLabel("μ: --\nσ: --")
            stats_lbl.setStyleSheet(
                f"color: {ch['color']}; font-size: 13px; font-family: 'Courier New', monospace;"
            )
            stats_lbl.setAlignment(Qt.AlignCenter)
            stats_lbl.setWordWrap(True)
            self.channel_stats_labels[ch["name"]] = stats_lbl

            grid.addWidget(name_lbl, row * 3, col)
            grid.addWidget(val_lbl, row * 3 + 1, col)
            grid.addWidget(stats_lbl, row * 3 + 2, col)

        return grid

    # --- Helpers ---
    def _combo_style(self):
        return f"""
            QComboBox {{
                background-color: {COLORS['dark_bg']};
                border: 2px solid {COLORS['border_gray']};
                border-radius: 5px;
                padding: 5px;
                color: {COLORS['text_white']};
                font-weight: bold;
            }}
            QComboBox:focus {{ border-color: {COLORS['primary_blue']}; }}
        """

    def _spinbox_style(self):
        return f"""
            QDoubleSpinBox {{
                background-color: {COLORS['dark_bg']};
                border: 2px solid {COLORS['border_gray']};
                border-radius: 5px;
                padding: 5px;
                color: {COLORS['text_white']};
                font-weight: bold;
            }}
        """

    # --- Slots ---
    def _on_unit_changed(self, unit):
        self.current_unit = unit

    def _on_factor_changed(self, factor):
        self.v_to_vm_factor = factor

    # --- Update ---
    def update_values(self, adc_values: dict):
        buffer = self.acquisition_manager.get_latest_samples(100) if self.acquisition_manager else []
        import numpy as np

        for ch in self.CHANNELS:
            raw = adc_values.get(ch["name"], 0)
            display = self._convert(raw, ch["index"])
            self.channel_labels[ch["name"]].setText(f"{display:.3f}")
            self._update_stats(ch, buffer, np)

    def _convert(self, raw, channel_index):
        if self.current_unit == "Codes ADC":
            return raw
        voltage = self.acquisition_manager.convert_adc_to_voltage(raw, channel=channel_index)
        if self.current_unit == "V/m":
            return voltage * self.v_to_vm_factor
        if self.current_unit == "mV":
            return voltage * 1000
        if self.current_unit == "µV":
            return voltage * 1_000_000
        return voltage

    def _update_stats(self, ch, buffer, np):
        stats_lbl = self.channel_stats_labels[ch["name"]]
        if not buffer:
            stats_lbl.setText("μ: --\nσ: --")
            return

        raw_vals = [getattr(s, ch["attr"], 0) for s in buffer]
        vals = [self._convert(v, ch["index"]) for v in raw_vals]

        if len(vals) > 1:
            mu = np.mean(vals)
            sigma = np.std(vals, ddof=1)
            stats_lbl.setText(f"μ: {mu:.2f}\nσ: {sigma:.2f}")
        else:
            stats_lbl.setText("μ: --\nσ: --")

# --- RealtimeGraphWidget ---
class RealtimeGraphWidget(QWidget):
    """
    Real-time 8-channel pyqtgraph widget for ADC data.
    Displays sliding-window time-series with unit conversion and smoothing.
    """
    WINDOW_DURATION = 2.0          # seconds
    DEFAULT_PERIOD  = 0.1          # fallback period
    MAX_POINTS_EXTRA = 10          # padding

    CHANNELS = [
        dict(name='ADC1_Ch1', index=1, color=COLORS['adc1_blue']),
        dict(name='ADC1_Ch2', index=2, color=COLORS['adc1_blue']),
        dict(name='ADC1_Ch3', index=3, color=COLORS['adc1_blue']),
        dict(name='ADC1_Ch4', index=4, color=COLORS['adc1_blue']),
        dict(name='ADC2_Ch1', index=5, color=COLORS['adc2_green']),
        dict(name='ADC2_Ch2', index=6, color=COLORS['adc2_green']),
        dict(name='ADC2_Ch3', index=7, color=COLORS['adc2_green']),
        dict(name='ADC2_Ch4', index=8, color=COLORS['adc2_green']),
    ]
    ATTR_MAP = {
        'ADC1_Ch1': 'adc1_ch1', 'ADC1_Ch2': 'adc1_ch2',
        'ADC1_Ch3': 'adc1_ch3', 'ADC1_Ch4': 'adc1_ch4',
        'ADC2_Ch1': 'adc2_ch1', 'ADC2_Ch2': 'adc2_ch2',
        'ADC2_Ch3': 'adc2_ch3', 'ADC2_Ch4': 'adc2_ch4',
    }

    def __init__(self, acquisition_manager, parent=None):
        super().__init__(parent)
        self.acquisition_manager = acquisition_manager
        # self.adc_converter = ADCConverter()  # SUPPRIMÉ
        self.current_unit = "mV"
        self.v_to_vm_factor = 63600.0
        self._build_ui()

    # ---------- UI ----------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addLayout(self._build_controls())
        layout.addWidget(self._build_plot())

    def _build_controls(self):
        hl = QHBoxLayout()
        self.checkboxes = {}
        for ch in self.CHANNELS:
            cb = QCheckBox(ch["name"])
            cb.setChecked(True)
            cb.setStyleSheet(f"color:{ch['color']};font-weight:bold;")
            cb.stateChanged.connect(self._on_checkbox_changed)
            self.checkboxes[ch["name"]] = cb
            hl.addWidget(cb)
        hl.addStretch()
        self.smooth_spin = QSpinBox()
        self.smooth_spin.setRange(1, 50)
        self.smooth_spin.setValue(1)
        self.smooth_spin.setToolTip("Largeur moyenne mobile")
        hl.addWidget(QLabel("Lissage:"))
        hl.addWidget(self.smooth_spin)
        return hl

    def _build_plot(self):
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(COLORS['dark_bg'])
        self.plot_widget.showGrid(x=True, y=True, alpha=0.2)
        self.plot_widget.setLabel('left', f'Valeur ({self.current_unit})')
        self.plot_widget.setLabel('bottom', 'Temps (s)')
        self.plot_widget.addLegend()
        self.curves = {}
        for ch in self.CHANNELS:
            c = self.plot_widget.plot([], [], pen=pg.mkPen(ch['color'], width=2), name=ch['name'])
            self.curves[ch['name']] = c
        return self.plot_widget

    # ---------- Helpers ----------
    def _on_checkbox_changed(self):
        for name, cb in self.checkboxes.items():
            self.curves[name].setVisible(cb.isChecked())


    def set_conversion_parameters(self, unit: str, v_to_vm_factor: float):
        """Update conversion parameters and Y-axis label."""
        self.current_unit = unit
        self.v_to_vm_factor = v_to_vm_factor
        self.plot_widget.setLabel('left', f'Valeur ({unit})')


    def _convert(self, raw, ch_index):
        if self.current_unit == "Codes ADC":
            return raw
        v = self.acquisition_manager.convert_adc_to_voltage(raw, channel=ch_index)
        return {
            "V/m": v * self.v_to_vm_factor,
            "mV":  v * 1000,
            "µV":  v * 1_000_000,
        }.get(self.current_unit, v)

    def _smooth(self, values, width):
        if width <= 1 or len(values) < width:
            return values
        import numpy as np
        kernel = np.ones(width) / width
        return np.convolve(values, kernel, mode='same')

    # ---------- Update ----------
    def update_graph(self):
        samples = self.acquisition_manager.get_latest_samples(
            int(self.WINDOW_DURATION / self.DEFAULT_PERIOD + self.MAX_POINTS_EXTRA)
        )


        times = [s.timestamp.timestamp() for s in samples]
        t0 = times[0]
        times = [t - t0 for t in times]

        for ch in self.CHANNELS:
            raw = [getattr(s, self.ATTR_MAP[ch["name"]]) for s in samples]
            vals = [self._convert(r, ch["index"]) for r in raw]
            vals = self._smooth(vals, self.smooth_spin.value())
            self.curves[ch["name"]].setData(times, vals)


# --- AcquisitionManager ---
# =========================
# CLASSE PRINCIPALE MainApp
# =========================

class MainApp(QMainWindow):
    """Application principale avec interface 3 paramètres et backend validé"""

    # =========================
    # Initialisation et setup général
    # =========================
    def __init__(self):
        super().__init__()

        # Création de l'AcquisitionManager
        try:
            self.acquisition_manager = AcquisitionManager(port="COM10")
        except Exception as e:
            QMessageBox.critical(self, "Erreur Initialisation", f"Impossible d'initialiser l'acquisition : {e}")
            sys.exit(1)
            
        self.init_ui()
        self.apply_dark_theme()
        self.setup_connections()
        # Synchronisation initiale forcée
        self._on_acquisition_config_changed(self.acquisition_manager._current_config)
        self._start_exploration()
        # Timer mise à jour affichage
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(100)  # 10 Hz

    def apply_dark_theme(self):
        """Application thème sombre"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['dark_bg']};
                color: {COLORS['text_white']};
            }}
        """)

    # =========================
    # CONSTRUCTION DE L'INTERFACE
    # =========================
    def init_ui(self):
        """Interface principale avec onglets"""
        self.setWindowTitle("Interface d'Acquisition AD9106/ADS131A04 - Phase 1")
        self.setGeometry(100, 100, 1200, 800)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20) 
        # Barre de titre
        title = QLabel("Interface d'Acquisition AD9106/ADS131A04")
        title.setStyleSheet(f"""
            font-weight: bold; 
            font-size: 24px; 
            color: {COLORS['primary_blue']};
            padding: 20px;
            border-bottom: 3px solid {COLORS['primary_blue']};
        """)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        
        # Onglets
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {COLORS['border_gray']};
                border-radius: 8px;
                background-color: {COLORS['darker_bg']};
            }}
            QTabBar::tab {{
                background-color: {COLORS['dark_bg']};
                color: {COLORS['text_white']};
                padding: 10px 20px;
                border: 2px solid {COLORS['border_gray']};
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['primary_blue']};
                border-color: {COLORS['primary_blue']};
            }}
        """)
        
        # Onglet principal
        self.main_tab = self._create_main_tab()
        self.tab_widget.addTab(self.main_tab, "📊 Visualisation & Export")
        
        # Onglet réglages avancés (placeholder)
        self.advanced_tab = self._create_advanced_tab()
        self.tab_widget.addTab(self.advanced_tab, "⚙️ Réglages Avancés DDS/ADC")
        
        main_layout.addWidget(self.tab_widget)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLORS['darker_bg']};
                color: {COLORS['text_white']};
                border-top: 1px solid {COLORS['border_gray']};
            }}
        """)
        self.status_bar.showMessage("Prêt")

    def _create_main_tab(self) -> QWidget:
        """Création onglet principal avec 3 zones + graphique pyqtgraph"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        # Zone gauche : Configuration + Contrôles
        left_layout = QVBoxLayout()
        self.mainParamsConfig_widget = MainParametersConfigWidget()
        self.advanced_settings = AdvancedSettingsWidget(self.acquisition_manager)
        self.mainParamsConfig_widget.advanced_settings = self.advanced_settings
        left_layout.addWidget(self.mainParamsConfig_widget)
        self.export_widget = ExportWidget()
        left_layout.addWidget(self.export_widget)
        left_layout.addStretch()
        layout.addLayout(left_layout)
        # Zone centrale : Affichage numérique
        self.display_widget = NumericDisplayWidget(self.acquisition_manager)
        layout.addWidget(self.display_widget)
        # Zone droite : Graphique temps réel pyqtgraph
        self.graph_widget = RealtimeGraphWidget(self.acquisition_manager)
        layout.addWidget(self.graph_widget)
        # Synchronisation des paramètres de conversion entre affichage numérique et graphique
        self.display_widget.unit_combo.currentTextChanged.connect(self._sync_conversion_to_graph)
        self.display_widget.factor_spinbox.valueChanged.connect(self._sync_conversion_to_graph)
        return tab
        
    def _create_advanced_tab(self) -> QWidget:
        """Création onglet réglages avancés avec intégration complète"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)  # marges réduites
        layout.setSpacing(10)  # espacement réduit
        
        # SUPPRESSION du titre central redondant
        # self.advanced_settings = AdvancedSettingsWidget(self.serial_communicator)
        # layout.addWidget(self.advanced_settings)
        self.advanced_settings = AdvancedSettingsWidget(self.acquisition_manager)
        layout.addWidget(self.advanced_settings)
        
        return tab
        
    # =========================
    # LOGIQUE MONTANTE UI --> MANAGER
    # =========================
    def setup_connections(self):
        """Configuration des connexions signaux/slots"""
        self.mainParamsConfig_widget.configuration_changed.connect(self._on_user_config_changed)
        self.export_widget.start_export.connect(self._start_export)
        self.export_widget.stop_export.connect(self._stop_export)
        self.acquisition_manager.error_occurred.connect(self._on_error_occurred)
        self.acquisition_manager.mode_changed.connect(self._on_mode_changed)
        self.acquisition_manager.configuration_changed.connect(self._on_acquisition_config_changed)

    def _on_user_config_changed(self, config: dict):
        """Synchronisation des paramètres de l'utilisateur vers le Manager"""
        self.acquisition_manager.update_configuration(config)
    
    def _start_exploration(self):
        """Démarrage mode exploration"""
        config = self.mainParamsConfig_widget.get_configuration()
        success = self.acquisition_manager.start_acquisition('exploration', config)
        if success:
            self.status_bar.showMessage("Exploration démarrée")
        else:
            QMessageBox.warning(self, "Erreur", "Impossible de démarrer l'exploration")
    
    def _start_export(self, export_config=None):
        """Démarre l'export avec la config courante du widget export"""
        if export_config is None:
            export_config = self.export_widget.get_config()
        success = self.acquisition_manager.start_export_csv(export_config)
        if success:
            self.status_bar.showMessage("Export CSV démarré")
            self.export_widget.set_export_status("EN COURS")
        else:
            QMessageBox.warning(self, "Erreur", "Impossible de démarrer l'export CSV")
            self.export_widget.set_export_status("ARRÊTÉ")
   
    def _stop_export(self):
        """Arrêt export CSV uniquement (jamais l'acquisition série)"""
        if self.acquisition_manager.is_exporting_csv:
            self.acquisition_manager.stop_export_csv()
            self.status_bar.showMessage("Export CSV arrêté")
            self.export_widget.set_export_status("ARRÊTÉ")
        else:
            QMessageBox.information(self, "Export", "Aucun export CSV en cours.")
            self.export_widget.set_export_status("ARRÊTÉ")
    
    # =========================
    # LOGIQUE DESCENDANTE MANAGER --> UI
    # =========================
    def _on_acquisition_config_changed(self, config: dict):
        """Synchronisation des paramètres du Manager vers tous les widgets"""
        
        # Synchronisation onglet principal (MainParametersConfigWidget)
        self.mainParamsConfig_widget.set_configuration(config)
        
        # Synchronisation onglet avancé (AdvancedSettingsWidget)
        if hasattr(self, 'advanced_settings') and self.advanced_settings is not None:
            # Synchroniser la fréquence
            if 'freq_hz' in config:
                self.advanced_settings.set_frequency(config['freq_hz'])
            # Synchroniser les gains DDS (DDS1 et DDS2 seulement pour l'instant)
            if 'gain_dds' in config:
                self.advanced_settings.set_dds_gain(1, config['gain_dds'])
                self.advanced_settings.set_dds_gain(2, config['gain_dds'])
            # Synchroniser les gains DDS3/4
            if 'gain_dds3' in config:
                self.advanced_settings.set_dds_gain(3, config['gain_dds3'])
            if 'gain_dds4' in config:
                self.advanced_settings.set_dds_gain(4, config['gain_dds4'])
            # Synchroniser les phases DDS1-4
            if 'phase_dds1' in config:
                self.advanced_settings.set_dds_phase(1, config['phase_dds1'])
            if 'phase_dds2' in config:
                self.advanced_settings.set_dds_phase(2, config['phase_dds2'])
            if 'phase_dds3' in config:
                self.advanced_settings.set_dds_phase(3, config['phase_dds3'])
            if 'phase_dds4' in config:
                self.advanced_settings.set_dds_phase(4, config['phase_dds4'])
    
    def _on_mode_changed(self, mode):
        if mode == 'exploration':
            self.mainParamsConfig_widget.set_enabled(True)
            self.export_widget.set_enabled(True)
            self.advanced_settings.set_enabled(True)
            self.status_bar.showMessage("Mode Exploration actif")
        else:
            self.mainParamsConfig_widget.set_enabled(False)
            self.export_widget.set_enabled(False)
            self.advanced_settings.set_enabled(False)
            self.status_bar.showMessage("Mode Export actif - Synchronisation maintenue")

    def _on_error_occurred(self, error_msg: str):
        """Erreur acquisition"""
        QMessageBox.critical(self, "Erreur Acquisition", error_msg)
        self.status_bar.showMessage(f"Erreur: {error_msg}")
    
    # =========================
    # UTILITAIRES INTERNES A L'INTERFACE
    # =========================

    def _update_display(self):
        latest_samples = self.acquisition_manager.get_latest_samples(1)
        if latest_samples:
            sample = latest_samples[0]
            adc_values = {
                'ADC1_Ch1': sample.adc1_ch1,
                'ADC1_Ch2': sample.adc1_ch2,
                'ADC1_Ch3': sample.adc1_ch3,
                'ADC1_Ch4': sample.adc1_ch4,
                'ADC2_Ch1': sample.adc2_ch1,
                'ADC2_Ch2': sample.adc2_ch2,
                'ADC2_Ch3': sample.adc2_ch3,
                'ADC2_Ch4': sample.adc2_ch4
            }
            self.display_widget.update_values(adc_values)
        # Mise à jour du graphique temps réel
        if hasattr(self, 'graph_widget'):
            self.graph_widget.update_graph()
    
    def _sync_conversion_to_graph(self):
        """Synchronisation des paramètres de conversion vers le graphique"""
        if hasattr(self, 'graph_widget'):
            unit = self.display_widget.current_unit
            factor = self.display_widget.v_to_vm_factor
            self.graph_widget.set_conversion_parameters(unit, factor)

    def closeEvent(self, event):
        """Fermeture propre de l'application"""
        # Arrêt propre de l'export CSV si actif
        if hasattr(self, 'acquisition_manager') and self.acquisition_manager.is_exporting_csv:
            self.acquisition_manager.stop_export_csv()
        if hasattr(self, 'acquisition_manager'):
            self.acquisition_manager.close()
        event.accept()

# =========================
# Point d'entrée principal
# =========================
def main():
    """Point d'entrée principal"""
    app = QApplication(sys.argv)
    # Application thème global
    app.setStyle('Fusion')
    
    # Création fenêtre principale
    window = MainApp()
    window.show()
    
    # Exécution
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 