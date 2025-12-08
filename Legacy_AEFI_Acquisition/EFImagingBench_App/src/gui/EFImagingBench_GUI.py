# -*- coding: utf-8 -*-
"""
Interface graphique globale EFImagingBench
- 4 onglets :
    1. Contrôle axes + visualisation
    2. Paramètres moteurs
    3. Acquisition/Export
    4. Réglages DDS+ADC
- Tous les widgets sont connectés à un metaManager unique
- Structure et logique fidèles aux scripts validés (voir EFImagingBench_GUI_tasks.md)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QStatusBar, QLineEdit
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QGroupBox, QGridLayout, QLabel, QDoubleSpinBox, QSpinBox, QComboBox, QPushButton, QCheckBox
        


# Import du metaManager et des widgets (adaptation possible si besoin)
from core.EFImagingBench_metaManager import MetaManager
from core.components.EFImagingBench_ExcitationDirection_Widget import ExcitationDirectionWidget
from core.components.EFImagingBench_PostProcessControl_Widget import PostProcessControlWidget

# Import des widgets et modules ArcusPerformax4EXStage
from core.ArcusPerfomax4EXStage.components.ArcusPerfomax4EXStage_AxisControl_Widget import AxisControlWidget
from core.ArcusPerfomax4EXStage.components.ArcusPerfomax4EXStage_SpeedParameters_Widget import SpeedParametersWidget
from core.ArcusPerfomax4EXStage.components.ArcusPerfomax4EXStage_GeometricalView_Widget import GeometricalViewWidget
from core.ArcusPerfomax4EXStage.modules.ArcusPerfomax4EXStage_GeometricalParametersConversion_Module import cm_to_inc, inc_to_cm

# Import des widgets et modules AD9106_ADS131A04_ElectricField_3D
from core.AD9106_ADS131A04_ElectricField_3D.components.AD9106_MainParametersConfig_Widget import MainParametersConfigWidget
from core.AD9106_ADS131A04_ElectricField_3D.components.AD9106_Export_Widget import ExportWidget
from core.AD9106_ADS131A04_ElectricField_3D.components.AD9106_NumericDisplay_Widget import NumericDisplayWidget
from core.AD9106_ADS131A04_ElectricField_3D.components.AD9106_RealtimeGraph_Widget import RealtimeGraphWidget
from core.AD9106_ADS131A04_ElectricField_3D.components.AD9106_AdvancedSettings_Widget import AdvancedSettingsWidget

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



class EFImagingBenchMainWindow(QMainWindow):
    # =========================
    # INITIALISATION ET SETUP
    # =========================
    def __init__(self):
        super().__init__()
        self.metaManager = MetaManager()
        self.setWindowTitle("EFImagingBench - Interface Globale")
        self.setGeometry(100, 100, 1200, 800)
        self._setup_ui()
        self._setup_connections()
        self._start_EXPLORATION()
        
        # SYNCHRONISATION INITIALE
        self.metaManager.sync_ui_with_hardware()

        # Log de l'état initial
        print("[GUI] === INITIALISATION ===")
        print(f"[GUI] Post-processing enabled: {getattr(self.metaManager, 'post_processing_enabled', 'NOT_SET')}")
        print(f"[GUI] Has post_processed_data_ready: {hasattr(self.metaManager, 'post_processing_data_ready')}")

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        # Onglet Principal : Acquisition Image Scan
        self.tab_widget.addTab(self._create_main_tab(), "Onglet Principal")
        


        # Onglet 1 : Contrôle axes + visualisation
        #self.tab_widget.addTab(self._create_axes_control_tab(), "Axes + Visualisation")
        # Onglet 2 : Paramètres moteurs
        self.tab_widget.addTab(self._create_motor_params_tab(), "Paramètres moteurs")
        # Onglet 3 : Acquisition/Export
        self.tab_widget.addTab(self._create_acquisition_tab(), "Export vs Time")
        # Onglet 4 : Réglages DDS+ADC
        self.tab_widget.addTab(self._create_advanced_tab(), "Réglages DDS+ADC")
        # Barre de statut
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Prêt")

    def apply_dark_theme(self):
        """Application thème sombre"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['dark_bg']};
                color: {COLORS['text_white']};
            }}
        """)


    # =========================
    # CONSTRUCTION UI
    # =========================
    def _create_axes_control_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        # Ligne de contrôle des axes
        axes_layout = QHBoxLayout()
        self.x_control = AxisControlWidget("X", "x")
        self.y_control = AxisControlWidget("Y", "y")
        axes_layout.addWidget(self.x_control)
        axes_layout.addWidget(self.y_control)
        layout.addLayout(axes_layout)
        # Zone du bas : scan 2D + visualisation
        bottom_layout = QHBoxLayout()
        # Scan 2D (reprise de la logique Arcus)
        from PyQt5.QtWidgets import QGroupBox, QGridLayout, QLabel, QDoubleSpinBox, QSpinBox, QComboBox, QPushButton
        scan2d_group = QGroupBox("Configuration Scan 2D")
        scan2d_layout = QGridLayout(scan2d_group)
        self.xmin_input = QDoubleSpinBox(); self.xmax_input = QDoubleSpinBox()
        self.ymin_input = QDoubleSpinBox(); self.ymax_input = QDoubleSpinBox()
        self.n_input = QSpinBox(); self.mode_combo = QComboBox()
        self.visualization_scan_btn = QPushButton("Visualiser Zone Scan")
        self.execute_btn = QPushButton("Exécuter le scan")
        self.mode_combo.addItems(["E", "S"])
        scan2d_layout.addWidget(QLabel("x_min (cm) :"), 0, 0)
        scan2d_layout.addWidget(self.xmin_input, 0, 1)
        scan2d_layout.addWidget(QLabel("x_max (cm) :"), 0, 2)
        scan2d_layout.addWidget(self.xmax_input, 0, 3)
        scan2d_layout.addWidget(QLabel("y_min (cm) :"), 1, 0)
        scan2d_layout.addWidget(self.ymin_input, 1, 1)
        scan2d_layout.addWidget(QLabel("y_max (cm) :"), 1, 2)
        scan2d_layout.addWidget(self.ymax_input, 1, 3)
        scan2d_layout.addWidget(QLabel("N (lignes) :"), 2, 0)
        scan2d_layout.addWidget(self.n_input, 2, 1)
        scan2d_layout.addWidget(QLabel("Mode :"), 2, 2)
        scan2d_layout.addWidget(self.mode_combo, 2, 3)
        scan2d_layout.addWidget(self.visualization_scan_btn, 3, 0, 1, 2)
        scan2d_layout.addWidget(self.execute_btn, 3, 2, 1, 2)
        scan2d_group.setLayout(scan2d_layout)
        bottom_layout.addWidget(scan2d_group)
        # Visualisation
        self.visual_widget = GeometricalViewWidget()
        bottom_layout.addWidget(self.visual_widget, stretch=1)
        layout.addLayout(bottom_layout)
        return widget

    def _create_motor_params_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.speed_params = SpeedParametersWidget()
        layout.addWidget(self.speed_params)
        layout.addStretch()
        return widget

    def _create_acquisition_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        # À gauche : config + export
        left_layout = QVBoxLayout()
        self.main_params = MainParametersConfigWidget()
        self.export_widget = ExportWidget()
        left_layout.addWidget(self.main_params)
        left_layout.addWidget(self.export_widget)
        
        # Ajout du bouton de compensation des signaux parasites
        self.signals_compensation_btn = QPushButton("Compensation Signaux Parasites")
        self.signals_compensation_btn.setCheckable(True)
        self.signals_compensation_btn.setChecked(False)  # Désactivé par défaut
        left_layout.addWidget(self.signals_compensation_btn)
        
        # --- Bouton de reset acquisition ---
        self.reset_acquisition_btn = QPushButton("🔄 Redémarrer Acquisition (Reset)")
        self.reset_acquisition_btn.setStyleSheet("QPushButton { background-color: #F77F00; color: white; font-weight: bold; padding: 10px; }")
        left_layout.addWidget(self.reset_acquisition_btn)
        self.reset_acquisition_btn.clicked.connect(self._reset_acquisition_default)
        
        left_layout.addStretch()
        layout.addLayout(left_layout)
        
        # Centre : affichage numérique + rotation
        center_layout = QHBoxLayout()
        # self.display_widget = NumericDisplayWidget(self.metaManager)  # COMMENTÉ - doublon
        # center_layout.addWidget(self.display_widget)

        layout.addLayout(center_layout)
        
        # Droite : graphique temps réel
        # self.graph_widget = RealtimeGraphWidget(self.metaManager)  # COMMENTÉ - doublon
        # layout.addWidget(self.graph_widget)
        
        return widget

    def _reset_acquisition_default(self):
        """Arrête et redémarre complètement l'acquisition avec la configuration par défaut."""
        try:
            print("[UI] Redémarrage complet de l'acquisition (reset manager)")
            self.metaManager.stop_acquisition()
            default_config = self.main_params.get_default_configuration() if hasattr(self.main_params, 'get_default_configuration') else {}
            success = self.metaManager.start_acquisition('exploration', default_config)
            if success:
                self.status_bar.showMessage("🔄 Acquisition réinitialisée avec la configuration par défaut")
            else:
                self.status_bar.showMessage("❌ Impossible de redémarrer l'acquisition")
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur lors du reset acquisition: {e}")

    def _create_advanced_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.advanced_settings = AdvancedSettingsWidget(self.metaManager)
        layout.addWidget(self.advanced_settings)
        return widget

    def _create_main_tab(self):
        """Onglet expérimental combinant Axes + Acquisition/Export"""

        widget = QWidget()
        main_layout = QHBoxLayout(widget)  # Layout principal horizontal
        
        # ========== PARTIE GAUCHE : CONTRÔLE DES AXES ==========
        axes_group = QGroupBox("🎛️ Contrôle des Axes")
        axes_layout = QVBoxLayout(axes_group)
        self.x_control_main = AxisControlWidget("X", "x")
        self.y_control_main = AxisControlWidget("Y", "y")
        axes_layout.addWidget(self.x_control_main)
        axes_layout.addWidget(self.y_control_main)
        
        # Bouton Home Both X+Y
        self.home_both_btn_main = QPushButton("🏠 Home Both X+Y")
        self.home_both_btn_main.setStyleSheet("QPushButton { background-color: #2E86AB; color: white; font-weight: bold; padding: 10px; margin: 5px; }")
        axes_layout.addWidget(self.home_both_btn_main)
        
        # Bouton Emergency Stop
        self.emergency_stop_btn_main = QPushButton("🚨 EMERGENCY STOP")
        self.emergency_stop_btn_main.setStyleSheet("QPushButton { background-color: #E63946; color: white; font-weight: bold; padding: 10px; margin: 5px; font-size: 14px; }")
        axes_layout.addWidget(self.emergency_stop_btn_main)
        
        axes_layout.addStretch()  # Pour pousser les widgets vers le haut
        
        axes_group.setMaximumWidth(450)  # Largeur fixe pour la colonne de gauche
        main_layout.addWidget(axes_group)
        
        # Configuration Excitation & Acquisition (déplacée ici)
        acquisition_config_group = QGroupBox("⚡ Configuration Excitation-Acquisition")
        acquisition_config_layout = QVBoxLayout(acquisition_config_group)
        
        # Widget Direction d'Excitation (intégré) - COMPACT
        self.excitation_widget_main = ExcitationDirectionWidget()
        self.excitation_widget_main.setMaximumHeight(120)  # Hauteur maximale fixée ici
        self.excitation_widget_main.setMinimumHeight(80)   # Hauteur minimale
        acquisition_config_layout.addWidget(self.excitation_widget_main)
        
        # Paramètres d'acquisition
        self.main_params_main = MainParametersConfigWidget()
        acquisition_config_layout.addWidget(self.main_params_main)
        
        acquisition_config_group.setMaximumWidth(450)  # Même largeur que les axes
        main_layout.addWidget(acquisition_config_group)
        

        # ========== PARTIE MILIEU : CONFIGURATION ==========
        config_layout = QVBoxLayout()
        
        # Configuration Scan 2D + Visualisation géométrique
        scan2d_visual_group = QGroupBox("🗺️ Scan 2D & Visualisation")
        scan2d_visual_layout = QVBoxLayout(scan2d_visual_group)
        
        # Partie configuration scan (compacte)
        scan_config_layout = QGridLayout()
        
        self.xmin_input_main = QDoubleSpinBox(); self.xmax_input_main = QDoubleSpinBox()
        self.ymin_input_main = QDoubleSpinBox(); self.ymax_input_main = QDoubleSpinBox()
        self.n_input_main = QSpinBox(); self.mode_combo_main = QComboBox()
        self.y_nb_input_main = QSpinBox(); self.timer_ms_input_main = QSpinBox()
        self.visualization_scan_btn_main = QPushButton("Visualiser Zone Scan")
        self.execute_btn_main = QPushButton("Exécuter le scan")
        
        # Configuration des inputs scan
        for inp in [self.xmin_input_main, self.xmax_input_main, self.ymin_input_main, self.ymax_input_main]:
            inp.setRange(0.0, 130.0)
            inp.setDecimals(2)
        # Valeurs par défaut
        self.xmin_input_main.setValue(50.0)
        self.xmax_input_main.setValue(70.0)
        self.ymin_input_main.setValue(50.0)
        self.ymax_input_main.setValue(70.0)
        self.n_input_main.setRange(1, 1000)
        self.n_input_main.setValue(3)
        # y_nb: nombre de points en Y par ligne (pour export/config)
        self.y_nb_input_main.setRange(1, 10000)
        self.y_nb_input_main.setValue(81)
        # timer_ms: attente entre points (ms)
        self.timer_ms_input_main.setRange(0, 100000)
        self.timer_ms_input_main.setValue(0)
        self.mode_combo_main.addItems(["E", "S"])
        
        # Layout scan 2D (plus compact)
        scan_config_layout.addWidget(QLabel("x_min (cm) :"), 0, 0)
        scan_config_layout.addWidget(self.xmin_input_main, 0, 1)
        scan_config_layout.addWidget(QLabel("x_max (cm) :"), 0, 2)
        scan_config_layout.addWidget(self.xmax_input_main, 0, 3)
        scan_config_layout.addWidget(QLabel("y_min (cm) :"), 1, 0)
        scan_config_layout.addWidget(self.ymin_input_main, 1, 1)
        scan_config_layout.addWidget(QLabel("y_max (cm) :"), 1, 2)
        scan_config_layout.addWidget(self.ymax_input_main, 1, 3)
        scan_config_layout.addWidget(QLabel("N (lignes X) :"), 2, 0)
        scan_config_layout.addWidget(self.n_input_main, 2, 1)
        scan_config_layout.addWidget(QLabel("Mode :"), 2, 2)
        scan_config_layout.addWidget(self.mode_combo_main, 2, 3)
        scan_config_layout.addWidget(QLabel("y_nb (points Y) :"), 3, 0)
        scan_config_layout.addWidget(self.y_nb_input_main, 3, 1)
        scan_config_layout.addWidget(QLabel("timer_ms :"), 3, 2)
        scan_config_layout.addWidget(self.timer_ms_input_main, 3, 3)
        scan_config_layout.addWidget(self.visualization_scan_btn_main, 4, 0, 1, 2)
        scan_config_layout.addWidget(self.execute_btn_main, 4, 2, 1, 2)
        
        # Checkbox pour filtrage des lignes actives
        self.filter_active_lines_checkbox = QCheckBox("Exporter uniquement lignes actives")
        self.filter_active_lines_checkbox.setToolTip("Si coché, seules les données des lignes de scan seront exportées (pas les transitions)")
        scan_config_layout.addWidget(self.filter_active_lines_checkbox, 4, 0, 1, 4)
        
        # Chemin d'export
        self.export_path_input = QLineEdit(r"C:\Users\manip\Documents\Data")
        self.export_path_input.setPlaceholderText("Chemin d'export")
        scan_config_layout.addWidget(QLabel("Export Path:"), 5, 0)
        scan_config_layout.addWidget(self.export_path_input, 5, 1, 1, 3)
        
        # Bouton pour arrêter l'export
        self.stop_export_btn_main = QPushButton("Arrêter Export CSV")
        self.stop_export_btn_main.setStyleSheet("QPushButton { background-color: #E63946; color: white; }")
        scan_config_layout.addWidget(self.stop_export_btn_main, 6, 0, 1, 4)

        # Ajout de la configuration au layout principal
        scan2d_visual_layout.addLayout(scan_config_layout)
        
        # Partie visualisation géométrique
        self.visual_widget_main = GeometricalViewWidget()
        scan2d_visual_layout.addWidget(self.visual_widget_main, stretch=1)
        
        config_layout.addWidget(scan2d_visual_group)
        
        # Post-processing widget avec contrôle complet
        self.post_process_widget = PostProcessControlWidget()
        config_layout.addWidget(self.post_process_widget)
        
        # Connecter au MetaManager
        self.post_process_widget.connect_to_manager(self.metaManager)
        


        config_layout.addStretch()  # Pour pousser les groupes vers le haut
        
        # Largeur fixe pour la zone de configuration
        config_widget = QWidget()
        config_widget.setLayout(config_layout)
        config_widget.setMaximumWidth(1500)  # Largeur fixe pour toute la config
        main_layout.addWidget(config_widget)
        
        # ========== PARTIE DROITE : AFFICHAGE DES DONNÉES ==========
        display_layout = QVBoxLayout()
        
        # Affichage numérique en haut
        display_group = QGroupBox("📊 Valeurs Live en RMS")
        display_group_layout = QVBoxLayout(display_group)  # Changé en QVBoxLayout
        
        self.display_widget_main = NumericDisplayWidget(self.metaManager, hidden_channels=["ADC2_Ch3", "ADC2_Ch4"])
        display_group_layout.addWidget(self.display_widget_main)
        
        # Taille du groupe
        display_group.setMinimumSize(450, 250)
        display_layout.addWidget(display_group)
        

        # Graphique temps réel en bas
        graph_group = QGroupBox("📈 Affichage Temps Réel")
        graph_group_layout = QVBoxLayout(graph_group)
        self.graph_widget_main = RealtimeGraphWidget(self.metaManager)
        graph_group_layout.addWidget(self.graph_widget_main)
        display_layout.addWidget(graph_group, stretch=1)
        
        # Ajout de la partie affichage au layout principal
        main_layout.addLayout(display_layout, stretch=1)
        

        
        return widget

    def _setup_connections(self):

        # Signal position_changed → visualisation + widgets X/Y
        self.metaManager.position_changed.connect(self._on_position_changed)
        # Onglet 2 : Paramètres moteurs
        self.speed_params.apply_btn.clicked.connect(self.apply_speed_parameters)
        # Onglet 3 : Acquisition/Export
        self.main_params.configuration_changed.connect(self._on_user_config_changed)
        self.export_widget.start_export.connect(self._start_export_csv)
        self.export_widget.stop_export.connect(self._stop_export_csv)
        self.metaManager.mode_changed.connect(self._on_mode_changed)
        self.metaManager.status_changed.connect(self._on_state_changed)
        self.metaManager.error_occurred.connect(self._on_error_occurred)
        self.metaManager.configuration_changed.connect(self._on_acquisition_config_changed)
        
        # Onglet 5 EXPÉRIMENTAL : Connexions pour les widgets dupliqués
        # Contrôle axes expérimental
        self.x_control_main.move_btn.clicked.connect(lambda: (print('[UI-EXP] Move To X'), self.move_to_main("x")))
        self.x_control_main.home_btn.clicked.connect(lambda: (print('[UI-EXP] Home X'), self.home("x")))
        self.x_control_main.stop_btn.clicked.connect(lambda: (print('[UI-EXP] Stop X'), self.stop("x", False)))
        self.x_control_main.emergency_btn.clicked.connect(lambda: (print('[UI-EXP] Emergency Stop X'), self.stop("x", True)))
        self.y_control_main.move_btn.clicked.connect(lambda: (print('[UI-EXP] Move To Y'), self.move_to_main("y")))
        self.y_control_main.home_btn.clicked.connect(lambda: (print('[UI-EXP] Home Y'), self.home("y")))
        self.y_control_main.stop_btn.clicked.connect(lambda: (print('[UI-EXP] Stop Y'), self.stop("y", False)))
        self.y_control_main.emergency_btn.clicked.connect(lambda: (print('[UI-EXP] Emergency Stop Y'), self.stop("y", True)))
        
        # Bouton Home Both X+Y expérimental
        self.home_both_btn_main.clicked.connect(lambda: (print('[UI-EXP] Home Both X+Y'), self.home_both_lock_main()))
        
        # Bouton Emergency Stop expérimental
        self.emergency_stop_btn_main.clicked.connect(lambda: (print('[UI-EXP] Emergency Stop Both'), self.emergency_stop_both_main()))
        
        # Scan 2D expérimental
        self.visualization_scan_btn_main.clicked.connect(self._update_subrect_from_ui_main)
        self.execute_btn_main.clicked.connect(self._execute_scan2d_from_ui_main)
        
        # Acquisition/Export expérimental
        self.main_params_main.configuration_changed.connect(self._on_user_config_changed)
        # self.export_widget_main.start_export.connect(self._start_export_csv)  # COMMENTÉ - doublon
        # self.export_widget_main.stop_export.connect(self._stop_export_csv)  # COMMENTÉ - doublon
        
        # Direction d'excitation expérimental
        self.excitation_widget_main.excitation_changed.connect(self._on_excitation_direction_changed)
        
        # Position synchronisée vers visualisation expérimentale
        self.metaManager.position_changed.connect(self._on_position_changed_main)
        
        # Onglet 4 : Réglages DDS+ADC - CONNEXIONS COMPLÈTES
        # === DDS Controls ===
        self.advanced_settings.dds_controls = getattr(self.advanced_settings, 'dds_controls', {})
        for dds in self.advanced_settings.dds_controls.values():
            dds.gain_changed.connect(lambda dds_num, gain: (print(f"[DEBUG UI] DDS{dds_num} gain_changed: {gain} → MetaManager"), self.metaManager.update_configuration({f'gain_dds{dds_num}': gain}))[1])
            dds.phase_changed.connect(lambda dds_num, phase: (print(f"[DEBUG UI] DDS{dds_num} phase_changed: {phase} → MetaManager"), self.metaManager.update_configuration({f'phase_dds{dds_num}': phase}))[1])
            dds.frequency_changed.connect(lambda freq: (print(f"[DEBUG UI] DDS frequency_changed: {freq} Hz → MetaManager"), self.metaManager.update_configuration({'freq_hz': freq}))[1])
        
        # === Fréquence globale ===
        if hasattr(self.advanced_settings, 'set_freq_button'):
            self.advanced_settings.set_freq_button.clicked.connect(self._apply_global_frequency)
        
        # === ADC Controls ===
        if hasattr(self.advanced_settings, 'adc_control'):
            self.advanced_settings.adc_control.gain_changed.connect(lambda ch, gain: (print(f"[DEBUG UI] ADC Ch{ch} gain_changed: {gain} → MetaManager"), self.metaManager.update_configuration({f'adc_gain_ch{ch}': gain}))[1])
            self.advanced_settings.adc_control.timing_changed.connect(self._on_adc_timing_changed)
            self.advanced_settings.adc_control.reference_changed.connect(self._on_adc_reference_changed)
        
        # === Synchronisation MetaManager -> UI ===
        self.metaManager.configuration_changed.connect(self._on_acquisition_config_changed)
        self.metaManager.mode_changed.connect(self.update_mode_status)
        self.metaManager.status_changed.connect(self._on_state_changed)
        
        # === 🔄 SYNCHRONISATION UNITÉS NumericDisplay ↔ RealtimeGraph ===
        # print("[DEBUG GUI] Configuration synchronisation unités entre widgets...")
        self._setup_unit_synchronization()
        
        # === 🔄 CONTRÔLE ROTATION DE RÉFÉRENTIEL ===
        # print("[DEBUG GUI] Configuration contrôle rotation de référentiel...")
        self._setup_frame_rotation()

        # === Connexions Post-Traitement ===
        # Rotation de référentiel - COMMENTÉ pour l'onglet 3
        # self.rotation_widget.connect_to_manager(self.metaManager)  # COMMENTÉ
        
        # Compensation signaux parasites (post-processing)
        self.signals_compensation_btn.clicked.connect(
            lambda checked: self._on_post_processing_toggled(checked)
        )
        
        # Post-processing widget
        #self.post_process_widget.calibration_requested.connect(self._on_calibration_requested)
        self.post_process_widget.calibration_completed.connect(lambda step, result: self._on_calibration_completed(step, result))
    
        
        # === CONNEXIONS POUR LES DONNÉES ===
        print("[GUI] Configuration connexions données...")
        
        # Données brutes (inchangé)
        self.metaManager.data_ready.connect(self._update_display_raw)
        
        # Données traitées via buffer
        if hasattr(self.metaManager, 'post_processed_data_ready'):
            self.metaManager.post_processed_data_ready.connect(self._update_display_processed)
            print("[GUI] Connexion post_processed_data_ready → buffer")
        
        if hasattr(self.metaManager, 'post_processing_changed'):
            print("[GUI] Connexion post_processing_changed")
            self.metaManager.post_processing_changed.connect(self._on_post_processing_changed)
        else:
            print("[GUI] ERREUR: post_processing_changed signal non trouvé!")
        
        # Test de connexion
        if hasattr(self.metaManager, 'post_processed_data_ready'):
            print(f"[DEBUG] Connexion post_processed_data_ready: {self.metaManager.receivers(self.metaManager.post_processed_data_ready)}")
        
        # Vérification des méthodes attendues
        if hasattr(self.metaManager, 'set_post_processing_enabled'):
            print("[GUI] Méthode set_post_processing_enabled trouvée")
        else:
            print("[GUI] ERREUR: Méthode set_post_processing_enabled non trouvée!")

    # =========================
    # LOGIQUE MONTANTE UI --> METAMANAGER
    # =========================

    # === TO STAGE MANAGER ===
    def move_to(self, axis):
        print(f"[DEBUG UI] move_to appelé pour axe {axis}")
        print(f"[DEBUG UI] État actuel du homing - X: {self.metaManager.managers['stage'].controller.get_axis_homed_status('x')}, Y: {self.metaManager.managers['stage'].controller.get_axis_homed_status('y')}")
        
        # Vérification si l'axe est homed avant d'envoyer la commande
        if not self.metaManager.managers['stage'].controller.get_axis_homed_status(axis):
            QMessageBox.information(self, "Homing requis", f"L'axe {axis.upper()} n'est pas homed. Veuillez faire le homing d'abord.")
            print(f"[DEBUG UI] Commande move_to bloquée - axe {axis} non homed")
            return
        
        print(f"[DEBUG UI] Envoi de la commande move_to vers MetaManager pour axe {axis}")
        target = getattr(self, f"{axis}_control").get_target_position()
        target_inc, _ = cm_to_inc(target)
        self.metaManager.move_to(axis, target_inc)

    def home(self, axis):
        print(f"[DEBUG UI] home appelé pour axe {axis}")
        print(f"[DEBUG UI] État avant homing - {axis}: {self.metaManager.managers['stage'].controller.get_axis_homed_status(axis)}")
        print(f"[DEBUG UI] Envoi de la commande home vers MetaManager pour axe {axis}")
        self.metaManager.home_lock(axis)

    def home_both(self):
        print("[UI] Appel home_both (commande HOME_BOTH)")
        try:
            self.metaManager.home_both()
            self.status_bar.showMessage("🏠 Homing X+Y en cours...")
            # Logique synchrone d'origine : attendre la fin du homing ici si besoin
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur homing X+Y: {e}")

    def stop(self, axis, immediate=False):
        try:
            self.metaManager.stop(axis, immediate=immediate)
            if immediate:
                self.status_bar.showMessage(f"🛑 Arrêt d'urgence axe {axis.upper()}")
            else:
                self.status_bar.showMessage(f"⏸️ Arrêt contrôlé axe {axis.upper()}")
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur arrêt {axis}: {e}")

    def emergency_stop_all(self):
        try:
            for axis in ["x", "y"]:
                self.metaManager.stop(axis, immediate=True)
            self.status_bar.showMessage("🚨 ARRÊT D'URGENCE GLOBAL ACTIVÉ")
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur arrêt d'urgence: {e}")

    def apply_speed_parameters(self):
        try:
            for axis in ["x", "y"]:
                params = self.speed_params.get_params(axis)
                self.metaManager.set_axis_params(axis, **params)
            self.status_bar.showMessage("🚀 Paramètres de vitesse appliqués avec succès")
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur application paramètres: {e}")

    def load_current_parameters(self):
        try:
            for axis in ["x", "y"]:
                def on_params(params, axis=axis):
                    def update_ui():
                        self.speed_params.set_params(axis, params)
                        self.status_bar.showMessage(f"✅ Paramètres {axis.upper()} chargés depuis le contrôleur")
                    QTimer.singleShot(0, update_ui)
                self.metaManager.get_axis_params(axis, callback=on_params)
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur chargement paramètres: {e}")

    # === NOUVELLES MÉTHODES POUR RÉGLAGES DDS+ADC ===
    def _apply_global_frequency(self):
        """Applique la fréquence globale à tous les DDS"""
        try:
            freq = self.advanced_settings.freq_spin.value()
            print(f"[DEBUG UI] _apply_global_frequency: freq={freq} Hz → MetaManager")
            self.metaManager.update_configuration({'freq_hz': freq})
            self.status_bar.showMessage(f"🎯 Fréquence globale appliquée: {freq} Hz")
        except Exception as e:
            print(f"[DEBUG UI] Erreur _apply_global_frequency: {e}")
            self.status_bar.showMessage(f"❌ Erreur fréquence globale: {e}")

    def _on_adc_timing_changed(self, timing_config: dict):
        """Gestion changement paramètres timing ADC"""
        try:
            print(f"[DEBUG UI] _on_adc_timing_changed: config={timing_config} → MetaManager")
            self.metaManager.update_configuration(timing_config)
            self.status_bar.showMessage("⏱️ Paramètres timing ADC mis à jour")
        except Exception as e:
            print(f"[DEBUG UI] Erreur _on_adc_timing_changed: {e}")
            self.status_bar.showMessage(f"❌ Erreur timing ADC: {e}")

    def _on_adc_reference_changed(self, reference_config: dict):
        """Gestion changement paramètres référence ADC"""
        try:
            print(f"[DEBUG UI] _on_adc_reference_changed: config={reference_config} → MetaManager")
            self.metaManager.update_configuration(reference_config)
            self.status_bar.showMessage("🎚️ Paramètres référence ADC mis à jour")
        except Exception as e:
            print(f"[DEBUG UI] Erreur _on_adc_reference_changed: {e}")
            self.status_bar.showMessage(f"❌ Erreur référence ADC: {e}")

    def _on_excitation_direction_changed(self, mode: str, phase_config: dict):
        """Gestion changement direction d'excitation"""
        try:
            print(f"[DEBUG UI] _on_excitation_direction_changed: mode={mode}, phases={phase_config} → MetaManager")
            self.metaManager.update_configuration(phase_config)
            
            # Message de statut selon le mode
            mode_messages = {
                "off": "🔌 Excitation désactivée",
                "xdir": "↔️ Excitation direction X",
                "ydir": "↕️ Excitation direction Y", 
                "circ+": "🔄 Excitation circulaire +",
                "circ-": "🔄 Excitation circulaire -"
            }
            message = mode_messages.get(mode, f"🎯 Direction d'excitation: {mode}")
            self.status_bar.showMessage(message)
            
        except Exception as e:
            print(f"[DEBUG UI] Erreur _on_excitation_direction_changed: {e}")
            self.status_bar.showMessage(f"❌ Erreur direction excitation: {e}")

    def _detect_excitation_mode_from_phases(self, config: dict) -> str:
        """Détecte le mode d'excitation à partir des phases DDS"""
        try:
            # Récupérer les phases (avec valeurs par défaut si manquantes)
            phase1 = config.get('phase_dds1', 0)
            phase2 = config.get('phase_dds2', 0)
            phase3 = config.get('phase_dds3', 0)
            phase4 = config.get('phase_dds4', 0)
            
            # Normaliser les phases sur [0, 32768) pour comparaison
            phases = [p % 65536 for p in [phase1, phase2, phase3, phase4]]
            
            # Définir les configurations connues (avec tolérance)
            def phases_match(target, tolerance=1000):
                return all(abs(phases[i] - target[i]) <= tolerance for i in range(4))
            
            # X Direction : [0, 32768, 32768, 0] (DDS1 et DDS2 en opposition)
            if phases_match([0, 32768, 32768, 0]):
                return "xdir"
            
            # Y Direction : [0, 0, 32768, 32768] (DDS1 et DDS2 en phase)
            if phases_match([0, 0, 32768, 32768]):
                return "ydir"
            
            # Circulaire + : [0, 16384, 32768, 49152]
            if phases_match([0, 16384, 32768, 49152]):
                return "circ+"
            
            # Circulaire - : [0, 49152, 32768, 16384]
            if phases_match([0, 49152, 32768, 16384]):
                return "circ-"
            
            # Off : [0, 0, 0, 0]
            if phases_match([0, 0, 0, 0]):
                return "off"
            
            # Configuration non reconnue
            print(f"[DEBUG GUI] Configuration de phases non reconnue: {phases}")
            return None
            
        except Exception as e:
            print(f"[DEBUG GUI] Erreur détection mode excitation: {e}")
            return None


    # === TO ACQUISITION MANAGER ===
    def _on_user_config_changed(self, config: dict):
        """Synchronisation des paramètres de l'utilisateur vers le Manager"""
        self.metaManager.update_configuration(config)

    def _start_EXPLORATION(self):
        """Démarrage mode exploration"""
        config = self.main_params.get_configuration()
        success = self.metaManager.start_acquisition('exploration', config)
        if success:
            self.status_bar.showMessage("Exploration démarrée")
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", "Impossible de démarrer l'exploration")

    def _start_export_csv(self, export_config=None):
        """Démarre l'export avec la config courante du widget export"""
        if export_config is None:
            export_config = self.export_widget.get_config()
        success = self.metaManager.start_export_csv(export_config)
        if success:
            self.status_bar.showMessage("Export CSV démarré")
            self.export_widget.set_export_status("EN COURS")
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", "Impossible de démarrer l'export CSV")
            self.export_widget.set_export_status("ARRÊTÉ")

    def _stop_export_csv(self):
        """Arrêt export CSV uniquement (jamais l'acquisition série)"""
        if self.metaManager.is_exporting_csv:
            self.metaManager.stop_export_csv()
            self.status_bar.showMessage("Export CSV arrêté")
            self.export_widget.set_export_status("ARRÊTÉ")
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "Export", "Aucun export CSV en cours.")
            self.export_widget.set_export_status("ARRÊTÉ")

    # =========================
    # LOGIQUE DESCENDANTE MANAGER --> UI
    # =========================

    # === FROM STAGE MANAGER ===
    def _on_position_changed(self, x_inc, y_inc):
        x_cm = inc_to_cm(x_inc)
        y_cm = inc_to_cm(y_inc)
        self.visual_widget_main.set_current_position(x_cm, y_cm)

    def update_mode_status(self):
        mode = self.metaManager.mode
        if mode == self.metaManager.MODE_EXPLORATION:
            # self.mode_status_label.setText("Mode : Exploration") # This line was not in the original file, so it's commented out.
            pass # No label to update in this class
        else:
            # self.mode_status_label.setText("Mode : Export (UI bloquée)") # This line was not in the original file, so it's commented out.
            pass # No label to update in this class

    def _on_state_changed(self, state):
        if state == "ui_buttons_disabled":
            self._set_all_buttons_enabled(False)
        elif state == "ui_buttons_enabled":
            self._set_all_buttons_enabled(True)

    def _set_all_buttons_enabled(self, enabled):
        widgets = [
            # Onglet 2 - Paramètres vitesse
            self.speed_params.apply_btn,
            # Onglet principal - Contrôles axes
            self.x_control_main.move_btn, self.x_control_main.home_btn, self.x_control_main.stop_btn, self.x_control_main.emergency_btn,
            self.y_control_main.move_btn, self.y_control_main.home_btn, self.y_control_main.stop_btn, self.y_control_main.emergency_btn,
            self.home_both_btn_main,  # Bouton Home Both X+Y
            # Note: emergency_stop_btn_main n'est volontairement PAS dans cette liste - il doit toujours rester actif
            self.x_control_main.target_input, self.y_control_main.target_input,
            # Onglet principal - Scan 2D
            self.visualization_scan_btn_main, self.execute_btn_main,
            self.xmin_input_main, self.xmax_input_main, self.ymin_input_main, self.ymax_input_main,
            self.n_input_main, self.mode_combo_main
        ]
        
        # Ajout des paramètres de vitesse (onglet 2)
        for axis in ["x", "y"]:
            for param in ["ls", "hs", "acc", "dec"]:
                widgets.append(self.speed_params.params[axis][param])
        
        # Activation/désactivation de tous les widgets
        for w in widgets:
            w.setEnabled(enabled)

    # === FROM ACQUISITION MANAGER ===

    def _on_acquisition_config_changed(self, config: dict):
        """Synchronisation des paramètres du Manager vers tous les widgets"""
        # print(f"[DEBUG GUI] _on_acquisition_config_changed reçu: {config}")
        
        # Synchronisation onglet 3
        self.main_params.set_configuration(config)
        # Synchronisation onglet expérimental
        if hasattr(self, 'main_params_main'):
            self.main_params_main.set_configuration(config)
        
        # Synchronisation onglet 4 (avancés) - COMPLÈTE
        if hasattr(self, 'advanced_settings') and self.advanced_settings is not None:
            print(f"[DEBUG GUI] Synchronisation onglet DDS+ADC avec config: {list(config.keys())}")
            
            # === Fréquence globale ===
            if 'freq_hz' in config:
                if hasattr(self.advanced_settings, 'freq_spin'):
                    print(f"[DEBUG GUI] Setting freq_spin to {config['freq_hz']}")
                    self.advanced_settings.freq_spin.setValue(config['freq_hz'])
            
            # === DDS Gains ===
            if 'gain_dds' in config:
                print(f"[DEBUG GUI] Setting DDS1&2 gain to {config['gain_dds']}")
                for dds_num in [1, 2]:
                    if hasattr(self.advanced_settings, 'dds_controls') and dds_num in self.advanced_settings.dds_controls:
                        print(f"[DEBUG GUI] Calling set_gain on DDS{dds_num}")
                        self.advanced_settings.dds_controls[dds_num].set_gain(config['gain_dds'])
            
            # === DDS Gains individuels (avec synchronisation) ===
            for dds_num in [1, 2]:
                key = f'gain_dds{dds_num}'
                if key in config:
                    if hasattr(self.advanced_settings, 'dds_controls') and dds_num in self.advanced_settings.dds_controls:
                        gain_value = config[key]
                        print(f"[DEBUG GUI] 🔄 Synchronisation DDS{dds_num} gain: {gain_value}")
                        self.advanced_settings.dds_controls[dds_num].set_gain(gain_value)
            
            # === DDS3 & DDS4 Gains (détection synchrone, pas de synchronisation) ===
            for dds_num in [3, 4]:
                key = f'gain_dds{dds_num}'
                if key in config:
                    if hasattr(self.advanced_settings, 'dds_controls') and dds_num in self.advanced_settings.dds_controls:
                        self.advanced_settings.dds_controls[dds_num].set_gain(config[key])
            
            # === DDS Phases ===
            for dds_num in [1, 2, 3, 4]:
                key = f'phase_dds{dds_num}'
                if key in config:
                    if hasattr(self.advanced_settings, 'dds_controls') and dds_num in self.advanced_settings.dds_controls:
                        self.advanced_settings.dds_controls[dds_num].set_phase(config[key])
            
            # === ADC Gains ===
            for ch in [1, 2, 3, 4]:
                key = f'adc_gain_ch{ch}'
                if key in config:
                    if hasattr(self.advanced_settings, 'adc_control'):
                        self.advanced_settings.adc_control.set_gain(ch, config[key])
            
            # === ADC Timing & References ===
            timing_keys = ['clkin', 'iclk', 'oversampling']
            if any(key in config for key in timing_keys):
                if hasattr(self.advanced_settings, 'adc_control'):
                    timing_config = {k: config[k] for k in timing_keys if k in config}
                    self.advanced_settings.adc_control.set_timing_config(timing_config)
            
            ref_keys = ['negative_ref', 'high_res', 'ref_voltage', 'ref_selection']
            if any(key in config for key in ref_keys):
                if hasattr(self.advanced_settings, 'adc_control'):
                    ref_config = {k: config[k] for k in ref_keys if k in config}
                    self.advanced_settings.adc_control.set_reference_config(ref_config)
        
        # Synchronisation widget direction d'excitation (onglet principal)
        if hasattr(self, 'excitation_widget_main'):
            # Synchronisation complète avec la configuration hardware
            # print(f"[DEBUG GUI] Synchronisation ExcitationDirectionWidget avec config: {config}")
            self.excitation_widget_main.sync_from_hardware_config(config)

    def _on_mode_changed(self, mode):
        if mode == 'exploration':
            # Onglet 3
            self.main_params.set_enabled(True)
            self.export_widget.set_enabled(True)
            # Onglet 4
            self.advanced_settings.set_enabled(True)
            # Onglet expérimental
            if hasattr(self, 'main_params_main'):
                self.main_params_main.set_enabled(True)
            if hasattr(self, 'export_widget_main'):
                self.export_widget_main.set_enabled(True)
            self.status_bar.showMessage("Mode Exploration actif")
        else:
            # Onglet 3
            self.main_params.set_enabled(False)
            self.export_widget.set_enabled(False)
            # Onglet 4
            self.advanced_settings.set_enabled(False)
            # Onglet expérimental
            if hasattr(self, 'main_params_main'):
                self.main_params_main.set_enabled(False)
            if hasattr(self, 'export_widget_main'):
                self.export_widget_main.set_enabled(False)
            self.status_bar.showMessage("Mode Export actif - Synchronisation maintenue")

    def _on_error_occurred(self, error_msg: str):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Erreur Acquisition", error_msg)
        self.status_bar.showMessage(f"Erreur: {error_msg}")

    def _update_display_raw(self, sample):
        """Mise à jour avec les données brutes de l'acquisition (reçues via signal)"""
        try:
            if sample and hasattr(self, 'display_widget_main'):
                
                # Affichage conditionnel selon le mode
                adc_values = {
                    'Ex In-Phase': sample.adc1_ch1,
                    'Ex Quadrature': sample.adc1_ch2,
                    'Ey In-Phase': sample.adc1_ch3,
                    'Ey Quadrature': sample.adc1_ch4,
                    'Ez In-Phase': sample.adc2_ch1,
                    'Ez Quadrature': sample.adc2_ch2
                }
                self.display_widget_main.update_values(adc_values)   

            if hasattr(self, 'graph_widget_main'):
                self.graph_widget_main.update_graph()
                
        except Exception as e:
            print(f"[GUI] Erreur raw: {e}")

    # Modifier _update_display_processed pour afficher les corrections

    def _update_display_processed(self, processed_samples):
        """Mise à jour avec les données post-traitées (reçues via signal)"""
        try:
            if processed_samples and len(processed_samples) > 0 and hasattr(self, 'display_widget_main'):
                
                sample = processed_samples[0]  # Premier échantillon traité
                
                # Affichage conditionnel selon le mode
                adc_values = {
                    'Ex In-Phase': sample.adc1_ch1,
                    'Ex Quadrature': sample.adc1_ch2,
                    'Ey In-Phase': sample.adc1_ch3,
                    'Ey Quadrature': sample.adc1_ch4,
                    'Ez In-Phase': sample.adc2_ch1,
                    'Ez Quadrature': sample.adc2_ch2
                }
                self.display_widget_main.update_values(adc_values)   

            # Mise à jour du graphique
            if hasattr(self, 'graph_widget_main'):
                self.graph_widget_main.update_graph()
                
        except Exception as e:
            print(f"[GUI] ERREUR processed: {e}")

    # Corriger _display_correction_info pour gérer l'absence de données

    def _display_correction_info(self):
        """Affiche les valeurs de correction actives"""
        try:
            info = self.metaManager.get_post_processing_info()
            
            # Créer un résumé lisible
            active_ops = []
            
            # Vérifier chaque type de correction
            for key, data in info.items():
                    
                if data.get('active', False):
                    values = data.get('values', {})
                    # Formater les valeurs significatives
                    formatted_values = []
                    for k, v in values.items():
                        if abs(v) > 0.001:
                            formatted_values.append(f"{k}: {v:.2f}")
                    
                    if formatted_values:
                        active_ops.append(f"{key.upper()}: {', '.join(formatted_values)}")
            
            if active_ops:
                status_msg = " | ".join(active_ops)
                self.status_bar.showMessage(status_msg[:100])  # Limiter la longueur
                print(f"[GUI] Corrections: {status_msg}")
            else:
                self.status_bar.showMessage("Aucune correction active")
                
        except Exception as e:
            print(f"[GUI] Erreur affichage corrections: {e}")
            self.status_bar.showMessage("Erreur corrections")

    def _format_correction_values(self, values_dict):
        """Formate les valeurs de correction pour l'affichage"""
        if not values_dict:
            return "Aucune"
        
        formatted = []
        for key, value in values_dict.items():
            if abs(value) > 0.001:  # Afficher seulement les valeurs significatives
                formatted.append(f"{key}: {value:.3f}")
        
        return ", ".join(formatted) if formatted else "Nulle"

    def _on_post_processing_toggled(self, enabled: bool):
        """Gère l'activation/désactivation du post-processing"""
        print(f"[GUI] === MODE CHANGE === Post-processing toggle: {enabled}")
        
        try:
            # Vérifier l'état actuel
            has_enabled = hasattr(self.metaManager, 'post_processing_enabled')
            has_signal = hasattr(self.metaManager, 'post_processed_data_ready')
            has_method = hasattr(self.metaManager, 'set_post_processing_enabled')
            print(f"[GUI] MetaManager capabilities - enabled: {has_enabled}, signal: {has_signal}, method: {has_method}")
            
            if has_method:
                print(f"[GUI] Appel de set_post_processing_enabled({enabled})")
                self.metaManager.set_post_processing_enabled(enabled)
                print(f"[GUI] Mode post-processing défini: {'ACTIVÉ' if enabled else 'DÉSACTIVÉ'}")
                
                # Vérifier si le changement a été pris en compte
                if hasattr(self.metaManager, 'post_processing_enabled'):
                    actual_state = self.metaManager.post_processing_enabled
                    print(f"[GUI] État confirmé: {actual_state}")
                
                # Vérifier aussi le display_mode
                if hasattr(self.metaManager, 'display_mode'):
                    display_mode = self.metaManager.display_mode
                    print(f"[GUI] Display mode: {display_mode}")
                
            else:
                print("[GUI] ERREUR: MetaManager.set_post_processing_enabled non trouvé")
                
            status = "ACTIVÉ" if enabled else "DÉSACTIVÉ"
            self.status_bar.showMessage(f"Post-processing {status}")
            
        except Exception as e:
            print(f"[GUI] ERREUR toggle: {e}")
            import traceback
            traceback.print_exc()

    def _add_post_processing_indicator(self):
        """Ajoute un indicateur visuel de l'état du post-processing"""
        if hasattr(self, 'status_bar'):
            self.post_processing_label = QLabel("Post-Processing: OFF")
            self.post_processing_label.setStyleSheet("QLabel { color: #E63946; font-weight: bold; }")
            self.status_bar.addPermanentWidget(self.post_processing_label)
    
    def _update_post_processing_indicator(self, enabled: bool):
        """Met à jour l'indicateur visuel"""
        if hasattr(self, 'post_processing_label'):
            if enabled:
                self.post_processing_label.setText("Post-Processing: ON")
                self.post_processing_label.setStyleSheet("QLabel { color: #2A9D8F; font-weight: bold; }")
            else:
                self.post_processing_label.setText("Post-Processing: OFF")
                self.post_processing_label.setStyleSheet("QLabel { color: #E63946; font-weight: bold; }")

    def _setup_unit_synchronization(self):
        """🔄 Configuration de la synchronisation des unités entre NumericDisplay et RealtimeGraph"""
        
        # === ONGLET 3 : Acquisition/Export ===
        if hasattr(self, 'display_widget') and hasattr(self, 'graph_widget'):
            # print("[DEBUG GUI] Configuration sync onglet 3 (Acquisition/Export)")
            self.display_widget.sync_callback = self._sync_conversion_to_graph_tab3
            # Synchronisation initiale
            initial_unit = self.display_widget.get_current_unit()
            initial_factor = self.display_widget.get_v_to_vm_factor()
            print(f"[DEBUG GUI] Sync initiale onglet 3: unit={initial_unit}, factor={initial_factor}")
            self.graph_widget.set_conversion_parameters(initial_unit, initial_factor)
        
        # === ONGLET PRINCIPAL ===
        if hasattr(self, 'display_widget_main') and hasattr(self, 'graph_widget_main'):
            # print("[DEBUG GUI] Configuration sync onglet principal")
            self.display_widget_main.sync_callback = self._sync_conversion_to_graph_main
            # Synchronisation initiale
            initial_unit = self.display_widget_main.get_current_unit()
            initial_factor = self.display_widget_main.get_v_to_vm_factor()
            print(f"[DEBUG GUI] Sync initiale onglet principal: unit={initial_unit}, factor={initial_factor}")
            self.graph_widget_main.set_conversion_parameters(initial_unit, initial_factor)

    def _sync_conversion_to_graph_tab3(self):
        """Synchronisation unités onglet 3 : NumericDisplay → RealtimeGraph"""
        if hasattr(self, 'graph_widget'):
            unit = self.display_widget.get_current_unit()
            factor = self.display_widget.get_v_to_vm_factor()
            print(f"[DEBUG GUI] Sync onglet 3: unit={unit}, factor={factor}")
            self.graph_widget.set_conversion_parameters(unit, factor)

    def _sync_conversion_to_graph_main(self):
        """Synchronisation unités onglet principal : NumericDisplay → RealtimeGraph"""
        if hasattr(self, 'graph_widget_main'):
            unit = self.display_widget_main.get_current_unit()
            factor = self.display_widget_main.get_v_to_vm_factor()
            print(f"[DEBUG GUI] Sync onglet principal: unit={unit}, factor={factor}")
            self.graph_widget_main.set_conversion_parameters(unit, factor)

    def _sync_conversion_to_graph(self):
        """Méthode legacy - utilise maintenant les méthodes spécialisées"""
        self._sync_conversion_to_graph_tab3()

    def _setup_frame_rotation(self):
        """🔄 Configuration du contrôle de rotation de référentiel"""
        
        # === ONGLET 3 : Acquisition/Export ===
        if hasattr(self, 'rotation_widget'):
            # print("[DEBUG GUI] Configuration rotation onglet 3 (Acquisition/Export)")
            
            # Connexion signaux widget → metaManager
            self.rotation_widget.frame_changed.connect(self._on_frame_changed_tab3)
            self.rotation_widget.angles_changed.connect(self._on_angles_changed_tab3)
            
            # Synchronisation initiale avec l'état du manager
            current_frame = self.metaManager.get_display_frame()
            current_angles = self.metaManager.get_rotation_angles()
            self.rotation_widget.update_status_from_manager(current_frame, current_angles)
        
        # === ONGLET PRINCIPAL ===
        if hasattr(self, 'rotation_widget_main'):
            # print("[DEBUG GUI] Configuration rotation onglet principal")
            
            # Connexion signaux widget → metaManager
            self.rotation_widget_main.frame_changed.connect(self._on_frame_changed_main)
            self.rotation_widget_main.angles_changed.connect(self._on_angles_changed_main)
            
            # Synchronisation initiale avec l'état du manager
            current_frame = self.metaManager.get_display_frame()
            current_angles = self.metaManager.get_rotation_angles()
            self.rotation_widget_main.update_status_from_manager(current_frame, current_angles)

    def _on_frame_changed_tab3(self, frame: str):
        """Changement de référentiel d'affichage onglet 3"""
        print(f"[DEBUG GUI] Référentiel changé onglet 3: {frame}")
        self.metaManager.set_display_frame(frame)
    
    def _on_angles_changed_tab3(self, theta_x: float, theta_y: float, theta_z: float):
        """Changement d'angles de rotation onglet 3"""
        print(f"[DEBUG GUI] Angles changés onglet 3: θx={theta_x:.2f}°, θy={theta_y:.2f}°, θz={theta_z:.2f}°")
        self.metaManager.set_rotation_angles(theta_x, theta_y, theta_z)
    
    def _on_frame_changed_main(self, frame: str):
        """Changement de référentiel d'affichage onglet principal"""
        print(f"[DEBUG GUI] Référentiel changé onglet principal: {frame}")
        self.metaManager.set_display_frame(frame)
        
        # Synchronisation avec l'autre widget
        if hasattr(self, 'rotation_widget'):
            self.rotation_widget.update_status_from_manager(frame)
    
    def _on_angles_changed_main(self, theta_x: float, theta_y: float, theta_z: float):
        """Changement d'angles de rotation onglet principal"""
        print(f"[DEBUG GUI] Angles changés onglet principal: θx={theta_x:.2f}°, θy={theta_y:.2f}°, θz={theta_z:.2f}°")
        self.metaManager.set_rotation_angles(theta_x, theta_y, theta_z)
        
        # Synchronisation avec l'autre widget
        if hasattr(self, 'rotation_widget'):
            self.rotation_widget.set_rotation_angles(theta_x, theta_y, theta_z)



    # =========================
    # METHODES INTERNES
    # =========================

    # Méthode supprimée - remplacée par _update_subrect_from_ui_main()

    # === MÉTHODES SPÉCIFIQUES ONGLET EXPÉRIMENTAL ===
    
    def move_to_main(self, axis):
        """Move_to spécifique pour l'onglet expérimental"""
        print(f"[DEBUG UI-EXP] move_to_main appelé pour axe {axis}")
        
        # Vérification homing comme dans move_to()
        if not self.metaManager.managers['stage'].controller.get_axis_homed_status(axis):
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "Homing requis", f"L'axe {axis.upper()} n'est pas homed. Veuillez faire le homing d'abord.")
            print(f"[DEBUG UI-EXP] Commande move_to_main bloquée - axe {axis} non homed")
            return
        
        print(f"[DEBUG UI-EXP] Envoi de la commande move_to vers MetaManager pour axe {axis}")
        target = getattr(self, f"{axis}_control_main").get_target_position()
        target_inc, _ = cm_to_inc(target)
        self.metaManager.move_to(axis, target_inc)

    def home_both_lock_main(self):
        """Home Both X+Y spécifique pour l'onglet expérimental (bloquant)"""
        print("[DEBUG UI-EXP] home_both_lock_main appelé")
        try:
            self.metaManager.home_both_lock()
            self.status_bar.showMessage("🏠 Homing X+Y terminé (bloquant)")
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur homing X+Y (EXP): {e}")

    def emergency_stop_both_main(self):
        """Arrêt d'urgence des deux axes pour l'onglet expérimental"""
        print("[DEBUG UI-EXP] emergency_stop_both_main appelé")
        try:
            # Arrêt d'urgence immédiat sur les deux axes
            self.metaManager.stop("x", immediate=True)
            self.metaManager.stop("y", immediate=True)
            self.status_bar.showMessage("🚨 ARRÊT D'URGENCE X+Y ACTIVÉ")
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur arrêt d'urgence (EXP): {e}")

    def _on_position_changed_main(self, x_inc, y_inc):
        """Mise à jour position pour l'onglet expérimental"""
        x_cm = inc_to_cm(x_inc)
        y_cm = inc_to_cm(y_inc)
        self.visual_widget_main.set_current_position(x_cm, y_cm)

    def _update_subrect_from_ui_main(self):
        """Mise à jour sous-rectangle depuis l'UI expérimentale"""
        x_min = self.xmin_input_main.value()
        x_max = self.xmax_input_main.value()
        y_min = self.ymin_input_main.value()
        y_max = self.ymax_input_main.value()
        self.visual_widget_main.set_subrect(x_min, x_max, y_min, y_max)

    def _execute_scan2d_from_ui_main(self):
        """Exécution scan 2D depuis l'UI expérimentale"""
        x_min_cm = self.xmin_input_main.value()
        x_max_cm = self.xmax_input_main.value()
        y_min_cm = self.ymin_input_main.value()
        y_max_cm = self.ymax_input_main.value()

        N = self.n_input_main.value()
        mode_str = self.mode_combo_main.currentText()
        mode = 'E' if mode_str.startswith('E') else 'S'
        
        # Conversion cm -> inc
        x_min_inc, _ = cm_to_inc(x_min_cm)
        x_max_inc, _ = cm_to_inc(x_max_cm)
        y_min_inc, _ = cm_to_inc(y_min_cm)
        y_max_inc, _ = cm_to_inc(y_max_cm)
        
        # Numbers of lines and rows for post-processing
        x_nb = N 
        y_nb = int(self.y_nb_input_main.value())

        # timer_ms for post-processing
        timer_ms = int(self.timer_ms_input_main.value())
        # Configuration export avec le chemin de l'UI et option de filtrage
        export_config = {
            "output_dir": self.export_path_input.text(),
            "filename_base": "Default",
            "filter_active_lines_only": self.filter_active_lines_checkbox.isChecked()
        }
        
        # Génération et exécution
        scan_config = self.metaManager.generate_scan_config(
            x_min_inc, x_max_inc, y_min_inc, y_max_inc, x_nb, mode,
            y_nb=int(self.y_nb_input_main.value()),
            timer_ms=int(self.timer_ms_input_main.value())
        )
        self._set_all_buttons_enabled(False)
        self.status_bar.showMessage("⏳ Scan 2D en cours... (EXPÉRIMENTAL)")
        
        try:
            # L'export sera automatiquement démarré dans inject_scan_batch
            self.metaManager.inject_scan_batch(scan_config)
            self.status_bar.showMessage("✅ Scan 2D injecté (batch) avec export CSV - EXPÉRIMENTAL")
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur exécution scan (EXP) : {e}")
        finally:
            self._set_all_buttons_enabled(True)

    def _execute_scan2d_from_ui(self):
        x_min_cm = self.xmin_input.value()
        x_max_cm = self.xmax_input.value()
        y_min_cm = self.ymin_input.value()
        y_max_cm = self.ymax_input.value()
        N = self.n_input.value()
        mode_str = self.mode_combo.currentText()
        mode = 'E' if mode_str.startswith('E') else 'S'
        x_min_inc, _ = cm_to_inc(x_min_cm)
        x_max_inc, _ = cm_to_inc(x_max_cm)
        y_min_inc, _ = cm_to_inc(y_min_cm)
        y_max_inc, _ = cm_to_inc(y_max_cm)
        scan_config = self.metaManager.generate_scan_config(
            x_min_inc, x_max_inc, y_min_inc, y_max_inc, N, mode,
            y_nb=int(self.y_nb_input_main.value()),
            timer_ms=int(self.timer_ms_input_main.value())
        )
        self._set_all_buttons_enabled(False)
        self.status_bar.showMessage("⏳ Scan 2D en cours...")
        try:
            self.metaManager.inject_scan_batch(scan_config)
            self.status_bar.showMessage("✅ Scan 2D injecté (batch)")
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur exécution scan : {e}")
        finally:
            self._set_all_buttons_enabled(True)


    def _on_scan_status_changed(self, status):
        """Gestion des changements de statut du scan"""
        if status == 'scan2d_finished':
            self.status_bar.showMessage("✅ Scan 2D terminé - Export CSV arrêté automatiquement")
            # Réactiver les boutons si nécessaire
            self._set_all_buttons_enabled(True)
            


    # === MÉTHODES SPÉCIFIQUES POST-PROCESSING ===


    def _on_calibration_completed(self, step: str, result: dict):
        """Gère la fin d'une calibration"""
        QMessageBox.information(self, "Calibration", f"{step} terminé avec succès!")

    def _on_post_processing_changed(self, enabled: bool):
        """Gère les changements d'état du post-processing"""
        try:
            status = "activé" if enabled else "désactivé"
            print(f"[DEBUG] Post-processing {status}")
            self.status_bar.showMessage(f"Post-processing {status}")
            
            # Mise à jour de l'indicateur visuel
            self._update_post_processing_indicator(enabled)
            
            # Nettoyer l'affichage lors du changement d'état
            if hasattr(self, 'display_widget_main') and hasattr(self.display_widget_main, 'clear_values'):
                self.display_widget_main.clear_values()
                
        except Exception as e:
            print(f"[DEBUG] Erreur changement état post-processing: {e}")

    # METHODE DE FERMETURE PROPRE


    def _stop_export_main(self):
        """Arrête l'export CSV en cours"""
        try:
            success = self.metaManager.stop_export_csv()
            if success:
                self.status_bar.showMessage("✅ Export CSV arrêté")
            else:
                self.status_bar.showMessage("⚠️ Aucun export en cours")
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur arrêt export: {e}")

    def closeEvent(self, event):
        print("[DEBUG] Fermeture de l'application")
        try:
            # Déconnecter les signaux
            if hasattr(self, 'metaManager'):
                self.metaManager.data_ready.disconnect(self._update_display_raw)
                if hasattr(self.metaManager, 'post_processed_data_ready'):
                    self.metaManager.post_processed_data_ready.disconnect(self._update_display_processed)
                if hasattr(self.metaManager, 'post_processing_changed'):
                    self.metaManager.post_processing_changed.disconnect(self._on_post_processing_changed)
                print("[DEBUG] Signals déconnectés")
            self.metaManager.close()
        except Exception as e:
            print(f"[DEBUG] Erreur fermeture: {e}")
        event.accept()

def main():
    app = QApplication(sys.argv)
    # Appliquer le style Fusion et la palette sombre AVANT toute création de widget
    app.setStyle('Fusion')
    from PyQt5.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, QColor(0, 0, 0))
    palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)
    window = EFImagingBenchMainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
