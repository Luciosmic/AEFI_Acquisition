#!/usr/bin/env python3
"""
Acquisition Manager - Backend adaptatif selon mode EXPLORATION/EXPORT

Thread-safe avec threading pour acquisition continue.
Pause/reprise automatique pour modifications paramètres.
"""

import time
import threading
from typing import Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
import sys, os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from .AD9106_ADS131A04_ModeController_Module import AcquisitionMode
from .AD9106_ADS131A04_DataBuffer_Module import AcquisitionSample, AdaptiveDataBuffer
from .ADS131A04_Converter_Module import ADCConverter


class AcquisitionStatus(Enum):
    """États possibles de l'acquisition"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class AcquisitionManager(QObject):
    """
    Gestionnaire d'acquisition adaptatif selon mode
    
    Responsabilités :
    - Acquisition continue en thread séparé
    - Pause/reprise automatique (mode EXPLORATION)
    - Gestion des erreurs et reconnexions
    - Émission signaux PyQt5 thread-safe
    """
    
    # Signaux PyQt5
    data_ready = pyqtSignal(object)  # AcquisitionSample
    status_changed = pyqtSignal(str)  # AcquisitionStatus
    error_occurred = pyqtSignal(str)  # Message d'erreur
    configuration_changed = pyqtSignal(dict)  # Nouvelle configuration complète
    
    def __init__(self, port="COM10", data_buffer=None, mode_controller=None, adc_converter=None, serial_communicator=None):
        """
        Initialisation du gestionnaire
        
        Args:
            port: Port série à utiliser (défaut: COM10)
            data_buffer: Buffer d'acquisition (injection pour tests)
            mode_controller: Contrôleur de mode (optionnel)
            adc_converter: Convertisseur ADC (pour conversion et synchro gains)
            serial_communicator: Interface hardware (optionnel, sinon créé automatiquement)
        """
        super().__init__()
        
        # Création automatique du SerialCommunicator si non fourni
        if serial_communicator is None:
            try:
                from instruments.AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator
                self._serial_communicator = SerialCommunicator()
                # Connexion automatique
                success, msg = self._serial_communicator.connect(port)
                if not success:
                    raise RuntimeError(f"Impossible de se connecter au port {port}: {msg}")
                # Configuration par défaut
                success, msg = self._serial_communicator.init_default_config()
                if not success:
                    print(f"Warning: Configuration par défaut non appliquée: {msg}")
            except Exception as e:
                self._serial_communicator = None
                raise RuntimeError(f"Erreur d'initialisation SerialCommunicator: {e}")
        else:
            self._serial_communicator = serial_communicator
        
        self._acquisition_thread = None
        self._status = AcquisitionStatus.STOPPED
        self._current_mode = AcquisitionMode.EXPLORATION
        
        # Contrôle thread
        self._running = False
        self._paused = False
        self._stop_requested = False
        
        # Threading
        self._thread_lock = threading.RLock()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Non pausé par défaut
        
        # Configuration
        self._current_config = {}
        self._config_changed = threading.Event()
        
        # Buffer (injection possible)
        self._data_buffer = data_buffer if data_buffer is not None else AdaptiveDataBuffer()
        
        # Mode controller (optionnel)
        self._mode_controller = mode_controller
        
        # Ajout pour conversion/synchronisation des gains ADC
        self._adc_converter = adc_converter
        
        # Statistiques
        self._samples_acquired = 0
        self._last_acquisition_time = None
        
        # Initialisation de la configuration centrale avec les valeurs hardware
        try:
            memory = self._serial_communicator.get_memory_state()
            dds = memory["DDS"]
            self._current_config["gain_dds"] = dds["Gain"][1]
            self._current_config["gain_dds3"] = dds["Gain"][3]
            self._current_config["gain_dds4"] = dds["Gain"][4]
            self._current_config["phase_dds1"] = dds["Phase"][1]
            self._current_config["phase_dds2"] = dds["Phase"][2]
            self._current_config["phase_dds3"] = dds["Phase"][3]
            self._current_config["phase_dds4"] = dds["Phase"][4]
            self._current_config["freq_hz"] = dds["Frequence"]
            # Émettre la config initiale pour synchroniser l'UI
            self.configuration_changed.emit(self._current_config.copy())
        except Exception as e:
            print(f"Impossible de synchroniser la config initiale : {e}")
        
        self._csv_exporter = None
        
    def start_acquisition(self, mode: AcquisitionMode, config: Dict[str, Any]) -> bool:
        """
        Démarre l'acquisition dans le mode spécifié
        
        Args:
            mode: Mode d'acquisition (EXPLORATION/EXPORT)
            config: Configuration (gain_dds, freq_hz, n_avg)
            
        Returns:
            True si démarrage réussi
        """
        with self._thread_lock:
            if self._status == AcquisitionStatus.RUNNING:
                return False
            
            # Configuration
            self._current_mode = mode
            self._current_config = config.copy()
            self._data_buffer.set_mode(mode)
            
            # Reset état
            self._running = True
            self._paused = False
            self._stop_requested = False
            self._pause_event.set()
            self._samples_acquired = 0
            
            # Démarrage thread
            self._acquisition_thread = threading.Thread(target=self._acquisition_worker)
            self._acquisition_thread.start()
            
            self._set_status(AcquisitionStatus.RUNNING)
            return True
    
    def stop_acquisition(self) -> bool:
        """
        Arrête l'acquisition
        
        Returns:
            True si arrêt réussi
        """
        with self._thread_lock:
            if self._status == AcquisitionStatus.STOPPED:
                return True
            
            # Signal d'arrêt
            self._stop_requested = True
            self._running = False
            self._pause_event.set()  # Débloquer si en pause
            
            # Attente fin thread
            if self._acquisition_thread:
                self._acquisition_thread.join(timeout=5.0)
            
            self._set_status(AcquisitionStatus.STOPPED)
            return True
    
    def pause_acquisition(self) -> bool:
        """
        Met en pause l'acquisition (mode EXPLORATION uniquement)
        
        Returns:
            True si pause réussie
        """
        if self._current_mode != AcquisitionMode.EXPLORATION:
            return False
        
        with self._thread_lock:
            if self._status != AcquisitionStatus.RUNNING:
                return False
            
            self._paused = True
            self._pause_event.clear()
            self._set_status(AcquisitionStatus.PAUSED)
            return True
    
    def resume_acquisition(self) -> bool:
        """
        Reprend l'acquisition après pause
        
        Returns:
            True si reprise réussie
        """
        with self._thread_lock:
            if self._status != AcquisitionStatus.PAUSED:
                return False
            
            # Vider le buffer série avant de reprendre
            if self._serial_communicator:
                self._serial_communicator.clear_serial_buffer()
            
            self._paused = False
            self._pause_event.set()
            self._set_status(AcquisitionStatus.RUNNING)
            return True
    
    def update_configuration(self, config: Dict[str, Any]) -> bool:
        """
        Met à jour la configuration (avec pause automatique si nécessaire)
        
        Args:
            config: Nouvelle configuration
            
        Returns:
            True si mise à jour réussie
        """
        print(f"update_configuration: config={config}")
        if self._current_mode == AcquisitionMode.EXPORT:
            # Mode EXPORT : configuration figée
            return False
        
        with self._thread_lock:
            # Pause automatique si en cours
            was_running = self._status == AcquisitionStatus.RUNNING
            if was_running:
                self.pause_acquisition()
                # Attendre 100ms pour stabilisation
                time.sleep(0.1)
            
            # Mise à jour config
            old_config = self._current_config.copy()
            self._current_config.update(config)
            self._config_changed.set()
            
            # Émission du signal uniquement si la config a changé
            if old_config != self._current_config:
                self.configuration_changed.emit(self._current_config.copy())
            
            # Reprise automatique
            if was_running:
                self.resume_acquisition()
            
            return True
    
    def start_export_csv(self, export_config):
        """Démarre l'export CSV avec la config fournie (dict avec output_dir, filename_base, duration_seconds)"""
        from .AD9106_ADS131A04_CSVexporter_Module import CSVExporter, ExportConfig
        if self._csv_exporter and self._csv_exporter.is_exporting:
            return False
        config = ExportConfig(
            output_dir=export_config.get('output_dir', '.'),
            filename_base=export_config.get('filename_base', 'export'),
            duration_seconds=export_config.get('duration_seconds', None),
            metadata={},
        )
        self._csv_exporter = CSVExporter()
        started = self._csv_exporter.start_export(config)
        if started:
            self._current_mode = AcquisitionMode.EXPORT
            self._set_status(AcquisitionStatus.RUNNING)
        return started

    def stop_export_csv(self):
        """Arrête l'export CSV si actif"""
        if self._csv_exporter and self._csv_exporter.is_exporting:
            self._csv_exporter.stop_export()
            self._current_mode = AcquisitionMode.EXPLORATION
            self._set_status(AcquisitionStatus.RUNNING)
            return True
        return False

    @property
    def is_exporting_csv(self):
        return self._csv_exporter is not None and self._csv_exporter.is_exporting
    
    def _acquisition_worker(self):
        print("Thread acquisition démarré")
        while self._running:
            try:
                self._pause_event.wait()
                if not self._running:
                    break
                if self._config_changed.is_set():
                    self._apply_configuration()
                    self._config_changed.clear()
                sample = self._acquire_sample()
                if sample:
                    self.data_ready.emit(sample)
                    self._data_buffer.add_sample(sample)
                    self._samples_acquired += 1
                    self._last_acquisition_time = datetime.now()
                    # Ajout à l'export CSV si actif et mode EXPORT
                    if self._current_mode == AcquisitionMode.EXPORT and self._csv_exporter and self._csv_exporter.is_exporting:
                        self._csv_exporter.add_sample(sample)
                else:
                    print("Aucun échantillon acquis")
            except Exception as e:
                print(f"Exception dans le worker: {e}")
                self.error_occurred.emit(str(e))
                self._set_status(AcquisitionStatus.ERROR)
                break
    
    def _acquire_sample(self) -> Optional[AcquisitionSample]:
        """
        Acquiert un échantillon via SerialCommunicator
        Returns:
            AcquisitionSample ou None si erreur
        """
        if not self._serial_communicator:
            return None
            
        # Récupérer le paramètre de moyennage depuis la config
        n_avg = self._current_config.get('n_avg', 127)
        
        success, data_str = self._serial_communicator.acquisition(n_avg)
        if not success:
            return None
            
        # Nettoyer les données : remplacer les espaces multiples par des espaces simples
        data_str = ' '.join(data_str.split())
        
        # Validation des données : vérifier qu'on a 8 valeurs
        values = data_str.split()
        if len(values) != 8:
            return None
            
        # Créer l'échantillon
        try:
            values = [float(x) for x in values]
            return AcquisitionSample(
                timestamp=datetime.now(),
                adc1_ch1=int(values[0]),
                adc1_ch2=int(values[1]),
                adc1_ch3=int(values[2]),
                adc1_ch4=int(values[3]),
                adc2_ch1=int(values[4]),
                adc2_ch2=int(values[5]),
                adc2_ch3=int(values[6]),
                adc2_ch4=int(values[7])
            )
        except (ValueError, IndexError):
            return None
    
    def _apply_configuration(self):
        """Applique la configuration hardware réelle (fréquence, gain, etc.)"""
        if not self._serial_communicator:
            print("Pas de serial_communicator, rien à appliquer.")
            return
        try:
            # Appliquer la fréquence DDS si présente
            freq = self._current_config.get('freq_hz')
            if freq is not None:
                print(f"Application hardware : set_dds_frequency({freq})")
                success, msg = self._serial_communicator.set_dds_frequency(freq)
                print(f"Résultat set_dds_frequency: {success}, {msg}")
                time.sleep(1.0)  # Délai pour stabilisation hardware
            # Appliquer le gain DDS1/2 si présent
            gain = self._current_config.get('gain_dds')
            if gain is not None:
                print(f"Application hardware : set_dds_gain(1, {gain}) et set_dds_gain(2, {gain})")
                for ch in (1, 2):
                    success, msg = self._serial_communicator.set_dds_gain(ch, gain)
                    print(f"Résultat set_dds_gain ch{ch}: {success}, {msg}")
                time.sleep(0.2)
            # Appliquer le gain DDS3/4 si présents
            gain3 = self._current_config.get('gain_dds3')
            if gain3 is not None:
                print(f"Application hardware : set_dds_gain(3, {gain3})")
                success, msg = self._serial_communicator.set_dds_gain(3, gain3)
                print(f"Résultat set_dds_gain ch3: {success}, {msg}")
            gain4 = self._current_config.get('gain_dds4')
            if gain4 is not None:
                print(f"Application hardware : set_dds_gain(4, {gain4})")
                success, msg = self._serial_communicator.set_dds_gain(4, gain4)
                print(f"Résultat set_dds_gain ch4: {success}, {msg}")
            # Appliquer la phase DDS1/2 si présente
            phase1 = self._current_config.get('phase_dds1')
            if phase1 is not None:
                print(f"Application hardware : set_dds_phase(1, {phase1})")
                success, msg = self._serial_communicator.set_dds_phase(1, phase1)
                print(f"Résultat set_dds_phase ch1: {success}, {msg}")
            phase2 = self._current_config.get('phase_dds2')
            if phase2 is not None:
                print(f"Application hardware : set_dds_phase(2, {phase2})")
                success, msg = self._serial_communicator.set_dds_phase(2, phase2)
                print(f"Résultat set_dds_phase ch2: {success}, {msg}")
            # Appliquer la phase DDS3/4 si présentes
            phase3 = self._current_config.get('phase_dds3')
            if phase3 is not None:
                print(f"Application hardware : set_dds_phase(3, {phase3})")
                success, msg = self._serial_communicator.set_dds_phase(3, phase3)
                print(f"Résultat set_dds_phase ch3: {success}, {msg}")
            phase4 = self._current_config.get('phase_dds4')
            if phase4 is not None:
                print(f"Application hardware : set_dds_phase(4, {phase4})")
                success, msg = self._serial_communicator.set_dds_phase(4, phase4)
                print(f"Résultat set_dds_phase ch4: {success}, {msg}")
        except Exception as e:
            self.error_occurred.emit(f"Erreur configuration: {e}")
    
    def _set_status(self, status: AcquisitionStatus):
        """Met à jour le statut et émet le signal"""
        self._status = status
        self.status_changed.emit(status.value)
    
    @property
    def status(self) -> AcquisitionStatus:
        """Statut actuel"""
        return self._status
    
    @property
    def current_mode(self) -> AcquisitionMode:
        """Mode actuel"""
        return self._current_mode
    
    @property
    def samples_acquired(self) -> int:
        """Nombre d'échantillons acquis"""
        return self._samples_acquired
    
    def get_buffer_status(self) -> Dict[str, Any]:
        """Retourne le statut du buffer"""
        return self._data_buffer.get_buffer_status()
    
    def get_acquisition_stats(self) -> Dict[str, Any]:
        """Statistiques d'acquisition"""
        return {
            'status': self._status.value,
            'mode': self._current_mode.value,
            'samples_acquired': self._samples_acquired,
            'is_paused': self._paused,
            'last_acquisition': self._last_acquisition_time.isoformat() if self._last_acquisition_time else None,
            'config': self._current_config.copy(),
            'buffer_status': self.get_buffer_status()
        }
    
    def set_mode(self, mode: AcquisitionMode):
        """
        Change dynamiquement le mode d'acquisition (EXPLORATION/EXPORT)
        """
        with self._thread_lock:
            self._current_mode = mode
            if hasattr(self, '_data_buffer') and self._data_buffer is not None:
                self._data_buffer.set_mode(mode)
    
    def set_adc_gain(self, channel: int, gain: int):
        """
        Applique le gain matériel via SerialCommunicator et synchronise l'ADCConverter.
        Pour la traçabilité scientifique, toute modification de gain doit passer par cette méthode.
        """
        # 1. Appliquer le gain matériel
        if self._serial_communicator:
            success, msg = self._serial_communicator.set_adc_gain(channel, gain)
            if not success:
                self.error_occurred.emit(f"Erreur configuration gain ADC ch{channel}: {msg}")
                return False
        # 2. Synchroniser l'ADCConverter
        if self._adc_converter:
            self._adc_converter.set_channel_gains({channel: gain})
        return True
    
    def close(self):
        """
        Ferme proprement l'AcquisitionManager et le SerialCommunicator
        """
        # Arrêt de l'acquisition
        self.stop_acquisition()
        
        # Fermeture du SerialCommunicator
        if self._serial_communicator:
            try:
                self._serial_communicator.disconnect()
            except Exception as e:
                print(f"Warning: Erreur lors de la fermeture SerialCommunicator: {e}")
            finally:
                self._serial_communicator = None 