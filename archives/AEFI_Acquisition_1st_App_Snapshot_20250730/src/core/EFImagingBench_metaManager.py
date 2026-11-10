
# Product Requirement Document (PRD) - MetaManager EFImagingBench
#
# ## Objectif
# Créer un MetaManager centralisant la gestion des sous-managers (moteurs, excitation, etc.), exposant une API publique pour l'UI globale, et permettant la synchronisation/orchestration multi-systèmes.
#
# ## Todo (tâches à réaliser)
#
# - [ ] Définir l'API publique du MetaManager *2/10*
#     - [ ] Lister les méthodes nécessaires pour l'UI globale *2/10*
#     - [ ] Définir les signaux globaux à relayer *2/10*
# - [ ] Instancier et connecter les sous-managers *2/10*
#     - [ ] Importer et initialiser StageManager *1/10*
#     - [ ] Importer et initialiser AcquisitionManager *1/10*
#     - [ ] Connecter les signaux d'erreur/statut *2/10*
# - [ ] Implémenter les méthodes de coordination (scan + acquisition, etc.) *3/10*
#     - [ ] start_scan_and_acquire : synchronisation fine *3/10*
# - [ ] Prévoir l'ajout dynamique de nouveaux managers *2/10*
# - [ ] Gérer la fermeture propre de tous les sous-managers *1/10*
# - [ ] Rédiger un exemple d'utilisation pour l'UI globale *2/10*
#
# (À compléter/raffiner au fil du développement)
#


# -*- coding: utf-8 -*-
from PyQt5.QtCore import QObject, pyqtSignal

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import des managers existants
from ArcusPerfomax4EXStage.components.EFImagingBench_StageManager_ArcusPerformax4EXStage import StageManager
from AD9106_ADS131A04_ElectricField_3D.components.AD9106_ADS131A04_acquisition_manager import AcquisitionManager


class MetaManager(QObject):
    """
    MetaManager centralisant la gestion des sous-managers (moteurs, excitation, etc.)
    - Fournit une API publique pour l'UI globale
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mode = None  # Ajout de l'attribut mode
        # Instanciation des sous-managers
        self.managers = {}
        self.managers['stage'] = StageManager()
        self.managers['acquisition'] = AcquisitionManager()
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
           self.managers['acquisition'].data_ready.connect(self.data_ready.emit)# # Relais des changements de configuration
        if hasattr(self.managers['stage'], 'configuration_changed'):
            self.managers['stage'].configuration_changed.connect(lambda conf: (print(f'[MetaManager] Reçu configuration_changed (stage): {conf}'), self.configuration_changed_stage.emit(conf)))
        if hasattr(self.managers['acquisition'], 'configuration_changed'):
            self.managers['acquisition'].configuration_changed.connect(lambda conf: (print(f'[MetaManager] Reçu configuration_changed (acquisition): {conf}'), self.configuration_changed_acquisition.emit(conf), self.configuration_changed.emit(conf)))
        # Relais des changements de mode
        if hasattr(self.managers['stage'], 'mode_changed'):
            self.managers['stage'].mode_changed.connect(self._on_stage_mode_changed)
        if hasattr(self.managers['acquisition'], 'mode_changed'):
            self.managers['acquisition'].mode_changed.connect(self._on_acquisition_mode_changed)
        # # Relais du signal position_changed pour compatibilité ArcusGUIModern
        if hasattr(self.managers['stage'], 'position_changed'):
             self.managers['stage'].position_changed.connect(lambda x, y: self.position_changed.emit(x, y))
        # Ajoute ici d'autres relais directs si besoin (ex : data_ready, etc.)

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
        for m in self.managers.values():
            if hasattr(m, 'close'):
                m.close()

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
    def generate_scan2d(self, *args, **kwargs):
        return self.managers['stage'].generate_scan2d(*args, **kwargs)
    def inject_scan_batch(self, batch_commands):
        return self.managers['stage'].inject_scan_batch(batch_commands)
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

    # === API POST-TRAITEMENT ===
    def toggle_frame_rotation(self, enable=None):
        """Active/désactive la rotation de référentiel"""
        return self.managers['acquisition'].toggle_frame_rotation(enable)

    def toggle_parasitic_signals_compensation(self, enable=None):
        """Active/désactive la compensation des signaux parasites"""
        return self.managers['acquisition'].toggle_parasitic_signals_compensation(enable)

    def set_display_frame(self, frame):
        """Change le référentiel d'affichage ('sensor'/'bench')"""
        return self.managers['acquisition'].set_display_frame(frame)

    def get_display_frame(self):
        """Retourne le référentiel d'affichage actuel"""
        return self.managers['acquisition'].get_display_frame()

    def set_rotation_angles(self, theta_x, theta_y, theta_z):
        """Met à jour les angles de rotation"""
        return self.managers['acquisition'].set_rotation_angles(theta_x, theta_y, theta_z)

    def get_rotation_angles(self):
        """Retourne les angles de rotation actuels"""
        return self.managers['acquisition'].get_rotation_angles()

    def get_rotation_info(self):
        """Retourne les informations complètes sur la rotation"""
        return self.managers['acquisition'].get_rotation_info()

    def get_sensor_samples(self, n=1):
        """Retourne explicitement les échantillons du référentiel capteur"""
        return self.managers['acquisition'].get_sensor_samples(n)
    
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
    def start_export_csv(self, export_config):
        return self.managers['acquisition'].start_export_csv(export_config)
    def stop_export_csv(self):
        return self.managers['acquisition'].stop_export_csv()
    @property
    def is_exporting_csv(self):
        return self.managers['acquisition'].is_exporting_csv

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

    # === 🔄 API ROTATION DE RÉFÉRENTIEL (PASS-THROUGH) ===
    def set_display_frame(self, frame: str):
        """Définit le référentiel d'affichage ('sensor' ou 'bench')"""
        return self.managers['acquisition'].set_display_frame(frame)
    
    def get_display_frame(self) -> str:
        """Retourne le référentiel d'affichage actuel"""
        return self.managers['acquisition'].get_display_frame()
    
    def set_rotation_angles(self, theta_x: float, theta_y: float, theta_z: float):
        """Met à jour les angles de rotation de référentiel"""
        return self.managers['acquisition'].set_rotation_angles(theta_x, theta_y, theta_z)
    
    def get_rotation_angles(self) -> dict:
        """Retourne les angles de rotation actuels"""
        return self.managers['acquisition'].get_rotation_angles()
    
    def get_rotation_info(self) -> dict:
        """Retourne les informations complètes sur la rotation"""
        return self.managers['acquisition'].get_rotation_info()
    
    def get_sensor_samples(self, n=1):
        """Retourne explicitement les échantillons du référentiel capteur"""
        return self.managers['acquisition'].get_sensor_samples(n)
    


    def toggle_parasitic_signals_compensation(self, enable=None):
        """
        Active ou désactive la compensation des signaux parasites
        
        Args:
            enable (bool, optional): État souhaité. Si None, inverse l'état actuel.
        
        Returns:
            bool: Nouvel état de la compensation
        """
        if 'acquisition' in self.managers:
            return self.managers['acquisition'].toggle_parasitic_signals_compensation(enable)
        return False
