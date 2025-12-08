#!/usr/bin/env python3
"""
Interface d'Acquisition AD9106/ADS131A04 - Phase 1
Interface moderne avec 2 modes : Temps Réel (Exploration) vs Export (Mesures)

Backend validé avec AcquisitionManager et ModeController.
Interface 3 paramètres : Gain DDS, Fréq Hz, N_avg
"""

import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QComboBox, QTabWidget,
                             QPushButton, QGroupBox, QSpinBox, QStatusBar,
                             QDoubleSpinBox, QMessageBox, QGridLayout, QStyle,
                             QCheckBox, QProgressBar, QFileDialog, QLineEdit)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPalette, QColor, QFont

# --- Bloc d'importation robuste pour le module de communication ---
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
    from instruments.AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator
except (ImportError, ModuleNotFoundError):
    try:
        from getE3D.instruments.AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator
    except (ImportError, ModuleNotFoundError):
        QMessageBox.critical(None, "Erreur Critique",
                             "Impossible de trouver le module de communication requis.\n"
                             "Vérifiez l'arborescence du projet et le PYTHONPATH.")
        sys.exit(1)

# Import des composants backend validés
try:
    from getE3D.interface.components.AD9106_ADS131A04_acquisition_manager import AcquisitionManager, AcquisitionStatus
    from getE3D.interface.components.AD9106_ADS131A04_ModeController_Module import ModeController, AcquisitionMode
    from getE3D.interface.components.ADS131A04_Converter_Module import ADCConverter
    from getE3D.interface.components.AD9106_ADS131A04_CSVexporter_Module import CSVExporter
    from getE3D.interface.components.AD9106_AdvancedControl_Widget import DDSControlAdvanced
    from getE3D.interface.components.ADS131A04_AdvancedControl_Widget import ADCControlAdvanced
except ImportError as e:
    QMessageBox.critical(None, "Erreur Backend",
                         f"Impossible d'importer les composants backend : {e}")
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


class ConfigurationWidget(QWidget):
    """Widget de configuration 3 paramètres (Gain DDS, Fréq Hz, N_avg)"""
    
    # Signaux
    configuration_changed = pyqtSignal(dict)
    
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
            color: {COLORS['primary_blue']};
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
        gain_label = QLabel("Gain DDS:")
        gain_label.setStyleSheet(f"color: {COLORS['text_white']}; font-weight: bold;")
        self.gain_spinbox = QSpinBox()
        self.gain_spinbox.setRange(0, 16376)
        self.gain_spinbox.setValue(5000)
        self.gain_spinbox.setStyleSheet(self._spinbox_style())
        self.gain_spinbox.valueChanged.connect(self._on_config_changed)
        
        gain_info = QLabel("(DDS1 & DDS2)")
        gain_info.setStyleSheet(f"color: {COLORS['border_gray']}; font-style: italic;")
        
        # Fréquence
        freq_label = QLabel("Fréq (Hz):")
        freq_label.setStyleSheet(f"color: {COLORS['text_white']}; font-weight: bold;")
        self.freq_spinbox = QDoubleSpinBox()
        self.freq_spinbox.setRange(0.1, 1000000.0)
        self.freq_spinbox.setValue(500.0)
        self.freq_spinbox.setDecimals(1)
        self.freq_spinbox.setSuffix(" Hz")
        self.freq_spinbox.setStyleSheet(self._spinbox_style())
        self.freq_spinbox.valueChanged.connect(self._on_config_changed)
        
        # N_avg
        navg_label = QLabel("N_avg:")
        navg_label.setStyleSheet(f"color: {COLORS['text_white']}; font-weight: bold;")
        self.navg_spinbox = QSpinBox()
        self.navg_spinbox.setRange(1, 1000)
        self.navg_spinbox.setValue(10)
        self.navg_spinbox.setStyleSheet(self._spinbox_style())
        self.navg_spinbox.valueChanged.connect(self._on_config_changed)
        
        # Layout
        config_layout.addWidget(gain_label, 0, 0)
        config_layout.addWidget(self.gain_spinbox, 0, 1)
        config_layout.addWidget(gain_info, 0, 2)
        config_layout.addWidget(freq_label, 1, 0)
        config_layout.addWidget(self.freq_spinbox, 1, 1)
        config_layout.addWidget(navg_label, 2, 0)
        config_layout.addWidget(self.navg_spinbox, 2, 1)
        
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
    
    def _on_config_changed(self):
        """Émission signal configuration changée"""
        config = {
            'gain_dds': self.gain_spinbox.value(),
            'freq_hz': self.freq_spinbox.value(),
            'n_avg': self.navg_spinbox.value()
        }
        self.configuration_changed.emit(config)
    
    def get_configuration(self) -> dict:
        """Retourne la configuration actuelle"""
        return {
            'gain_dds': self.gain_spinbox.value(),
            'freq_hz': self.freq_spinbox.value(),
            'n_avg': self.navg_spinbox.value()
        }
    
    def set_configuration(self, config: dict):
        """Met à jour la configuration"""
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


