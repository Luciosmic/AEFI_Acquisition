#!/usr/bin/env python3
"""
Acquisition Manager - Backend adaptatif selon mode EXPLORATION/EXPORT

Thread-safe avec threading pour acquisition continue.
Pause/reprise automatique pour modifications paramètres.
"""

# --- Imports & Constantes ---
import time
import threading
from typing import Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
import sys, os
import pickle
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from .AD9106_ADS131A04_DataBuffer_Module import AcquisitionSample


class AcquisitionStatus(Enum):
    """États possibles de l'acquisition"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"

# --- Classe AcquisitionManager ---
class AcquisitionManager(QObject):
    """
    Gestionnaire d'acquisition adaptatif selon mode
    Responsabilités :
    - Acquisition continue en thread séparé
    - Pause/reprise automatique (mode EXPLORATION)
    - Gestion des erreurs et reconnexions
    - Émission signaux PyQt5 thread-safe
    """
    # --- Signaux PyQt5 ---
    data_ready = pyqtSignal(object)  # AcquisitionSample
    status_changed = pyqtSignal(str)  # AcquisitionStatus
    error_occurred = pyqtSignal(str)  # Message d'erreur
    configuration_changed = pyqtSignal(dict)  # Nouvelle configuration complète
    mode_changed = pyqtSignal(object)  # AcquisitionMode - Exploration ou Export

    # === Initialisation & Configuration ===
    def __init__(self, port="COM10", serial_communicator=None, adc_converter=None, data_buffer=None, acquisition_sample=None, csv_exporter=None):
        """
        Initialisation du gestionnaire
        Args:
            port: Port série à utiliser (défaut: COM10)
            data_buffer: Buffer d'acquisition (injection pour tests)
            adc_converter: Convertisseur ADC (pour conversion et synchro gains)
            serial_communicator: Interface hardware (optionnel, sinon créé automatiquement)
        """
        super().__init__() 

        # Création automatique du SerialCommunicator si non fourni
        if serial_communicator is None:
            try:
                from core.AD9106_ADS131A04_ElectricField_3D.controller.AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator
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

        # Création automatique du CSVExporter si non fourni
        if csv_exporter is None:
            from .AD9106_ADS131A04_CSVexporter_Module import CSVExporter
            self._csv_exporter = CSVExporter()
        else:
            self._csv_exporter = csv_exporter
        
        # Création automatique du DataBuffer si non fourni
        if data_buffer is None:
            from .AD9106_ADS131A04_DataBuffer_Module import AdaptiveDataBuffer
            self._data_buffer = AdaptiveDataBuffer()
        else:
            self._data_buffer = data_buffer

        
        # Création automatique du ADCConverter si non fourni
        if adc_converter is None:
            from .ADS131A04_Converter_Module import ADCConverter
            self._adc_converter = ADCConverter()
        else:
            self._adc_converter = adc_converter

        # === 🔄 ROTATION DE RÉFÉRENTIEL ===
        # Buffer pour données dans référentiel banc (roté)
        from .AD9106_ADS131A04_DataBuffer_Module import AdaptiveDataBuffer
        self._post_processed_buffer = AdaptiveDataBuffer()  # Buffer pour données post-traitées
        
        # Processeur de rotation référentiel
        from .EFImagingBench_FrameRotation_Module import FrameRotationProcessor
        self._rotation_processor = FrameRotationProcessor()
        
        # Choix du référentiel d'affichage : 'sensor' ou 'bench'
        self.display_frame = 'bench'  # Affichage par défaut dans référentiel banc
        print(f"[DEBUG AcquisitionManager] Référentiel d'affichage par défaut: {self.display_frame}")

        # === 🔄 FLAGS DE POST-TRAITEMENT ===
        self.frame_rotation_enabled = True  # Rotation de référentiel activée par défaut
        self.parasitic_signals_compensation_enabled = False  # Compensation désactivée par défaut
        print(f"[DEBUG AcquisitionManager] Post-traitement par défaut: rotation={self.frame_rotation_enabled}, compensation={self.parasitic_signals_compensation_enabled}")

        # Etats globaux
        self._status = AcquisitionStatus.STOPPED
        self._current_mode = 'exploration'
        self._samples_acquired = 0
        self._last_acquisition_time = None

        # Threading / Contrôle des threads
        self._running = False
        self._paused = False
        self._stop_requested = False
        self._acquisition_thread = None
        self._thread_lock = threading.RLock()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Non pausé par défaut
        
        # === 🔄 ARCHITECTURE OPTIMISÉE : Queue + PostProcessor ===
        from queue import Queue
        self._raw_samples_queue = Queue()  # Queue thread-safe pour échantillons bruts
        self._postprocessor_thread = None
        self._postprocessor_running = False
        
        # Configuration
        self._current_config = {}
        self._config_changed = threading.Event()

        
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
            self.configuration_changed.emit(self._current_config.copy())
        except Exception as e:
            print(f"Impossible de synchroniser la config initiale : {e}")

        # Compensation des signaux parasites
        self._load_parasitic_signals_compensation()
        self.parasitic_signals_compensation_enabled = False

    def sync_ui_with_hardware(self):
        """Force la synchronisation UI avec l'état hardware actuel"""
        if not self._serial_communicator:
            print("[DEBUG AcquisitionManager] sync_ui_with_hardware: Pas de serial_communicator")
            return
            
        try:
            # 🔄 LECTURE DIRECTE de l'état hardware (pas self._current_config qui peut être écrasé)
            memory = self._serial_communicator.get_memory_state()
            dds = memory["DDS"]
            adc = memory.get("ADC", {})
            
            hardware_config = {
                "gain_dds": dds["Gain"][1],           # DDS1&2 gain
                "gain_dds1": dds["Gain"][1],          # DDS1 gain individuel
                "gain_dds2": dds["Gain"][2],          # DDS2 gain individuel
                "gain_dds3": dds["Gain"][3],          # DDS3 gain  
                "gain_dds4": dds["Gain"][4],          # DDS4 gain
                "phase_dds1": dds["Phase"][1],        # DDS1 phase
                "phase_dds2": dds["Phase"][2],        # DDS2 phase
                "phase_dds3": dds["Phase"][3],        # DDS3 phase
                "phase_dds4": dds["Phase"][4],        # DDS4 phase
                "freq_hz": dds["Frequence"],          # Fréquence globale
            }
            
            # Ajout des gains ADC si disponibles
            if "Gain" in adc:
                for ch in [1, 2, 3, 4]:
                    if ch in adc["Gain"]:
                        hardware_config[f"adc_gain_ch{ch}"] = adc["Gain"][ch]
            
            print(f"[DEBUG AcquisitionManager] sync_ui_with_hardware: VRAIE config hardware={hardware_config}")
            self.configuration_changed.emit(hardware_config)
            
        except Exception as e:
            print(f"[DEBUG AcquisitionManager] sync_ui_with_hardware ERROR: {e}")
            # Fallback sur self._current_config
            print(f"[DEBUG AcquisitionManager] Fallback sur _current_config={self._current_config}")
            self.configuration_changed.emit(self._current_config.copy())

    # === Gestion des Threads & Workers ===
    def _acquisition_worker(self):
        """
        Thread principal d'acquisition continue
        """
        while self._running:
            try:
                self._pause_event.wait()
                if not self._running:
                    break
                if self._config_changed.is_set():
                    # On consomme les clés modifiées
                    changed_keys = getattr(self, '_changed_keys_pending', None)
                    self._apply_configuration(changed_keys)
                    self._changed_keys_pending = set()
                    self._config_changed.clear()
                raw_sample = self._acquire_sample()
                if raw_sample:
                    # === 🔄 ARCHITECTURE OPTIMISÉE : Acquisition → Queue ===
                    # Thread acquisition : minimal, juste acquisition + queue (non bloquant)
                    self._raw_samples_queue.put(raw_sample)
                    self._samples_acquired += 1
                    self._last_acquisition_time = datetime.now()
                else:
                    print("Aucun échantillon acquis")
            except Exception as e:
                print(f"Exception dans le worker: {e}")
                self.error_occurred.emit(str(e))
                self._set_status(AcquisitionStatus.ERROR)
                break

    def _postprocessor_worker(self):
        """
        Thread PostProcessor : Queue → Rotation → Buffers → UI
        
        Consomme la queue d'échantillons bruts et fait le post-traitement :
        - Rotation de référentiel (calculs coûteux)
        - Buffering dans les deux référentiels
        - Émission signaux UI selon display_frame
        - Export CSV (toujours en données brutes)
        """
        from queue import Empty
        
        while self._postprocessor_running:
            try:
                # Consommation non-bloquante de la queue avec timeout
                try:
                    raw_sample = self._raw_samples_queue.get(timeout=0.1)
                except Empty:
                    continue  # Pas d'échantillon, continue la boucle
                
                # === 🔄 POST-TRAITEMENT COMPLET (en parallèle de l'acquisition) ===
                
                # Buffer données brutes (référentiel capteur) - existant
                self._data_buffer.add_sample(raw_sample)
                
                # Initialisation du sample post-traité
                post_processed_sample = raw_sample

                # Rotation de référentiel (si activée)
                if self.frame_rotation_enabled:
                    post_processed_sample = self._rotation_processor.rotate_sample(post_processed_sample, to_bench_frame=True)
                
                # Compensation signaux parasites (si activée)
                if self.parasitic_signals_compensation_enabled and self._compensation_functions:
                    current_frequency = self._serial_communicator.memory_state['DDS']['Frequence']
                    post_processed_sample = self._compensate_sample(post_processed_sample, current_frequency)
                
                # Buffer données post-traitées (rotation + compensation)
                self._post_processed_buffer.add_sample(post_processed_sample)
                
                # Émission signal UI selon référentiel d'affichage choisi
                display_sample = post_processed_sample if self.display_frame == 'bench' else raw_sample
                self.data_ready.emit(display_sample)
                
                # Export toujours en données brutes (sensor) pour traçabilité
                if self._current_mode == 'export' and self._csv_exporter and self._csv_exporter.is_exporting:
                    self._csv_exporter.add_sample(raw_sample)
                
                # Marquer la tâche comme terminée
                self._raw_samples_queue.task_done()
                
            except Exception as e:
                print(f"[ERROR PostProcessor] Exception dans le post-traitement: {e}")
                self.error_occurred.emit(f"Erreur post-traitement: {e}")
                # Continue le traitement même en cas d'erreur sur un échantillon

    def _acquire_sample(self) -> Optional[AcquisitionSample]:
        if not self._serial_communicator:
            return None
        n_avg = self._current_config.get('n_avg', 127)
        success, data_str = self._serial_communicator.acquisition(n_avg)
        if not success:
            return None
        data_str = ' '.join(data_str.split())
        values = data_str.split()
        if len(values) != 8:
            return None
        try:
            values = [float(x) for x in values]
            sample = AcquisitionSample(
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
            return sample
        except (ValueError, IndexError) as e:
            return None

    def _apply_configuration(self, changed_keys=None):
        """
        Applique la configuration hardware réelle (fréquence, gain, phase, ADC, etc.)
        changed_keys: set des paramètres à appliquer (si None, applique tout comme avant)
        """
        if not self._serial_communicator:
            print("[DEBUG AcquisitionManager] Pas de serial_communicator, rien à appliquer.")
            return
        try:
            keys = set(self._current_config.keys()) if changed_keys is None else changed_keys
            print(f"[DEBUG AcquisitionManager] _apply_configuration: keys_to_apply={keys}")
            
            # --- AD9106 (DDS) ---
            if 'freq_hz' in keys:
                freq = self._current_config.get('freq_hz')
                if freq is not None:
                    print(f"[DEBUG AcquisitionManager] Applying DDS frequency: {freq} Hz → SerialCommunicator")
                    success, msg = self._serial_communicator.set_dds_frequency(freq)
                    print(f"[DEBUG AcquisitionManager] DDS frequency result: success={success}, msg={msg}")
                    time.sleep(0.2)
            # === GAINS DDS1 & DDS2 (Synchronisation forcée pour excitation) ===
            if 'gain_dds' in keys:
                gain = self._current_config.get('gain_dds')
                if gain is not None:
                    print(f"[DEBUG AcquisitionManager] Applying DDS1&2 gain: {gain} → SerialCommunicator")
                    for ch in (1, 2):
                        success, msg = self._serial_communicator.set_dds_gain(ch, gain)
                        print(f"[DEBUG AcquisitionManager] DDS{ch} gain result: success={success}, msg={msg}")
                    time.sleep(0.02)
            
            # === GAIN DDS1 individuel (avec synchronisation automatique DDS2) ===
            if 'gain_dds1' in keys:
                gain1 = self._current_config.get('gain_dds1')
                if gain1 is not None:
                    print(f"[DEBUG AcquisitionManager] Applying DDS1 gain: {gain1} → SerialCommunicator")
                    print(f"[DEBUG AcquisitionManager] 🔄 SYNCHRONISATION FORCÉE: DDS2 gain = DDS1 gain = {gain1}")
                    
                    # Application sur DDS1 et DDS2 (synchronisation forcée)
                    for ch in (1, 2):
                        success, msg = self._serial_communicator.set_dds_gain(ch, gain1)
                        print(f"[DEBUG AcquisitionManager] DDS{ch} gain result: success={success}, msg={msg}")
                    
                    # Mise à jour de la config interne pour cohérence
                    self._current_config['gain_dds'] = gain1  # Synchronisation avec gain global
                    self._current_config['gain_dds2'] = gain1  # Synchronisation DDS2
                    
                    # 🔄 ÉMISSION SYNCHRONISATION UI : Notifier que DDS2 a aussi changé
                    sync_config = {
                        'gain_dds': gain1,      # Gain global synchronisé
                        'gain_dds1': gain1,     # Gain DDS1 (confirme)
                        'gain_dds2': gain1      # Gain DDS2 (synchronisé)
                    }
                    print(f"[DEBUG AcquisitionManager] 🔄 Émission sync DDS1→DDS2: {sync_config}")
                    self.configuration_changed.emit(sync_config)
                    
                    time.sleep(0.02)
            if 'gain_dds3' in keys:
                gain3 = self._current_config.get('gain_dds3')
                if gain3 is not None:
                    print(f"[DEBUG AcquisitionManager] Applying DDS3 gain: {gain3} → SerialCommunicator")
                    success, msg = self._serial_communicator.set_dds_gain(3, gain3)
                    print(f"[DEBUG AcquisitionManager] DDS3 gain result: success={success}, msg={msg}")
            if 'gain_dds4' in keys:
                gain4 = self._current_config.get('gain_dds4')
                if gain4 is not None:
                    print(f"[DEBUG AcquisitionManager] Applying DDS4 gain: {gain4} → SerialCommunicator")
                    success, msg = self._serial_communicator.set_dds_gain(4, gain4)
                    print(f"[DEBUG AcquisitionManager] DDS4 gain result: success={success}, msg={msg}")
            if 'phase_dds1' in keys:
                phase1 = self._current_config.get('phase_dds1')
                if phase1 is not None:
                    print(f"[DEBUG AcquisitionManager] Applying DDS1 phase: {phase1}° → SerialCommunicator")
                    success, msg = self._serial_communicator.set_dds_phase(1, phase1)
                    print(f"[DEBUG AcquisitionManager] DDS1 phase result: success={success}, msg={msg}")
            if 'phase_dds2' in keys:
                phase2 = self._current_config.get('phase_dds2')
                if phase2 is not None:
                    print(f"[DEBUG AcquisitionManager] Applying DDS2 phase: {phase2}° → SerialCommunicator")
                    success, msg = self._serial_communicator.set_dds_phase(2, phase2)
                    print(f"[DEBUG AcquisitionManager] DDS2 phase result: success={success}, msg={msg}")
            if 'phase_dds3' in keys:
                phase3 = self._current_config.get('phase_dds3')
                if phase3 is not None:
                    print(f"[DEBUG AcquisitionManager] Applying DDS3 phase: {phase3}° → SerialCommunicator")
                    success, msg = self._serial_communicator.set_dds_phase(3, phase3)
                    print(f"[DEBUG AcquisitionManager] DDS3 phase result: success={success}, msg={msg}")
            if 'phase_dds4' in keys:
                phase4 = self._current_config.get('phase_dds4')
                if phase4 is not None:
                    print(f"[DEBUG AcquisitionManager] Applying DDS4 phase: {phase4}° → SerialCommunicator")
                    success, msg = self._serial_communicator.set_dds_phase(4, phase4)
                    print(f"[DEBUG AcquisitionManager] DDS4 phase result: success={success}, msg={msg}")
            # --- ADC (ADS131A04) ---
            for ch in range(1, 5):
                key = f'adc_gain_ch{ch}'
                if key in keys:
                    gain = self._current_config.get(key)
                    if gain is not None:
                        print(f"[DEBUG AcquisitionManager] Applying ADC Ch{ch} gain: {gain} → SerialCommunicator")
                        success, msg = self._serial_communicator.set_adc_gain(ch, gain)
                        print(f"[DEBUG AcquisitionManager] ADC Ch{ch} gain result: success={success}, msg={msg}")
            
            # --- ADC Timing Parameters ---
            timing_keys = ['clkin', 'iclk', 'oversampling']
            timing_params = {k: self._current_config.get(k) for k in timing_keys if k in keys and self._current_config.get(k) is not None}
            if timing_params:
                print(f"[DEBUG AcquisitionManager] Applying ADC timing config: {timing_params} → SerialCommunicator")
                
                # CLKIN Divider Ratio
                if 'clkin' in timing_params:
                    clkin_val = timing_params['clkin']
                    print(f"[DEBUG AcquisitionManager] Setting CLKIN divider: {clkin_val}")
                    success, msg = self._serial_communicator.set_clkin_divider(clkin_val)
                    print(f"[DEBUG AcquisitionManager] CLKIN divider result: success={success}, msg={msg}")
                
                # ICLK et Oversampling (peuvent être liés ou séparés)
                if 'iclk' in timing_params and 'oversampling' in timing_params:
                    # Les deux ensemble (plus efficace)
                    iclk_val = timing_params['iclk']
                    oversamp_val = timing_params['oversampling']
                    print(f"[DEBUG AcquisitionManager] Setting ICLK+Oversampling: {iclk_val}, {oversamp_val}")
                    success, msg = self._serial_communicator.set_iclk_divider_and_oversampling(iclk_val, oversamp_val)
                    print(f"[DEBUG AcquisitionManager] ICLK+Oversampling result: success={success}, msg={msg}")
                elif 'iclk' in timing_params:
                    # ICLK seul
                    iclk_val = timing_params['iclk']
                    print(f"[DEBUG AcquisitionManager] Setting ICLK divider: {iclk_val}")
                    success, msg = self._serial_communicator.set_iclk_divider(iclk_val)
                    print(f"[DEBUG AcquisitionManager] ICLK divider result: success={success}, msg={msg}")
                elif 'oversampling' in timing_params:
                    # Oversampling seul
                    oversamp_val = timing_params['oversampling']
                    print(f"[DEBUG AcquisitionManager] Setting oversampling ratio: {oversamp_val}")
                    success, msg = self._serial_communicator.set_oversampling_ratio(oversamp_val)
                    print(f"[DEBUG AcquisitionManager] Oversampling ratio result: success={success}, msg={msg}")
                
            # --- ADC Reference Parameters ---
            ref_keys = ['negative_ref', 'high_res', 'ref_voltage', 'ref_selection']
            ref_params = {k: self._current_config.get(k) for k in ref_keys if k in keys and self._current_config.get(k) is not None}
            if ref_params:
                print(f"[DEBUG AcquisitionManager] Applying ADC reference config: {ref_params} → SerialCommunicator")
                
                # Récupération des valeurs avec valeurs par défaut
                negative_ref = ref_params.get('negative_ref', False)
                high_res = ref_params.get('high_res', True)
                ref_voltage = ref_params.get('ref_voltage', 1)  # 1 = 4.0V par défaut
                ref_selection = ref_params.get('ref_selection', 1)  # 1 = Internal par défaut
                
                print(f"[DEBUG AcquisitionManager] Setting reference config: neg_ref={negative_ref}, high_res={high_res}, ref_voltage={ref_voltage}, ref_selection={ref_selection}")
                success, msg = self._serial_communicator.set_reference_config(negative_ref, high_res, ref_voltage, ref_selection)
                print(f"[DEBUG AcquisitionManager] Reference config result: success={success}, msg={msg}")
            print(f"[DEBUG AcquisitionManager] _apply_configuration completed successfully")
        except Exception as e:
            print(f"[DEBUG AcquisitionManager] _apply_configuration ERROR: {e}")
            self.error_occurred.emit(f"Erreur configuration: {e}")

    def _set_status(self, status: AcquisitionStatus):
        """
        Met à jour le statut et émet le signal
        """
        self._status = status
        self.status_changed.emit(status.value)

    @property
    def status(self) -> AcquisitionStatus:
        """
        Statut actuel
        """
        return self._status

    @property
    def current_mode(self) -> str:
        """
        Mode actuel ('exploration'/'export')
        """
        return self._current_mode

    @property
    def samples_acquired(self) -> int:
        """
        Nombre d'échantillons acquis
        """
        return self._samples_acquired

    # === Gestion des Signaux/Callbacks ===
    def add_data_callback(self, callback):
        """
        Connecte un callback au signal data_ready
        """
        self.data_ready.connect(callback)

    def add_status_callback(self, callback):
        """
        Connecte un callback au signal status_changed
        """
        self.status_changed.connect(callback)


    # === Fermeture & Nettoyage ===
    def close(self):
        """
        Ferme proprement l'AcquisitionManager et le SerialCommunicator
        """
        print("[DEBUG AcquisitionManager] Fermeture en cours...")
        
        # Arrêt de l'acquisition (gère déjà les deux threads)
        self.stop_acquisition()
        
        # Nettoyage final de la queue si nécessaire
        remaining_samples = 0
        while not self._raw_samples_queue.empty():
            try:
                self._raw_samples_queue.get_nowait()
                remaining_samples += 1
            except:
                break
        if remaining_samples > 0:
            print(f"[DEBUG AcquisitionManager] {remaining_samples} échantillons non traités supprimés")
        
        # Fermeture du SerialCommunicator
        if self._serial_communicator:
            try:
                self._serial_communicator.disconnect()
                print("[DEBUG AcquisitionManager] SerialCommunicator fermé")
            except Exception as e:
                print(f"Warning: Erreur lors de la fermeture SerialCommunicator: {e}")
            finally:
                self._serial_communicator = None 







    # =========================
    # SECTION DES API PUBLIQUES
    # =========================

    # === API MANAGER ===
    def start_acquisition(self, mode: str, config: Dict[str, Any]) -> bool:
        """
        Démarre l'acquisition dans le mode spécifié
        Args:
            mode: Mode d'acquisition ('exploration'/'export')
            config: Configuration (gain_dds, freq_hz, n_avg)
        Returns:
            True si démarrage réussi
        """
        with self._thread_lock:
            if self._status == AcquisitionStatus.RUNNING:
                return False
            self._current_mode = mode
            self._current_config = config.copy()
            self._data_buffer.set_mode(mode)
            self._post_processed_buffer.set_mode(mode)  # Synchronisation mode pour buffer post-traité
            
            # === 🔄 DÉMARRAGE DOUBLE THREAD OPTIMISÉ ===
            self._running = True
            self._paused = False
            self._stop_requested = False
            self._pause_event.set()
            self._samples_acquired = 0
            
            # Démarrage thread PostProcessor en premier
            self._postprocessor_running = True
            self._postprocessor_thread = threading.Thread(target=self._postprocessor_worker, daemon=True)
            self._postprocessor_thread.start()
            print("[DEBUG AcquisitionManager] Thread PostProcessor démarré")
            
            # Démarrage thread Acquisition
            self._acquisition_thread = threading.Thread(target=self._acquisition_worker)
            self._acquisition_thread.start()
            print("[DEBUG AcquisitionManager] Thread Acquisition démarré")
            
            self._set_status(AcquisitionStatus.RUNNING)
            self.mode_changed.emit(self._current_mode)
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
            
            # === 🔄 ARRÊT DOUBLE THREAD OPTIMISÉ ===
            self._stop_requested = True
            self._running = False
            self._pause_event.set()
            
            # Arrêt thread Acquisition
            if self._acquisition_thread:
                self._acquisition_thread.join(timeout=3.0)
                print("[DEBUG AcquisitionManager] Thread Acquisition arrêté")
            
            # Vider la queue et arrêter thread PostProcessor
            print(f"[DEBUG AcquisitionManager] Queue restante: {self._raw_samples_queue.qsize()} échantillons")
            self._postprocessor_running = False
            if self._postprocessor_thread:
                self._postprocessor_thread.join(timeout=3.0)
                print("[DEBUG AcquisitionManager] Thread PostProcessor arrêté")
            
            self._set_status(AcquisitionStatus.STOPPED)
            return True

    def pause_acquisition(self) -> bool:
        """
        Met en pause l'acquisition (mode exploration uniquement)
        Returns:
            True si pause réussie
        """
        if self._current_mode != 'exploration':
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
        if self._current_mode == 'export':
            return False
        with self._thread_lock:
            was_running = self._status == AcquisitionStatus.RUNNING
            if was_running:
                self.pause_acquisition()
                time.sleep(0.1)
            old_config = self._current_config.copy()
            self._current_config.update(config)
            # Détection des paramètres modifiés
            changed_keys = {k for k in self._current_config if old_config.get(k) != self._current_config[k]}
            self._changed_keys_pending = changed_keys if changed_keys else set()
            self._config_changed.set()
            if changed_keys:
                self.configuration_changed.emit({k: self._current_config[k] for k in changed_keys})
            if was_running:
                self.resume_acquisition()
            return True

    def start_export_csv(self, export_config):
        """
        Démarre l'export CSV avec la config fournie (dict avec output_dir, filename_base, duration_seconds)
        """
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
            self._current_mode = 'export'
            self._set_status(AcquisitionStatus.RUNNING)
            self.mode_changed.emit(self._current_mode)
        return started

    def stop_export_csv(self):
        """
        Arrête l'export CSV si actif
        """
        if self._csv_exporter and self._csv_exporter.is_exporting:
            self._csv_exporter.stop_export()
            self._current_mode = 'exploration'
            self.mode_changed.emit(self._current_mode)
            self._set_status(AcquisitionStatus.RUNNING)
            return True
        return False

    @property
    def is_exporting_csv(self):
        """
        Indique si un export CSV est en cours
        """
        return self._csv_exporter is not None and self._csv_exporter.is_exporting


    # === API BUFFER (PASS-THROUGH) ===
    def get_buffer_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du buffer
        """
        return self._data_buffer.get_buffer_status()

    def get_acquisition_stats(self) -> Dict[str, Any]:
        """
        Statistiques d'acquisition
        """
        return {
            'status': self._status.value,
            'mode': self._current_mode,
            'samples_acquired': self._samples_acquired,
            'is_paused': self._paused,
            'last_acquisition': self._last_acquisition_time.isoformat() if self._last_acquisition_time else None,
            'config': self._current_config.copy(),
            'buffer_status': self.get_buffer_status()
        }

    def get_latest_samples(self, n=1):
        """Retourne les n derniers échantillons du buffer selon référentiel d'affichage"""
        if self.display_frame == 'bench':
            return self._post_processed_buffer.get_latest_samples(n)
        return self._data_buffer.get_latest_samples(n)

    def get_all_samples(self):
        """Retourne tous les échantillons du buffer selon référentiel d'affichage"""
        if self.display_frame == 'bench':
            return self._post_processed_buffer.get_all_samples()
        return self._data_buffer.get_all_samples()

    def clear_buffer(self):
        """Vide les buffers d'acquisition (sensor et post-processed)"""
        self._data_buffer.clear_buffer()
        self._post_processed_buffer.clear_buffer()

    def flush_for_export(self):
        """Flush les échantillons pour export CSV (API DataBuffer)"""
        return self._data_buffer.flush_for_export()

    def add_production_callback(self, callback):
        """Ajoute un callback de flush production (API DataBuffer)"""
        self._data_buffer.add_production_callback(callback)


    # === API ADC_Converter (PASS-THROUGH) ===
    def set_channel_gains(self, gains: Dict[int, int]):
        if self._adc_converter:
            return self._adc_converter.set_channel_gains(gains)

    def set_v_to_vm_factor(self, factor: float):
        if self._adc_converter:
            return self._adc_converter.set_v_to_vm_factor(factor)

    def convert_sample(self, sample, gains: Dict[str, int], target_unit):
        if self._adc_converter:
            return self._adc_converter.convert_sample(sample, gains, target_unit)

    def convert_adc_to_voltage(self, adc_code: int, channel: int):
        if self._adc_converter:
            return self._adc_converter.convert_adc_to_voltage(adc_code, channel)

    def convert_channel_array(self, adc_codes, start_channel: int = 1):
        if self._adc_converter:
            return self._adc_converter.convert_channel_array(adc_codes, start_channel)

    def convert_to_units(self, voltage: float, target_units):
        if self._adc_converter:
            return self._adc_converter.convert_to_units(voltage, target_units)

    def convert_full_acquisition(self, adc1_data, adc2_data, target_units=None):
        if self._adc_converter:
            return self._adc_converter.convert_full_acquisition(adc1_data, adc2_data, target_units)

    def get_voltage_range(self, gain: int):
        if self._adc_converter:
            return self._adc_converter.get_voltage_range(gain)

    def get_channel_info(self, channel: int):
        if self._adc_converter:
            return self._adc_converter.get_channel_info(channel)

    def get_all_channels_info(self):
        if self._adc_converter:
            return self._adc_converter.get_all_channels_info()

    def clear_adc_cache(self):
        if self._adc_converter:
            return self._adc_converter.clear_cache()

    @property
    def channel_gains(self):
        if self._adc_converter:
            return self._adc_converter.channel_gains
        return None

    # === 🔄 API ROTATION DE RÉFÉRENTIEL ===
    def set_display_frame(self, frame: str):
        """
        Définit le référentiel d'affichage pour les échantillons.
        
        Args:
            frame: 'sensor' pour référentiel capteur, 'bench' pour référentiel banc
        """
        if frame not in ['sensor', 'bench']:
            print(f"[ERROR AcquisitionManager] Référentiel invalide: {frame}. Utiliser 'sensor' ou 'bench'.")
            return False
        
        self.display_frame = frame
        print(f"[DEBUG AcquisitionManager] Référentiel d'affichage changé: {frame}")
        return True
    
    def get_display_frame(self) -> str:
        """Retourne le référentiel d'affichage actuel."""
        return self.display_frame
    
    def set_rotation_angles(self, theta_x: float, theta_y: float, theta_z: float):
        """
        Met à jour les angles de rotation et recalcule le processeur.
        
        Args:
            theta_x, theta_y, theta_z: Angles de rotation en degrés
        """
        self._rotation_processor.set_rotation_angles(theta_x, theta_y, theta_z)
        print(f"[DEBUG AcquisitionManager] Angles de rotation mis à jour")
        return True
    
    def get_rotation_angles(self) -> dict:
        """Retourne les angles de rotation actuels."""
        return {
            'theta_x': self._rotation_processor.theta_x,
            'theta_y': self._rotation_processor.theta_y, 
            'theta_z': self._rotation_processor.theta_z
        }
    
    def get_rotation_info(self) -> dict:
        """Retourne les informations complètes sur la rotation."""
        return self._rotation_processor.get_rotation_info()
    
    def get_sensor_samples(self, n=1):
        """Retourne explicitement les échantillons du référentiel capteur."""
        return self._data_buffer.get_latest_samples(n)
    


    def _load_parasitic_signals_compensation(self):
        """
        Charge les fonctions d'interpolation pour la compensation des signaux parasites
        """
        try:
            compensation_file = os.path.join(
                os.path.dirname(__file__), 
                '..', '..', '..', 'data_processing', 
                'noexcitation_parasitic_signals_characterization_compensation_functions.pkl'
            )
            
            with open(compensation_file, 'rb') as f:
                self._compensation_functions = pickle.load(f)
            
            print("✅ Fonctions de compensation des signaux parasites chargées")
        except Exception as e:
            print(f"❌ Erreur de chargement des fonctions de compensation : {e}")
            self._compensation_functions = None

    def _compensate_sample(self, sample, current_frequency):
        """
        Applique la compensation des signaux parasites à un échantillon
        
        Args:
            sample (AcquisitionSample): Échantillon à compenser
            current_frequency (float): Fréquence courante
        
        Returns:
            AcquisitionSample: Échantillon compensé
        """
        if not self.parasitic_signals_compensation_enabled or self._compensation_functions is None:
            return sample

        # Calcul des offsets interpolés
        offsets = {}
        for channel in ['adc1_ch1', 'adc1_ch2', 'adc1_ch3', 'adc1_ch4', 'adc2_ch1', 'adc2_ch2']:
            if channel in self._compensation_functions:
                interpolation_func = self._compensation_functions[channel]
                offsets[channel] = interpolation_func(current_frequency)
            else:
                offsets[channel] = 0
        
        # Création d'un nouvel échantillon compensé (comme la rotation)
        from .AD9106_ADS131A04_DataBuffer_Module import AcquisitionSample
        compensated_sample = AcquisitionSample(
            timestamp=sample.timestamp,
            adc1_ch1=int(round(sample.adc1_ch1 - offsets['adc1_ch1'])),
            adc1_ch2=int(round(sample.adc1_ch2 - offsets['adc1_ch2'])),
            adc1_ch3=int(round(sample.adc1_ch3 - offsets['adc1_ch3'])),
            adc1_ch4=int(round(sample.adc1_ch4 - offsets['adc1_ch4'])),
            adc2_ch1=int(round(sample.adc2_ch1 - offsets['adc2_ch1'])),
            adc2_ch2=int(round(sample.adc2_ch2 - offsets['adc2_ch2'])),
            adc2_ch3=sample.adc2_ch3,  # Canaux auxiliaires inchangés
            adc2_ch4=sample.adc2_ch4
        )
        
        return compensated_sample



    def toggle_parasitic_signals_compensation(self, enable=None):
        """
        Active ou désactive la compensation des signaux parasites
        
        Args:
            enable (bool, optional): État souhaité. Si None, inverse l'état actuel.
        
        Returns:
            bool: Nouvel état de la compensation
        """
        if enable is None:
            self.parasitic_signals_compensation_enabled = not self.parasitic_signals_compensation_enabled
        else:
            self.parasitic_signals_compensation_enabled = enable
        
        print(f"📊 Compensation des signaux parasites : {'✅ Activée' if self.parasitic_signals_compensation_enabled else '❌ Désactivée'}")
        return self.parasitic_signals_compensation_enabled


    def toggle_frame_rotation(self, enable=None):
        """
        Active ou désactive la rotation de référentiel
        
        Args:
            enable (bool, optional): État souhaité. Si None, inverse l'état actuel.
        
        Returns:
            bool: Nouvel état de la rotation
        """
        if enable is None:
            self.frame_rotation_enabled = not self.frame_rotation_enabled
        else:
            self.frame_rotation_enabled = enable
        
        print(f"🔄 Rotation de référentiel : {'✅ Activée' if self.frame_rotation_enabled else '❌ Désactivée'}")
        return self.frame_rotation_enabled




