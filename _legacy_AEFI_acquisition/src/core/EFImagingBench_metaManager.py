# -*- coding: utf-8 -*-
from PyQt5.QtCore import QObject, pyqtSignal, QThread

import sys
import os
import numpy as np
import threading
from typing import List, Dict, Any

import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import des managers existants
from .ArcusPerfomax4EXStage.components.ArcusPerfomax4EXStage_StageManager import StageManager
from .AD9106_ADS131A04_ElectricField_3D.components.AD9106_ADS131A04_acquisition_manager import AcquisitionManager
from .components.EFImagingBench_PostProcessing_Module import PostProcessingManager
from .components.EFImagingBench_ExcitationDirection_Module import ExcitationConfig
from .components.EFImagingBench_CSVExporter_Module import EFImagingBenchCSVExporter, ExportConfig
from .components.EFImagingBench_AutoCalibration_Module import AutoCalibrationThread

from datetime import datetime
# Assume PositionSample ; si non, définit un simple ici ou importe correctement
# Exemple : from core.ArcusPerfomax4EXStage.components.EFImagingBench_DataBuffer_Module import PositionSample

from dataclasses import dataclass
@dataclass
class PositionSample:
    x: float
    y: float
    timestamp: datetime




class MetaManager(QObject):
    """
    MetaManager centralisant la gestion des sous-managers (moteurs, excitation, etc.)
    - Fournit une API publique pour des clients externes (UI, scripts, etc.)
    - Relaye les signaux importants des sous-managers
    - Permet la synchronisation et l'orchestration multi-systèmes
    """

    # Constantes de mode centralisées
    MODE_EXPLORATION = "exploration"
    MODE_EXPORT = "export"

    # Signaux publiques pour l'UI globale
    error_occurred = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    data_ready = pyqtSignal(object)  # Pour compatibilité ElectricFieldGUI
    configuration_changed = pyqtSignal(dict)
    mode_changed = pyqtSignal(object)
    position_changed = pyqtSignal(float, float)  # Pour compatibilité ArcusGUIModern
    #data_ready_stage = pyqtSignal(object)
    data_ready_acquisition = pyqtSignal(object)
    configuration_changed_stage = pyqtSignal(dict)
    configuration_changed_acquisition = pyqtSignal(dict)
    mode_changed_stage = pyqtSignal(object)
    mode_changed_acquisition = pyqtSignal(object)
    post_processing_changed = pyqtSignal(dict)  # État du post-processing
    calibration_requested = pyqtSignal(str)  # type de calibration
    
    # Signaux séparés pour chaque type de calibration
    offset_exc_off_calibration_completed = pyqtSignal(dict)  # result
    phase_calibration_completed = pyqtSignal(dict)  # result  
    offset_exc_on_calibration_completed = pyqtSignal(dict)  # result
    frame_rotation_calibration_completed = pyqtSignal(dict)  # result
    
    # Signal générique pour compatibilité (à supprimer plus tard)
    calibration_completed = pyqtSignal(str, dict)  # type, résultat
    # Signal pour les données post-traitées
    post_processed_data_ready = pyqtSignal(list)
    # Signal pour progression du cycle auto-calibration
    auto_compensation_progress = pyqtSignal(str, str)  # phase du cycle, status
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mode = None  # Ajout de l'attribut mode
        # Instanciation des sous-managers
        self.managers = {}
        self.managers['stage'] = StageManager()
        self.managers['acquisition'] = AcquisitionManager()
        self.csv_exporter = EFImagingBenchCSVExporter()
        self.excitation_config = ExcitationConfig()
        # Création et ajout du PostProcessingManager
        # Mode d'affichage
        self.display_mode = 'raw'  # 'raw' ou 'processed'
        self.post_processing_enabled = False  # Ajout de l'attribut manquant
        self.post_processor = PostProcessingManager()
        self.add_manager('post_processor', self.post_processor)
        
        # ACTIVER le post-processing par défaut
        self.post_processing_enabled = True
        self.display_mode = "processed"
        print("[META] Post-processing activé par défaut")
        
        print(f"[MetaManager] Initialisation - display_mode: {self.display_mode}, post_processing_enabled: {self.post_processing_enabled}")
        
        # Thread de post-processing
        self._processing_thread = None
        self._processing_running = False
        self._processing_queue = []
        self._processing_lock = threading.Lock()
        
        # Calibration state
        self._calibration_state = None
        self._calibration_lock = threading.Lock()
        
        # Start processing thread
        self._start_processing_thread()
        
        # Connexion des signaux des sous-managers vers le metaManager
        self._connect_signals()
        
    def _connect_signals(self):
        # Relais des erreurs
        self.managers['stage'].error_occurred.connect(lambda msg: (print(f'[MetaManager] Reçu error_occurred (stage): {msg}'), self.error_occurred.emit(f"[stage] {msg}")))
        self.managers['acquisition'].error_occurred.connect(lambda msg: (print(f'[MetaManager] Reçu error_occurred (acquisition): {msg}'), self.error_occurred.emit(f"[acquisition] {msg}")))
        # Relais des statuts
        self.managers['stage'].status_changed.connect(lambda status: (print(f'[MetaManager] Reçu status_changed (stage): {status}'), self.status_changed.emit(f"[stage] {status}")))
        self.managers['acquisition'].status_changed.connect(lambda status: (print(f'[MetaManager] Reçu status_changed (acquisition): {status}'), self.status_changed.emit(f"[acquisition] {status}")))
        # Relais des signaux data_ready (si présents)
        if hasattr(self.managers['stage'], 'data_ready'):
            self.managers['stage'].data_ready.connect(lambda data: (print(f'[MetaManager] Reçu data_ready (stage)'), self.data_ready_stage.emit(data)))
        if hasattr(self.managers['acquisition'], 'data_ready'):
           self.managers['acquisition'].data_ready.connect(self._on_acquisition_data_ready)
           self.managers['acquisition'].data_ready.connect(self.data_ready.emit)# # Relais des changements de configuration
        if hasattr(self.managers['stage'], 'configuration_changed'):
            self.managers['stage'].configuration_changed.connect(lambda conf: (print(f'[MetaManager] Reçu configuration_changed (stage): {conf}'), self.configuration_changed_stage.emit(conf)))
        if hasattr(self.managers['acquisition'], 'configuration_changed'):
            self.managers['acquisition'].configuration_changed.connect(lambda conf: (print(f'[MetaManager] Reçu configuration_changed (acquisition): {conf}'), self.configuration_changed_acquisition.emit(conf), self.configuration_changed.emit(conf)))
        # Relais du signal post-processing
        if hasattr(self.managers['acquisition'], 'post_processing_changed'):
            self.managers['acquisition'].post_processing_changed.connect(lambda info: self.post_processing_changed.emit(info))
        # Relais des changements de mode
        if hasattr(self.managers['stage'], 'mode_changed'):
            self.managers['stage'].mode_changed.connect(self._on_stage_mode_changed)
        if hasattr(self.managers['acquisition'], 'mode_changed'):
            self.managers['acquisition'].mode_changed.connect(self._on_acquisition_mode_changed)
        # # Relais du signal position_changed pour compatibilité ArcusGUIModern
        if hasattr(self.managers['stage'], 'position_changed'):
             self.managers['stage'].position_changed.connect(lambda x, y: self.position_changed.emit(x, y))
        # Ajoute ici d'autres relais directs si besoin (ex : data_ready, etc.)
        self.calibration_requested.connect(self._on_calibration_requested)
        self.calibration_completed.connect(self._on_calibration_completed)

    def _on_calibration_requested(self, calibration_type: str):
        """Gère une demande de calibration depuis l'UI"""
        print(f"[META] Calibration demandée: {calibration_type}")
        
        with self._calibration_lock:
            if self._calibration_state is not None:
                print("[META] Calibration déjà en cours, ignorée")
                return
            
            # Initialize calibration state
            self._calibration_state = {
                'type': calibration_type,
                'status': 'pending',
                'start_time': datetime.now()
            }
            
            # Lancer la vraie calibration
            if self.post_processor is not None:
                print(f"[META] Lancement calibration: {calibration_type}")
                # Utiliser request_buffer_calibration comme l'autocalib
                result = self.request_buffer_calibration(calibration_type)
                if result:
                    print(f"[META] Calibration terminée: {result}")
                    # Activer la compensation
                    if calibration_type in self.post_processor.config.compensation_active:
                        self.post_processor.config.compensation_active[calibration_type] = True
                    
                    # Émettre le signal spécifique selon le type de calibration
                    print(f"[META] Émission signal spécifique pour: {calibration_type}")
                    if calibration_type == 'offset_exc_off':
                        self.offset_exc_off_calibration_completed.emit(result)
                    elif calibration_type == 'phase':
                        self.phase_calibration_completed.emit(result)
                    elif calibration_type == 'offset_exc_on':
                        self.offset_exc_on_calibration_completed.emit(result)
                    elif calibration_type == 'frame_rotation':
                        self.frame_rotation_calibration_completed.emit(result)
                    else:
                        print(f"[META] Type de calibration inconnu: {calibration_type}")
                        self.calibration_completed.emit(calibration_type, result)  # Fallback
                    
                    # IMPORTANT: Nettoyer l'état de calibration pour permettre la suivante
                    print(f"[META] Nettoyage de l'état de calibration pour: {calibration_type}")
                    self._calibration_state = None
                else:
                    print("[META] Calibration échouée")
                    self._calibration_state = None
            else:
                print("[META] ERREUR: post_processor non disponible")
                self._calibration_state = None
    def _on_calibration_completed(self, result):
        """Callback pour la fin de la calibration"""
        print(f"[META] Calibration terminée: {result}")
        
        # Debug : état actuel des compensations
        current_state = self.post_processor.config.compensation_active
        print(f"[META DEBUG] État compensations avant émission: {current_state}")
        
        # Émettre le signal UI
        self.post_processing_changed.emit(current_state)
        print(f"[META DEBUG] Signal post_processing_changed émis avec: {current_state}")

    def _on_stage_mode_changed(self, mode):
        print(f'[MetaManager] Reçu mode_changed (stage): {mode}')
        self.mode = mode
        self.mode_changed.emit(mode)

    def _on_acquisition_mode_changed(self, mode):
        print(f'[MetaManager] Reçu mode_changed (acquisition): {mode}')
        self.mode = mode
        self.mode_changed.emit(mode)

    def set_mode(self, mode):
        """Change le mode des sous-managers et met à jour le mode global."""
        if hasattr(self.managers['stage'], 'set_mode'):
            self.managers['stage'].set_mode(mode)
        if hasattr(self.managers['acquisition'], 'set_mode'):
            self.managers['acquisition'].set_mode(mode)
        self.mode = mode
        self.mode_changed.emit(mode)

    # ... Ajoute ici toutes les méthodes de coordination/synchronisation nécessaires

    # Exemple de méthode de synchronisation globale
    def start_scan_and_acquire(self, scan_params, acq_config):
        """
        Lance un scan moteur ET l'acquisition synchrone (exemple de coordination)
        """
        # 1. Configure le scan sur le stage
        scan_batch = self.managers['stage'].generate_scan2d(**scan_params)
        self.managers['stage'].inject_scan_batch(scan_batch)
        # 2. Démarre l'acquisition
        self.managers['acquisition'].start_acquisition('export', acq_config)
        # 3. (Optionnel) Gérer la synchronisation fine via signaux/callbacks

    # Ajout dynamique d'un nouveau manager
    def add_manager(self, name, manager_instance):
        """Permet d'ajouter dynamiquement un nouveau sous-manager"""
        self.managers[name] = manager_instance
        # (Optionnel) connecter ses signaux ici

    # Fermeture propre
    def close(self):
        self.stop_processing_thread()
        for m in self.managers.values():
            if hasattr(m, 'close'):
                m.close()
        self.stop_export_csv()

    # ===============================
    # === API PASS-THROUGH ===
    # ===============================

    # === API PASS-THROUGH EXHAUSTIVE STAGEMANAGER ===
    def move_to(self, axis, position):
        print(f"[MetaManager] Appel move_to : axis={axis}, position={position}")
        print(f"[MetaManager] Relais move_to vers stage : axis={axis}, position={position}")
        return self.managers['stage'].move_to(axis, position)
    def home_lock(self, axis):
        """
        Homing bloquant d'un axe via le StageManager
        """
        print(f"[MetaManager] Appel home_lock : axis={axis}")
        print(f"[MetaManager] Relais home_lock vers stage : axis={axis}")
        
        # Création d'un callback pour capturer le résultat
        def on_home_complete(result):
            print(f"[MetaManager] Homing {axis} terminé avec résultat: {result}")
        
        return self.managers['stage'].home_lock(axis, callback=on_home_complete)
    def home_both_lock(self):
        """
        Homing bloquant simultané X+Y via le StageManager
        """
        print(f"[MetaManager] Appel home_both_lock")
        print(f"[MetaManager] Relais home_both_lock vers stage")
        
        # Création d'un callback pour capturer le résultat
        def on_home_both_complete(result):
            print(f"[MetaManager] Homing X+Y terminé avec résultat: {result}")
        
        return self.managers['stage'].home_both_lock(callback=on_home_both_complete)
    def stop(self, axis, immediate=False):
        print(f"[MetaManager] Appel stop : axis={axis}, immediate={immediate}")
        print(f"[MetaManager] Relais stop vers stage : axis={axis}, immediate={immediate}")
        return self.managers['stage'].stop(axis, immediate)
    def set_axis_params(self, axis, ls=None, hs=None, acc=None, dec=None):
        print(f"[MetaManager] Appel set_axis_params : axis={axis}, ls={ls}, hs={hs}, acc={acc}, dec={dec}")
        print(f"[MetaManager] Relais set_axis_params vers stage : axis={axis}")
        return self.managers['stage'].set_axis_params(axis, ls, hs, acc, dec)
    def get_axis_params(self, axis, callback):
        return self.managers['stage'].get_axis_params(axis, callback)
    def get_position(self, axis, callback):
        return self.managers['stage'].get_position(axis, callback)
    def get_status(self, axis, callback):
        return self.managers['stage'].get_status(axis, callback)
    def is_moving(self, axis="all", callback=None):
        return self.managers['stage'].is_moving(axis, callback)
    def set_position_reference(self, axis, value=0):
        return self.managers['stage'].set_position_reference(axis, value)
    def generate_scan2d(self, x_min, x_max, y_min, y_max, N, mode='E'):
        """Génère les lignes de scan via StageManager (compat exécution)."""
        return self.managers['stage'].generate_scan2d(x_min, x_max, y_min, y_max, N, mode)

    def generate_scan_config(self, x_min, x_max, y_min, y_max, x_nb, mode='E', y_nb=None, timer_ms=None):
        """Construit le dictionnaire de configuration de scan (pour injection)."""
        cfg = {
            'x_min': int(x_min),
            'x_max': int(x_max),
            'y_min': int(y_min),
            'y_max': int(y_max),
            'x_nb': int(x_nb),
            'y_nb': int(y_nb),
            'timer_ms': int(timer_ms),
            'mode': str(mode).upper(),
        }
        return cfg

    def inject_scan_batch(self, batch_commands):
        # Démarrer l'export CSV automatiquement lors d'un scan
        print(f"[MetaManager] inject_scan_batch appelé, démarrage export CSV")
        self.start_export_csv()
        
        # Connecter le signal de changement de segment si pas déjà fait
        if hasattr(self.managers['stage'], 'scan_segment_changed'):
            try:
                # Déconnecter les connexions précédentes pour éviter les doublons
                self.managers['stage'].scan_segment_changed.disconnect()
            except:
                pass
            
            # Connecter pour propager au CSV exporter
            self.managers['stage'].scan_segment_changed.connect(
                lambda seg_id, seg_type, is_active: self.csv_exporter.set_current_segment(seg_id, is_active)
            )
            print("[MetaManager] Signal scan_segment_changed connecté au CSV exporter")
        
        # Connecter le signal de fin de scan pour arrêter l'export automatiquement
        def on_scan_finished(status):
            if status == 'scan2d_finished':
                print("[MetaManager] Scan terminé, arrêt automatique de l'export CSV")
                self.stop_export_csv()
                # Déconnecter le signal après utilisation
                try:
                    self.managers['stage'].status_changed.disconnect(on_scan_finished)
                except:
                    pass
        
        self.managers['stage'].status_changed.connect(on_scan_finished)
        print("[MetaManager] Signal status_changed connecté pour arrêt automatique de l'export")
        
        result = self.managers['stage'].inject_scan_batch(batch_commands)
        return result
        
    def get_latest_position_samples(self, count):
        return self.managers['stage'].get_latest_position_samples(count)
    def get_all_position_samples(self):
        return self.managers['stage'].get_all_position_samples()
    def clear_position_buffer(self):
        return self.managers['stage'].clear_position_buffer()
    def flush_position_buffer_for_export(self):
        return self.managers['stage'].flush_position_buffer_for_export()
    def add_position_production_callback(self, callback):
        return self.managers['stage'].add_position_production_callback(callback)
    def get_bench_limits_cm(self):
        return self.managers['stage'].get_bench_limits_cm()
    def clamp_rect_cm(self, x_min, x_max, y_min, y_max):
        return self.managers['stage'].clamp_rect_cm(x_min, x_max, y_min, y_max)
    def inc_to_cm(self, inc):
        return self.managers['stage'].inc_to_cm(inc)
    def cm_to_inc(self, cm):
        return self.managers['stage'].cm_to_inc(cm)
    @property
    def position_buffer_mode(self):
        return self.managers['stage'].position_buffer_mode
    @property
    def position_buffer_size(self):
        return self.managers['stage'].position_buffer_size

    # === API PASS-THROUGH EXHAUSTIVE ACQUISITIONMANAGER ===
    def start_acquisition(self, mode, config):
        return self.managers['acquisition'].start_acquisition(mode, config)
    def stop_acquisition(self):
        return self.managers['acquisition'].stop_acquisition()
    def pause_acquisition(self):
        return self.managers['acquisition'].pause_acquisition()
    def resume_acquisition(self):
        return self.managers['acquisition'].resume_acquisition()
    def update_configuration(self, config):
        return self.managers['acquisition'].update_configuration(config)
    def get_buffer_status(self):
        return self.managers['acquisition'].get_buffer_status()
    def get_acquisition_stats(self):
        return self.managers['acquisition'].get_acquisition_stats()
    def get_latest_samples(self, n=1):
        return self.managers['acquisition'].get_latest_samples(n)
    def get_all_samples(self):
        return self.managers['acquisition'].get_all_samples()
    def clear_buffer(self):
        return self.managers['acquisition'].clear_buffer()
    def flush_for_export(self):
        return self.managers['acquisition'].flush_for_export()
    def add_production_callback(self, callback):
        return self.managers['acquisition'].add_production_callback(callback)

    def set_channel_gains(self, gains):
        return self.managers['acquisition'].set_channel_gains(gains)
    def set_v_to_vm_factor(self, factor):
        return self.managers['acquisition'].set_v_to_vm_factor(factor)
    def convert_sample(self, sample, gains, target_unit):
        return self.managers['acquisition'].convert_sample(sample, gains, target_unit)
    def convert_adc_to_voltage(self, adc_code, channel):
        return self.managers['acquisition'].convert_adc_to_voltage(adc_code, channel)
    def convert_channel_array(self, adc_codes, start_channel=1):
        return self.managers['acquisition'].convert_channel_array(adc_codes, start_channel)
    def convert_to_units(self, voltage, target_units):
        return self.managers['acquisition'].convert_to_units(voltage, target_units)
    def convert_full_acquisition(self, adc1_data, adc2_data, target_units=None):
        return self.managers['acquisition'].convert_full_acquisition(adc1_data, adc2_data, target_units)
    def get_voltage_range(self, gain):
        return self.managers['acquisition'].get_voltage_range(gain)
    def get_channel_info(self, channel):
        return self.managers['acquisition'].get_channel_info(channel)
    def get_all_channels_info(self):
        return self.managers['acquisition'].get_all_channels_info()
    def clear_adc_cache(self):
        return self.managers['acquisition'].clear_adc_cache()
    @property
    def channel_gains(self):
        return self.managers['acquisition'].channel_gains
    def start_export_csv(self, config_export=None):
        """Démarre l'export CSV avec configuration optionnelle"""
        # Génération timestamp unique pour tous les exports
        timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
        
        # Vérification obligatoire de la configuration d'export
        if config_export is None:
            raise ValueError("Configuration d'export manquante. L'UI doit fournir output_dir et filename_base.")
        
        # Traitement selon le type de config
        if isinstance(config_export, dict):
            # Vérifier les champs obligatoires
            if 'output_dir' not in config_export:
                raise ValueError("output_dir manquant dans la configuration d'export")
            if 'filename_base' not in config_export:
                raise ValueError("filename_base manquant dans la configuration d'export")
            
            output_dir = config_export['output_dir']
            base_name = config_export['filename_base']
            filename_base = f"{timestamp}_{base_name}"
            
            config_export = ExportConfig(
                output_dir=output_dir,
                filename_base=filename_base,
                metadata={**self.get_acquisition_config(), **self.get_stage_config()}
            )
        elif not isinstance(config_export, ExportConfig):
            raise TypeError("config_export doit être un dict ou un ExportConfig")
        
        print(f"[MetaManager] Démarrage export CSV: output_dir={config_export.output_dir}, filename_base={config_export.filename_base}")
        success = self.csv_exporter.start_export(config_export)
        
        if success:
            print("[MetaManager] Export démarré, connexion aux signaux...")
            # Connecter pour capteur - utilise les samples du buffer d'acquisition
            def on_data_ready():
                samples = self.get_latest_samples(1)
                if samples:
                    self.csv_exporter.add_sensor_sample(samples[0])
            
            # Connecter pour position
            def on_position_changed(x, y):
                pos_sample = PositionSample(x=x, y=y, timestamp=datetime.now())
                self.csv_exporter.add_position_sample(pos_sample)
            
            # Stocker les connexions pour pouvoir les déconnecter
            self._export_data_connection = on_data_ready
            self._export_pos_connection = on_position_changed
            
            self.data_ready.connect(self._export_data_connection)
            self.position_changed.connect(self._export_pos_connection)
            
            print("[MetaManager] Export CSV démarré avec succès")
        else:
            print("[MetaManager] Échec du démarrage de l'export CSV")
        
        return success

    def stop_export_csv(self):
        """Arrête l'export CSV et déconnecte les signaux"""
        print("[MetaManager] Arrêt export CSV")
        
        # Déconnecter les signaux
        try:
            if hasattr(self, '_export_data_connection'):
                self.data_ready.disconnect(self._export_data_connection)
            if hasattr(self, '_export_pos_connection'):
                self.position_changed.disconnect(self._export_pos_connection)
        except Exception as e:
            print(f"[MetaManager] Erreur déconnexion signaux: {e}")
        
        return self.csv_exporter.stop_export()
    @property
    def is_exporting_csv(self):
        return self.csv_exporter.is_exporting

    def get_acquisition_config(self):
        """Retourne la configuration courante de l'acquisition (dict)."""
        return self.managers['acquisition']._current_config.copy() if hasattr(self.managers['acquisition'], '_current_config') else {}

    def get_stage_config(self):
        """Retourne la configuration courante du stage (si disponible)."""
        if hasattr(self.managers['stage'], '_current_config'):
            return self.managers['stage']._current_config.copy()
        return {}

    def get_stage_status(self):
        return self.managers['stage'].acquisition_status if hasattr(self.managers['stage'], 'acquisition_status') else None

    def sync_ui_with_hardware(self):
        """Force la synchronisation UI avec l'état hardware actuel"""
        return self.managers['acquisition'].sync_ui_with_hardware()


    # ============================================================
    # SECTION 4: API POST-PROCESSING (PASS-THROUGH VERS PostProcessingManager)
    # ============================================================
    def set_display_frame(self, frame: str) -> bool:
        """Définit le référentiel d'affichage ('sensor' ou 'bench')"""
        return self.post_processor.set_display_frame(frame)
    
    def get_display_frame(self) -> str:
        """Retourne le référentiel d'affichage actuel"""
        return self.post_processor.get_display_frame()
    
    def set_rotation_angles(self, theta_x: float, theta_y: float = None, theta_z: float = 0.0) -> bool:
        """Définit les angles de rotation du référentiel"""
        return self.post_processor.set_rotation_angles(theta_x, theta_y, theta_z)
    
    def get_rotation_angles(self) -> dict:
        """Retourne les angles de rotation actuels"""
        return self.post_processor.get_rotation_angles()
    
    def get_rotation_info(self) -> dict:
        """Retourne les informations complètes sur la rotation"""
        return self.post_processor.get_rotation_info()
    
    def toggle_frame_rotation(self, enable=None) -> bool:
        """Active/désactive la rotation de référentiel"""
        return self.post_processor.toggle_frame_rotation(enable)
    
    def toggle_phase_correction(self, enable=None) -> bool:
        """Active/désactive la correction de phase"""
        return self.post_processor.toggle_phase_correction(enable)
    
    def toggle_parasitic_signals_compensation(self, enable=None) -> bool:
        """Active/désactive la compensation des signaux parasites"""
        return self.post_processor.toggle_parasitic_signals_compensation(enable)
    
    def get_post_processing_info(self) -> dict:
        """Retourne l'état du post-processing via le PostProcessor"""
        if self.post_processor is not None:
            return self.post_processor.get_post_processing_info()
        return {
            'offset_exc_off': {'active': False, 'values': {}},
            'offset_exc_on': {'active': False, 'values': {}},
            'phase': {'active': False, 'values': {}},
            'frame_rotation': {'active': False, 'values': {}},
            'buffer_size': 0
        }
    
    def get_sensor_samples(self, n=1):
        """Retourne les échantillons du référentiel capteur"""
        return self.post_processor.get_sensor_samples(n)
    
    def set_phase_corrections(self, corrections: dict):
        """Définit les angles de correction de phase"""
        self.post_processor.set_phase_corrections(corrections)
    
    def set_offset_no_excitation(self, offsets: dict):
        """Définit les offsets pour la calibration sans excitation"""
        self.post_processor.set_offset_no_excitation(offsets)
    
    def set_offset_with_excitation(self, offsets: dict):
        """Définit les offsets pour la calibration avec excitation"""
        self.post_processor.set_offset_with_excitation(offsets)
    # ============================================================
    #     API EXCITATION CONFIGURATION MODULE (PASS-THROUGH)
    # ============================================================
    
    def set_excitation_mode(self, mode: str) -> bool:
        """Définit le mode d'excitation via le MetaManager"""
        try:
            config = self.excitation_config.get_config(mode)
            if config:
                self.update_configuration(config)
            return True
        except Exception as e:
            print(f"[ERROR] Erreur set_excitation_mode: {e}")
            return False
    
    def get_excitation_mode(self) -> str:
        """Retourne le mode d'excitation actuel"""
        current_config = self.managers['acquisition'].get_current_config()
        return self.excitation_config.detect_mode(current_config)

    # === METHODES INTERNES POUR GERER LE PROCESSING ===


    def _on_acquisition_data_ready(self, sample):
        """Réception des données d'acquisition avec stockage buffer"""
        if self.post_processing_enabled and self.post_processor is not None:
            #print(f"[MetaManager] DEBUG: post_processing_enabled={self.post_processing_enabled}, post_processor={type(self.post_processor)}")
            # Traiter l'échantillon
            processed_sample = self.post_processor.add_sample(sample)
            #print(f"[MetaManager] DEBUG: add_sample retourne {type(processed_sample)}: {processed_sample}")
            # Émettre signal seulement si l'échantillon est valide
            if processed_sample is not None:
                self.post_processed_data_ready.emit([processed_sample])
            else:
                print(f"[MetaManager] Warning: post_processor.add_sample retourne None pour {sample}")
                # Fallback: émettre l'échantillon brut
                self.data_ready.emit(sample)

        else:
            # Mode brut - comportement original
            self.data_ready.emit(sample)

    def _start_processing_thread(self):
        """Démarre le thread de post-processing"""
        if not self._processing_running:
            self._processing_running = True
            self._processing_thread = threading.Thread(
                target=self._processing_worker,
                daemon=True
            )
            self._processing_thread.start()
    
    
    def _processing_worker(self):
        """Worker thread principal - version stable avec autocalibration"""
        while self._processing_running:
            try:
                # Traitement normal des données
                if len(self._processing_queue) > 0:
                    sample = self._processing_queue.pop(0)
                    if sample:
                        processed_sample = self.post_processor.process_sample(sample)
                        self.post_processed_data_ready.emit([processed_sample])
                
                # Gestion calibration manuelle (existante)
                with self._calibration_lock:
                    if (self._calibration_state and 
                        self._calibration_state.get('type') == 'manual' and 
                        self._calibration_state['status'] == 'pending'):
                        
                        cal_type = self._calibration_state['type']
                        if cal_type in ['offset_exc_off', 'offset_exc_on']:
                            self.post_processor.start_calibration_renewal(cal_type)
                        elif cal_type == 'phase':
                            self.post_processor.start_calibration_renewal('phase_corrections')
                        
                        if self.post_processor.is_calibration_complete():
                            result = self.post_processor.complete_calibration()
                            self.calibration_completed.emit(cal_type, result)
                            self._calibration_state = None
                
                # Délai minimal
                time.sleep(0.01)
                        
            except Exception as e:
                print(f"[WORKER ERROR] {e}")
    def stop_processing_thread(self):
        """Arrête le thread de post-processing"""
        self._processing_running = False
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=1.0)