class NumericDisplayWidget(QWidget):
    """Widget d'affichage numérique 8 canaux temps réel"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.adc_converter = ADCConverter()
        self.current_unit = "mV"
        self.v_to_vm_factor = 63600.0  # Facteur V to V/m par défaut
        self.init_ui()
        
    def init_ui(self):
        """Grille 2x4 avec codes couleur"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Titre avec unités
        title_layout = QHBoxLayout()
        
        title = QLabel("Valeurs Live")
        title.setStyleSheet(f"""
            font-weight: bold; 
            font-size: 16px; 
            color: {COLORS['text_white']};
        """)
        
        # ComboBox unités
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["Codes ADC", "V", "mV", "µV", "V/m"])
        self.unit_combo.setCurrentText("mV")
        self.unit_combo.setStyleSheet(self._combo_style())
        self.unit_combo.currentTextChanged.connect(self._on_unit_changed)
        
        # Facteur V to V/m
        factor_label = QLabel("Facteur V→V/m:")
        factor_label.setStyleSheet(f"color: {COLORS['text_white']};")
        self.factor_spinbox = QDoubleSpinBox()
        self.factor_spinbox.setRange(1.0, 1000000.0)
        self.factor_spinbox.setValue(self.v_to_vm_factor)
        self.factor_spinbox.setStyleSheet(self._spinbox_style())
        self.factor_spinbox.valueChanged.connect(self._on_factor_changed)
        
        title_layout.addWidget(title)
        title_layout.addWidget(self.unit_combo)
        title_layout.addWidget(factor_label)
        title_layout.addWidget(self.factor_spinbox)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Grille 8 canaux
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        # Création des 8 labels
        self.channel_labels = {}
        channel_names = [
            ("ADC1_Ch1", 0, 0, COLORS['adc1_blue']),
            ("ADC1_Ch2", 0, 1, COLORS['adc1_blue']),
            ("ADC1_Ch3", 0, 2, COLORS['adc1_blue']),
            ("ADC1_Ch4", 0, 3, COLORS['adc1_blue']),
            ("ADC2_Ch1", 1, 0, COLORS['adc2_green']),
            ("ADC2_Ch2", 1, 1, COLORS['adc2_green']),
            ("ADC2_Ch3", 1, 2, COLORS['adc2_green']),
            ("ADC2_Ch4", 1, 3, COLORS['adc2_green'])
        ]
        
        for name, row, col, color in channel_names:
            # Label nom canal
            name_label = QLabel(name)
            name_label.setStyleSheet(f"""
                color: {color};
                font-weight: bold;
                font-size: 12px;
            """)
            name_label.setAlignment(Qt.AlignCenter)
            
            # Label valeur
            value_label = QLabel("0.000")
            value_label.setStyleSheet(f"""
                background-color: {COLORS['darker_bg']};
                border: 2px solid {color};
                border-radius: 5px;
                padding: 8px;
                color: {COLORS['text_white']};
                font-family: 'Courier New', monospace;
                font-weight: bold;
                font-size: 14px;
                min-width: 80px;
            """)
            value_label.setAlignment(Qt.AlignCenter)
            
            self.channel_labels[name] = value_label
            
            grid_layout.addWidget(name_label, row * 2, col)
            grid_layout.addWidget(value_label, row * 2 + 1, col)
        
        layout.addLayout(grid_layout)
        
        # Statistiques
        stats_layout = QHBoxLayout()
        
        self.freq_label = QLabel("Fréq: 0 Hz")
        self.freq_label.setStyleSheet(f"color: {COLORS['text_white']};")
        
        self.timestamp_label = QLabel("Dernière MAJ: --")
        self.timestamp_label.setStyleSheet(f"color: {COLORS['text_white']};")
        
        stats_layout.addWidget(self.freq_label)
        stats_layout.addStretch()
        stats_layout.addWidget(self.timestamp_label)
        
        layout.addLayout(stats_layout)
        
    def _combo_style(self) -> str:
        return f"""
            QComboBox {{
                background-color: {COLORS['dark_bg']};
                border: 2px solid {COLORS['border_gray']};
                border-radius: 5px;
                padding: 5px;
                color: {COLORS['text_white']};
                font-weight: bold;
            }}
            QComboBox:focus {{
                border-color: {COLORS['primary_blue']};
            }}
        """
    
    def _spinbox_style(self) -> str:
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
    
    def _on_unit_changed(self, unit: str):
        """Changement d'unité"""
        self.current_unit = unit
        # Conversion des valeurs affichées si nécessaire
    
    def _on_factor_changed(self, factor: float):
        """Changement facteur V to V/m"""
        self.v_to_vm_factor = factor
    
    def update_values(self, adc_values: dict):
        """Met à jour les valeurs affichées"""
        # Mapping explicite channel_name -> numéro de canal
        channel_map = {
            'adc1_ch1': 1, 'adc1_ch2': 2, 'adc1_ch3': 3, 'adc1_ch4': 4,
            'adc2_ch1': 5, 'adc2_ch2': 6, 'adc2_ch3': 7, 'adc2_ch4': 8
        }
        for channel_name, value_label in self.channel_labels.items():
            # Conversion selon l'unité
            if self.current_unit == "Codes ADC":
                display_value = adc_values.get(channel_name, 0)
            else:
                # Conversion via ADCConverter
                channel_index = channel_map.get(channel_name, 1)
                voltage = self.adc_converter.convert_adc_to_voltage(
                    adc_values.get(channel_name, 0),
                    channel=channel_index
                )
                if self.current_unit == "V/m":
                    display_value = voltage * self.v_to_vm_factor
                elif self.current_unit == "mV":
                    display_value = voltage * 1000
                elif self.current_unit == "µV":
                    display_value = voltage * 1000000
                else:  # V
                    display_value = voltage
            # Formatage
            value_label.setText(f"{display_value:.3f}")
    
    def update_stats(self, freq_hz: float, timestamp: str):
        """Met à jour les statistiques"""
        self.freq_label.setText(f"Fréq: {freq_hz:.1f} Hz")
        self.timestamp_label.setText(f"Dernière MAJ: {timestamp}")


class AcquisitionControlsWidget(QWidget):
    """Widget de contrôles d'acquisition selon le mode"""
    
    # Signaux
    start_exploration = pyqtSignal()
    stop_acquisition = pyqtSignal()
    configure_export = pyqtSignal()
    start_export = pyqtSignal(dict)  # config export
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_mode = AcquisitionMode.EXPLORATION
        self.init_ui()
        
    def init_ui(self):
        """Contrôles adaptatifs selon le mode"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Indicateur mode actif
        self.mode_indicator = QLabel("🟢 Mode Temps Réel : Exploration - Modifications immédiates")
        self.mode_indicator.setStyleSheet(f"""
            font-weight: bold;
            font-size: 14px;
            padding: 10px;
            border-radius: 5px;
            background-color: {COLORS['success_green']}20;
            border: 2px solid {COLORS['success_green']};
            color: {COLORS['success_green']};
        """)
        self.mode_indicator.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.mode_indicator)
        
        # Contrôles mode Temps Réel
        self.exploration_group = QGroupBox("Contrôles Exploration")
        self.exploration_group.setStyleSheet(f"""
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
        
        exploration_layout = QHBoxLayout(self.exploration_group)
        
        self.start_exploration_btn = QPushButton("🟢 Démarrer Exploration")
        self.start_exploration_btn.setStyleSheet(self._button_style(COLORS['success_green']))
        self.start_exploration_btn.clicked.connect(self.start_exploration.emit)
        
        self.stop_btn = QPushButton("🔴 Arrêter")
        self.stop_btn.setStyleSheet(self._button_style(COLORS['accent_red']))
        self.stop_btn.clicked.connect(self.stop_acquisition.emit)
        
        self.configure_export_btn = QPushButton("💾 Configurer Export")
        self.configure_export_btn.setStyleSheet(self._button_style(COLORS['warning_orange']))
        self.configure_export_btn.clicked.connect(self.configure_export.emit)
        
        exploration_layout.addWidget(self.start_exploration_btn)
        exploration_layout.addWidget(self.stop_btn)
        exploration_layout.addWidget(self.configure_export_btn)
        
        layout.addWidget(self.exploration_group)
        
        # Contrôles mode Export
        self.export_group = QGroupBox("Contrôles Export")
        self.export_group.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid {COLORS['accent_red']};
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
                background-color: {COLORS['darker_bg']};
                color: {COLORS['text_white']};
                font-weight: bold;
            }}
        """)
        
        export_layout = QVBoxLayout(self.export_group)
        
        # Configuration export
        config_layout = QGridLayout()
        
        # Dossier
        folder_label = QLabel("Dossier:")
        folder_label.setStyleSheet(f"color: {COLORS['text_white']};")
        self.folder_edit = QLineEdit("C:\\Data\\")
        self.folder_edit.setStyleSheet(self._lineedit_style())
        self.folder_btn = QPushButton("📁")
        self.folder_btn.setStyleSheet(self._button_style(COLORS['info_purple']))
        self.folder_btn.clicked.connect(self._select_folder)
        
        # Nom fichier
        name_label = QLabel("Nom:")
        name_label.setStyleSheet(f"color: {COLORS['text_white']};")
        self.name_edit = QLineEdit("Default")
        self.name_edit.setStyleSheet(self._lineedit_style())
        self.name_edit.textChanged.connect(self._update_filename_preview)
        
        # Durée
        duration_label = QLabel("Durée:")
        duration_label.setStyleSheet(f"color: {COLORS['text_white']};")
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(1, 3600)
        self.duration_spinbox.setValue(300)
        self.duration_spinbox.setSuffix(" s")
        self.duration_spinbox.setStyleSheet(self._spinbox_style())
        
        self.continuous_checkbox = QCheckBox("Continu")
        self.continuous_checkbox.setStyleSheet(f"color: {COLORS['text_white']};")
        self.continuous_checkbox.stateChanged.connect(self._on_continuous_changed)
        
        # Preview nom fichier
        self.filename_preview = QLabel("→ 2025-01-15-1430_Default_vsTime.csv")
        self.filename_preview.setStyleSheet(f"color: {COLORS['border_gray']}; font-style: italic;")
        
        config_layout.addWidget(folder_label, 0, 0)
        config_layout.addWidget(self.folder_edit, 0, 1)
        config_layout.addWidget(self.folder_btn, 0, 2)
        config_layout.addWidget(name_label, 1, 0)
        config_layout.addWidget(self.name_edit, 1, 1)
        config_layout.addWidget(self.filename_preview, 1, 2)
        config_layout.addWidget(duration_label, 2, 0)
        config_layout.addWidget(self.duration_spinbox, 2, 1)
        config_layout.addWidget(self.continuous_checkbox, 2, 2)
        
        export_layout.addLayout(config_layout)
        
        # Boutons export
        export_buttons_layout = QHBoxLayout()
        
        self.start_export_btn = QPushButton("💾 Démarrer Export")
        self.start_export_btn.setStyleSheet(self._button_style(COLORS['success_green']))
        self.start_export_btn.clicked.connect(self._start_export)
        
        export_buttons_layout.addWidget(self.start_export_btn)
        export_buttons_layout.addStretch()
        
        export_layout.addLayout(export_buttons_layout)
        
        layout.addWidget(self.export_group)
        
        # Status et progression
        self.status_label = QLabel("Status: STOPPED")
        self.status_label.setStyleSheet(f"color: {COLORS['text_white']}; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {COLORS['border_gray']};
                border-radius: 5px;
                text-align: center;
                background-color: {COLORS['darker_bg']};
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['primary_blue']};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
        # Initialisation état
        self._update_mode_display()
        
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
    
    def _lineedit_style(self) -> str:
        return f"""
            QLineEdit {{
                background-color: {COLORS['dark_bg']};
                border: 2px solid {COLORS['border_gray']};
                border-radius: 5px;
                padding: 5px;
                color: {COLORS['text_white']};
            }}
        """
    
    def _spinbox_style(self) -> str:
        return f"""
            QSpinBox {{
                background-color: {COLORS['dark_bg']};
                border: 2px solid {COLORS['border_gray']};
                border-radius: 5px;
                padding: 5px;
                color: {COLORS['text_white']};
            }}
        """
    
    def _select_folder(self):
        """Sélection dossier export"""
        folder = QFileDialog.getExistingDirectory(self, "Sélectionner dossier export")
        if folder:
            self.folder_edit.setText(folder)
            self._update_filename_preview()
    
    def _update_filename_preview(self):
        """Met à jour preview nom fichier"""
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
        name = self.name_edit.text() or "Default"
        filename = f"{timestamp}_{name}_vsTime.csv"
        self.filename_preview.setText(f"→ {filename}")
    
    def _on_continuous_changed(self, state):
        """Changement mode continu"""
        self.duration_spinbox.setEnabled(not state)
    
    def _start_export(self):
        """Démarrage export"""
        config = {
            'folder': self.folder_edit.text(),
            'name': self.name_edit.text(),
            'duration': self.duration_spinbox.value(),
            'continuous': self.continuous_checkbox.isChecked()
        }
        self.start_export.emit(config)
    
    def set_mode(self, mode: AcquisitionMode):
        """Change le mode d'affichage"""
        self.current_mode = mode
        self._update_mode_display()
    
    def _update_mode_display(self):
        """Met à jour l'affichage selon le mode"""
        if self.current_mode == AcquisitionMode.EXPLORATION:
            self.mode_indicator.setText("🟢 Mode Temps Réel : Exploration - Modifications immédiates")
            self.mode_indicator.setStyleSheet(f"""
                font-weight: bold;
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
                background-color: {COLORS['success_green']}20;
                border: 2px solid {COLORS['success_green']};
                color: {COLORS['success_green']};
            """)
            self.exploration_group.setVisible(True)
            self.export_group.setVisible(False)
        else:
            self.mode_indicator.setText("🔴 Mode Export : Mesures - Interface verrouillée")
            self.mode_indicator.setStyleSheet(f"""
                font-weight: bold;
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
                background-color: {COLORS['accent_red']}20;
                border: 2px solid {COLORS['accent_red']};
                color: {COLORS['accent_red']};
            """)
            self.exploration_group.setVisible(False)
            self.export_group.setVisible(True)
    
    def set_status(self, status: str, progress: int = 0):
        """Met à jour le status et la progression"""
        self.status_label.setText(f"Status: {status}")
        self.progress_bar.setValue(progress)