# ============================================================
#     POST-PROCESSING MANAGEMENT
# ============================================================

    def set_display_mode(self, mode: str):
        """Définit le mode d'affichage : 'raw' ou 'processed'"""
        if mode not in ['raw', 'processed']:
            raise ValueError("Mode doit être 'raw' ou 'processed'")
        self.display_mode = mode
        print(f"[MetaManager] Mode d'affichage: {mode}")
    
    def set_post_processing_enabled(self, enabled: bool):
        """Active ou désactive le post-processing et synchronise le mode d'affichage"""
        print(f"[MetaManager] set_post_processing_enabled appelé avec: {enabled}")
        print(f"[MetaManager] DEBUG: post_processor={type(self.post_processor)}, enabled={enabled}")
        
        self.post_processing_enabled = enabled
        
        # Synchroniser le mode d'affichage
        if enabled:
            self.set_display_mode('processed')
        else:
            self.set_display_mode('raw')
        
        print(f"[MetaManager] post_processing_enabled défini à: {self.post_processing_enabled}")
        print(f"[MetaManager] display_mode synchronisé à: {self.display_mode}")
        
        # Émettre le signal de changement
        self.post_processing_changed.emit({
            'enabled': enabled,
            'display_mode': self.display_mode
        })

    def get_display_mode(self):
        """Retourne le mode d'affichage actuel"""
        return self.display_mode

    def get_latest_samples(self, n=1):
        """Récupère les derniers échantillons selon le mode"""
        # print(f"[META] get_latest_samples appelé - mode: {self.display_mode}, n: {n}")
        
        if self.display_mode == "processed" and self.post_processor is not None:
            # Retourner depuis le buffer des données traitées
            if hasattr(self.post_processor, 'processed_data_buffer'):
                samples = self.post_processor.get_latest_samples(n)
                # print(f"[META] Retour buffer processed: {len(samples)} échantillons")
                return samples
            else:
                print("[META] Buffer processed non trouvé")
                return []
        else:
            # Mode brut - utiliser l'acquisition manager
            samples = self.managers['acquisition'].get_latest_samples(n)
            # print(f"[META] Retour acquisition manager: {len(samples)} échantillons")
            return samples

    def get_compensation_status(self) -> dict:
        """
        Retourne l'état des compensations pour l'interface GUI.
        
        Returns:
            dict: État des compensations
        """
        return self.post_processor.get_processing_info()

    def calculate_offset_exc_off(self, samples):
        """Alias pour calibration offset sans excitation"""
        return self.post_processor.calibrate_offset(samples, 'offset_exc_off')

    def calculate_offset_exc_on(self, samples):
        """Alias pour calibration offset avec excitation"""
        return self.post_processor.calibrate_offset(samples, 'offset_exc_on')

    def calculate_phase_correction(self, samples):
        """Alias pour calibration phase"""
        return self.post_processor.calibrate_phase(samples)

    def toggle_compensation(self, compensation_type: str, enabled: bool):
        """Active/désactive une compensation via le PostProcessor"""
        if self.post_processor is not None:
            self.post_processor.toggle_compensation(compensation_type, enabled)
    
    def calibrate_post_processing(self):
        """Lance la calibration du post-processing"""
        if self.post_processor is not None:
            self.post_processor.calibrate_post_processing()

    def request_calibration(self, calibration_type: str):
        """Méthode publique pour demander une calibration"""
        self.calibration_requested.emit(calibration_type)

    def request_buffer_calibration(self, calibration_type: str):
        """Méthode publique pour demander calibration depuis AutoCalibrationThread"""
        samples = self.post_processor.processed_data_buffer.get_all_samples()
        
        if calibration_type == 'offset_exc_off':
            return self.post_processor.calibrate_offset(samples, 'offset_exc_off')
        elif calibration_type == 'offset_exc_on':
            return self.post_processor.calibrate_offset(samples, 'offset_exc_on')
        elif calibration_type == 'phase':
            return self.post_processor.calibrate_phase(samples)
        else:
            return {}

    def start_auto_compensation_cycle(self, direction: str):
        print(f"[META] Début cycle auto-compensation - Direction: {direction}")
        
        self.calib_thread = AutoCalibrationThread(self, direction)
        self.calib_thread.calibration_progress.connect(self._on_calibration_progress)
        self.calib_thread.calibration_completed.connect(self._on_calibration_completed)
        self.calib_thread.config_request.connect(self._on_config_request)
        self.calib_thread.start()

    def _on_config_request(self, config):
        """Gère les changements de config depuis le thread"""
        self.managers['acquisition'].update_configuration(config)

    def _on_calibration_progress(self, message):
        """Callback pour l'avancement de la calibration"""
        print(f"[META] Calibration: {message}")

    def _on_calibration_completed(self, result):
        """Callback pour la fin de la calibration"""
        print(f"[META] Calibration terminée: {result}")
        
        # Émettre uniquement le signal UI (les compensations sont déjà activées)
        self.post_processing_changed.emit(self.post_processor.config.compensation_active)



# ============================================================
#     JSON CONFIGURATION MANAGEMENT
# ============================================================

    def get_scan_config(self) -> Dict[str, Any]:
        """Récupère la configuration de scan depuis le StageManager"""
        stage_manager = self.managers['stage']
        current_config = getattr(stage_manager, '_current_config', {})
        
        # Récupération des paramètres de scan depuis StageManager
        return {
            'x_min': current_config.get('x_min', 12000),
            'x_max': current_config.get('x_max', 18000),
            'y_min': current_config.get('y_min', 12000),
            'y_max': current_config.get('y_max', 18000),
            'x_nb': current_config.get('x_nb', 81),
            'y_nb': current_config.get('y_nb', 81),
            'timer_ms': current_config.get('timer_ms', 0),
            'Mode': current_config.get('Mode', 1)
        }
    
    def get_hardware_config(self) -> Dict[str, Any]:
        """Récupère la configuration hardware depuis AcquisitionManager (source unique)."""
        acq = self.managers['acquisition']
        cfg = getattr(acq, '_current_config', {}).copy()

        # Fallback: lecture directe du memory_state si certaines infos manquent (lecture seule)
        try:
            if hasattr(acq, '_serial_communicator') and acq._serial_communicator:
                mem = acq._serial_communicator.get_memory_state()
            else:
                mem = {}
        except Exception:
            mem = {}

        def get_or_mem(cfg_key, mem_path, default=None):
            # petit utilitaire: d'abord _current_config, sinon memory_state, sinon défaut
            if cfg_key in cfg and cfg.get(cfg_key) is not None:
                return cfg.get(cfg_key)
            try:
                d = mem
                for k in mem_path:
                    d = d[k]
                return d
            except Exception:
                return default

        # DDS gains
        gain1 = cfg.get('gain_dds1', cfg.get('gain_dds', get_or_mem('gain_dds1', ['DDS', 'Gain', 1], 0)))
        gain2 = cfg.get('gain_dds2', cfg.get('gain_dds', get_or_mem('gain_dds2', ['DDS', 'Gain', 2], 0)))
        gain3 = cfg.get('gain_dds3', get_or_mem('gain_dds3', ['DDS', 'Gain', 3], 0))
        gain4 = cfg.get('gain_dds4', get_or_mem('gain_dds4', ['DDS', 'Gain', 4], 0))

        # DDS phases
        phase1 = cfg.get('phase_dds1', get_or_mem('phase_dds1', ['DDS', 'Phase', 1], 0))
        phase2 = cfg.get('phase_dds2', get_or_mem('phase_dds2', ['DDS', 'Phase', 2], 0))
        phase3 = cfg.get('phase_dds3', get_or_mem('phase_dds3', ['DDS', 'Phase', 3], 0))
        phase4 = cfg.get('phase_dds4', get_or_mem('phase_dds4', ['DDS', 'Phase', 4], 0))

        # DDS offsets/const (ajoutés à _current_config, sinon fallback mémoire)
        off1 = cfg.get('offset_dds1', get_or_mem('offset_dds1', ['DDS', 'Offset', 1], 0))
        off2 = cfg.get('offset_dds2', get_or_mem('offset_dds2', ['DDS', 'Offset', 2], 0))
        off3 = cfg.get('offset_dds3', get_or_mem('offset_dds3', ['DDS', 'Offset', 3], 0))
        off4 = cfg.get('offset_dds4', get_or_mem('offset_dds4', ['DDS', 'Offset', 4], 0))

        const1 = cfg.get('const_dds1', get_or_mem('const_dds1', ['DDS', 'Const', 1], 0))
        const2 = cfg.get('const_dds2', get_or_mem('const_dds2', ['DDS', 'Const', 2], 0))
        const3 = cfg.get('const_dds3', get_or_mem('const_dds3', ['DDS', 'Const', 3], 0))
        const4 = cfg.get('const_dds4', get_or_mem('const_dds4', ['DDS', 'Const', 4], 0))

        dds_freq = cfg.get('freq_hz', get_or_mem('freq_hz', ['DDS', 'Frequence'], 0.0))

        # ADC timing
        clkin = cfg.get('clkin', get_or_mem('clkin', ['ADC', 'CLKIN_divider_ratio'], 1))
        iclk = cfg.get('iclk', get_or_mem('iclk', ['ADC', 'ICLK_divider_ratio'], 1))
        oversampling_ratio = cfg.get('oversampling', get_or_mem('oversampling', ['ADC', 'Oversampling_ratio'], 0))

        # ADC gains
        adc_gain = {
            "1": cfg.get('adc_gain_ch1', get_or_mem('adc_gain_ch1', ['ADC', 'Gain', 1], 0)),
            "2": cfg.get('adc_gain_ch2', get_or_mem('adc_gain_ch2', ['ADC', 'Gain', 2], 0)),
            "3": cfg.get('adc_gain_ch3', get_or_mem('adc_gain_ch3', ['ADC', 'Gain', 3], 0)),
            "4": cfg.get('adc_gain_ch4', get_or_mem('adc_gain_ch4', ['ADC', 'Gain', 4], 0)),
        }

        averaging = cfg.get('n_avg', 127)  # Valeur utilisée par l'acquisition par défaut

        # Type: valeur par défaut conservée (mapping non défini actuellement)
        type_map = {"dds_1": 49, "dds_2": 12544, "dds_3": 49, "dds_4": 12544}

        return {
            "dds1": {"gain": gain1, "offset": off1, "const": const1, "phase": phase1},
            "dds2": {"gain": gain2, "offset": off2, "const": const2, "phase": phase2},
            "dds3": {"gain": gain3, "offset": off3, "const": const3, "phase": phase3},
            "dds4": {"gain": gain4, "offset": off4, "const": const4, "phase": phase4},
            "type": type_map,
            "dds_freq_hz": dds_freq,
            "clkin": clkin,
            "iclk": iclk,
            "oversampling_ratio": oversampling_ratio,
            "adc_gain": adc_gain,
            "averaging": averaging,
        }
    
    def get_postprocessing_config(self) -> Dict[str, Any]:
        """Récupère la configuration post-processing depuis PostProcessingManager"""
        post_processor = self.post_processor
        
        # Récupération des paramètres de post-processing
        storage = post_processor.config.compensation_storage
        active = post_processor.config.compensation_active
        
        return {
            "offset": {
                "data": storage.get('offset_exc_off', {}),
                "on/off": active.get('offset_exc_off', False),
                "set": True  # TODO: Déterminer si configuré
            },
            "phase": {
                "data": storage.get('phase_corrections', {}),
                "on/off": active.get('phase', False),
                "set": True
            },
            "angProj": {
                "data": storage.get('frame_rotation', {}),
                "on/off": active.get('frame_rotation', False)
            }
        }