class AdvancedSettingsWidget(QWidget):
    """Widget principal pour l'onglet réglages avancés"""
    
    # Signaux pour synchronisation avec l'onglet principal
    dds_gain_changed = pyqtSignal(int, int)  # dds_number, gain_value
    dds_phase_changed = pyqtSignal(int, int)  # dds_number, phase_value
    frequency_changed = pyqtSignal(float)  # frequency_hz
    adc_gain_changed = pyqtSignal(int, int)  # channel, gain_value
    
    def __init__(self, communicator, parent=None):
        super().__init__(parent)
        self.communicator = communicator
        self.dds_controls = {}
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        # Zone DDS (gauche)
        dds_group = QGroupBox("🎛️ Contrôle DDS")
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
            dds_control = DDSControlAdvanced(i, self.communicator)
            self.dds_controls[i] = dds_control
            dds_control.gain_changed.connect(self.dds_gain_changed.emit)
            dds_control.phase_changed.connect(self.dds_phase_changed.emit)
            row = (i - 1) // 2
            col = (i - 1) % 2
            dds_layout.addWidget(dds_control, row, col)
        dds_vlayout.addLayout(dds_layout)
        layout.addWidget(dds_group, 2)

        # Zone ADC (droite)
        adc_group = QGroupBox("🟠 Configuration ADC")
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
        self.adc_control = ADCControlAdvanced(self.communicator)
        self.adc_control.gain_changed.connect(self.adc_gain_changed.emit)
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
        self.freq_spin.valueChanged.connect(self._on_frequency_changed)
        
        self.set_freq_button = QPushButton("📡 Appliquer à tous DDS")
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
        self.set_freq_button.clicked.connect(self._apply_frequency_to_all_dds)
        
        layout.addWidget(freq_label)
        layout.addWidget(self.freq_spin)
        layout.addWidget(self.set_freq_button)
        layout.addStretch()
        
        return group
    
    def _on_frequency_changed(self, freq_hz: float):
        """Changement de fréquence"""
        self.frequency_changed.emit(freq_hz)
    
    def _apply_frequency_to_all_dds(self):
        """Application de la fréquence à tous les DDS"""
        freq_hz = self.freq_spin.value()
        success, response = self.communicator.set_dds_frequency(freq_hz)
        if success:
            print(f"✅ Fréquence {freq_hz} Hz appliquée à tous les DDS")
        else:
            print(f"❌ Erreur application fréquence: {response}")
    
    def set_frequency(self, freq_hz: float):
        """Mise à jour externe de la fréquence (pour synchronisation)"""
        self.freq_spin.blockSignals(True)
        self.freq_spin.setValue(freq_hz)
        self.freq_spin.blockSignals(False)
    
    def set_dds_gain(self, dds_number: int, gain_value: int):
        """Mise à jour externe du gain DDS (pour synchronisation)"""
        if dds_number in self.dds_controls:
            self.dds_controls[dds_number].set_gain(gain_value)
    
    def set_adc_gain(self, channel: int, gain_value: int):
        """Mise à jour externe du gain ADC (pour synchronisation)"""
        self.adc_control.set_gain(channel, gain_value)
    
    def set_enabled(self, enabled: bool):
        """Active/désactive tous les contrôles selon le mode"""
        for dds_control in self.dds_controls.values():
            dds_control.setEnabled(enabled)
        self.adc_control.set_enabled(enabled)
        self.freq_spin.setEnabled(enabled)
        self.set_freq_button.setEnabled(enabled)


class MainApp(QMainWindow):
    """Application principale avec interface 3 paramètres et backend validé"""
    
    def __init__(self):
        print("[DEBUG UI] MainApp __init__ appelé")
        super().__init__()
        
        # Initialisation SerialCommunicator
        self.serial_communicator = SerialCommunicator()
        port = "COM10"  # À adapter si besoin
        success, msg = self.serial_communicator.connect(port)
        print(f"[DEBUG UI] Tentative de connexion sur {port}, résultat: {success}, message: {msg}")
        if not success:
            QMessageBox.critical(self, "Erreur Port Série", f"Impossible d'ouvrir le port {port} : {msg}")
            sys.exit(1)
        
        # Composants backend
        self.mode_controller = ModeController(self.serial_communicator)
        self.acquisition_manager = AcquisitionManager(
            serial_communicator=self.serial_communicator,
            mode_controller=self.mode_controller
        )
        
        # Interface
        self.apply_dark_theme()
        self.init_ui()
        self.setup_connections()
        
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
        """Création onglet principal avec 3 zones"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Zone gauche : Configuration + Contrôles
        left_layout = QVBoxLayout()
        
        # Configuration 3 paramètres
        self.config_widget = ConfigurationWidget()
        left_layout.addWidget(self.config_widget)
        
        # Contrôles d'acquisition
        self.controls_widget = AcquisitionControlsWidget()
        left_layout.addWidget(self.controls_widget)
        
        left_layout.addStretch()
        layout.addLayout(left_layout)
        
        # Zone droite : Affichage numérique
        self.display_widget = NumericDisplayWidget()
        layout.addWidget(self.display_widget)
        
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
        self.advanced_settings = AdvancedSettingsWidget(self.serial_communicator)
        layout.addWidget(self.advanced_settings)
        
        return tab
        
    def setup_connections(self):
        """Configuration des connexions signaux/slots"""
        # Configuration → Mode Controller
        self.config_widget.configuration_changed.connect(
            self.mode_controller.update_configuration
        )
        
        # Mode Controller → Interface
        self.mode_controller.mode_changed.connect(self._on_mode_changed)
        self.mode_controller.configuration_changed.connect(
            self.config_widget.set_configuration
        )
        
        # Contrôles → Acquisition Manager
        self.controls_widget.start_exploration.connect(self._start_exploration)
        self.controls_widget.stop_acquisition.connect(self._stop_acquisition)
        self.controls_widget.configure_export.connect(self._configure_export)
        self.controls_widget.start_export.connect(self._start_export)
        
        # Acquisition Manager → Interface
        self.acquisition_manager.data_ready.connect(self._on_data_ready)
        self.acquisition_manager.status_changed.connect(self._on_status_changed)
        self.acquisition_manager.error_occurred.connect(self._on_error_occurred)
        
        # Synchronisation onglet avancé
        if hasattr(self, 'advanced_settings'):
            # Configuration 3 paramètres → Avancé
            self.config_widget.configuration_changed.connect(self._sync_config_to_advanced)
            
            # Avancé → Configuration 3 paramètres
            self.advanced_settings.dds_gain_changed.connect(self._sync_dds_gain_from_advanced)
            self.advanced_settings.frequency_changed.connect(self._sync_frequency_from_advanced)
        
    def _on_mode_changed(self, mode: AcquisitionMode):
        """Changement de mode"""
        self.controls_widget.set_mode(mode)
        
        # Mise à jour interface selon mode
        if mode == AcquisitionMode.EXPLORATION:
            self.config_widget.set_enabled(True)
            if hasattr(self, 'advanced_settings'):
                self.advanced_settings.set_enabled(True)
            self.status_bar.showMessage("Mode Exploration actif")
        else:
            self.config_widget.set_enabled(False)
            if hasattr(self, 'advanced_settings'):
                self.advanced_settings.set_enabled(False)
            self.status_bar.showMessage("Mode Export actif")
    
    def _start_exploration(self):
        """Démarrage mode exploration"""
        config = self.config_widget.get_configuration()
        success = self.acquisition_manager.start_acquisition(
            AcquisitionMode.EXPLORATION, config
        )
        if success:
            self.status_bar.showMessage("Exploration démarrée")
        else:
            QMessageBox.warning(self, "Erreur", "Impossible de démarrer l'exploration")
    
    def _stop_acquisition(self):
        """Arrêt acquisition"""
        success = self.acquisition_manager.stop_acquisition()
        if success:
            self.status_bar.showMessage("Acquisition arrêtée")
    
    def _configure_export(self):
        """Configuration export (transition automatique)"""
        # Transition automatique vers mode export
        success = self.mode_controller.request_export_mode({})
        if not success:
            QMessageBox.warning(self, "Erreur", "Impossible de configurer l'export")
    
    def _start_export(self, export_config: dict):
        """Démarrage export"""
        config = self.config_widget.get_configuration()
        success = self.acquisition_manager.start_acquisition(
            AcquisitionMode.EXPORT, config
        )
        if success:
            self.status_bar.showMessage("Export démarré")
        else:
            QMessageBox.warning(self, "Erreur", "Impossible de démarrer l'export")
    
    def _on_data_ready(self, sample):
        print('DEBUG UI data_ready', sample)
        # Mise à jour affichage (sera géré par timer)
        pass
    
    def _on_status_changed(self, status: str):
        """Changement status acquisition"""
        self.controls_widget.set_status(status.upper())
    
    def _on_error_occurred(self, error_msg: str):
        """Erreur acquisition"""
        QMessageBox.critical(self, "Erreur Acquisition", error_msg)
        self.status_bar.showMessage(f"Erreur: {error_msg}")
    
    def _update_display(self):
        """Mise à jour périodique de l'affichage"""
        latest_samples = self.acquisition_manager._data_buffer.get_latest_samples(1)
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
            stats = self.acquisition_manager.get_acquisition_stats()
            freq = stats.get('acquisition_frequency', 0.0)
            timestamp = sample.timestamp.strftime("%H:%M:%S")
            self.display_widget.update_stats(freq, timestamp)
    
    def _sync_config_to_advanced(self, config: dict):
        """Synchronisation configuration 3 paramètres → onglet avancé"""
        if hasattr(self, 'advanced_settings'):
            # Synchronisation gain DDS (vers DDS1 et DDS2)
            if 'gain_dds' in config:
                self.advanced_settings.set_dds_gain(1, config['gain_dds'])
                self.advanced_settings.set_dds_gain(2, config['gain_dds'])
            
            # Synchronisation fréquence
            if 'freq_hz' in config:
                self.advanced_settings.set_frequency(config['freq_hz'])
    
    def _sync_dds_gain_from_advanced(self, dds_number: int, gain_value: int):
        """Synchronisation gain DDS avancé → configuration 3 paramètres"""
        # Calcul moyenne DDS1/DDS2 pour le gain principal
        if dds_number in [1, 2] and hasattr(self, 'advanced_settings'):
            dds1_gain = self.advanced_settings.dds_controls[1].get_gain()
            dds2_gain = self.advanced_settings.dds_controls[2].get_gain()
            avg_gain = (dds1_gain + dds2_gain) // 2
            
            # Mise à jour widget principal sans boucle
            self.config_widget.gain_spinbox.blockSignals(True)
            self.config_widget.gain_spinbox.setValue(avg_gain)
            self.config_widget.gain_spinbox.blockSignals(False)
    
    def _sync_frequency_from_advanced(self, freq_hz: float):
        """Synchronisation fréquence avancé → configuration 3 paramètres"""
        # Mise à jour widget principal sans boucle
        self.config_widget.freq_spinbox.blockSignals(True)
        self.config_widget.freq_spinbox.setValue(freq_hz)
        self.config_widget.freq_spinbox.blockSignals(False)
    
    def closeEvent(self, event):
        """Fermeture propre de l'application"""
        self.acquisition_manager.stop_acquisition()
        self.serial_communicator.disconnect()
        event.accept()


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