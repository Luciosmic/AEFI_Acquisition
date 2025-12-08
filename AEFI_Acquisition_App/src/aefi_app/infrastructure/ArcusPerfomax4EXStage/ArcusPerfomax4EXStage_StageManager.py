# -*- coding: utf-8 -*-

from PyQt5.QtCore import QObject, pyqtSignal
import threading
import queue
from enum import Enum, auto
import time # Centralisé ici


import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from .modules.ArcusPerfomax4EXStage_DataBuffer_Module import Position_AdaptiveBuffer, PositionSample
from .controller.ArcusPerformax4EXStage_Controller import ArcusPerformax4EXStageController
from .modules.ArcusPerfomax4EXStage_GeometricalParametersConversion_Module import (
    get_bench_limits_cm, clamp_rect_cm, inc_to_cm, cm_to_inc
) 
from .modules.ArcusPerfomax4EXStage_Scan2D_Module import Scan2DConfigurator

class StageManager(QObject):
    """
    StageManager pour Arcus Performax 4EX :
    - Centralise la gestion des mouvements, états, erreurs, logs, etc.
    - Sert d'interface entre l'UI, le contrôleur bas-niveau et la chaîne d'acquisition.
    - IMPORTANT : Les commandes de mouvement (move_to, home, etc.) sont envoyées sans appel à wait_move,
      pour ne jamais bloquer la communication série et permettre la lecture continue de la position.
      On considère le système parfait (la consigne est toujours atteinte), la robustesse sera ajoutée plus tard.
    - NOUVELLE ARCHITECTURE :
      Un worker unique (thread) gère toute la communication série via une file d'attente de commandes.
      L'UI et le reste du code ajoutent des commandes à la file, et lisent les positions via le buffer mis à jour par le worker.
      Cela garantit l'absence de conflit série et l'alignement avec AcquisitionManager.
    """

    # Signaux Qt
    status_changed = pyqtSignal(str)              # _AcquisitionStatus
    error_occurred = pyqtSignal(str)             # Message d'erreur
    logMessage = pyqtSignal(str)                # Message de log
    configuration_changed = pyqtSignal(dict)  # Signal de configuration modifiée
    mode_changed = pyqtSignal(object)  # AcquisitionMode - Exploration ou Export
    position_changed = pyqtSignal(float, float)  # x, y
    scan_segment_changed = pyqtSignal(str, str, bool)  # segment_id, segment_type, is_active_line
    scan_line_started = pyqtSignal(str)  # segment_id au début d'une scan_line
    scan_line_ended = pyqtSignal(str)    # segment_id à la fin d'une scan_line

    MODE_EXPLORATION = "exploration"
    MODE_EXPORT = "export"


    def __init__(self, dll_path=None, params=None, parent=None):
        super().__init__(parent)
        print("[StageManager] Initialisation du StageManager et démarrage du worker...")
        self.controller = ArcusPerformax4EXStageController(dll_path, params)
        # États internes
        self.connected = self.controller.is_opened()  # État de connexion initialisé à False
        self.error = None      # Attribut pour la gestion des erreurs
        self.mode = self.MODE_EXPLORATION
        # Initialisation du statut global selon l'état du contrôleur
        if self.controller.is_opened():
            self.acquisition_status = _AcquisitionStatus.RUNNING
        else:
            self.acquisition_status = _AcquisitionStatus.ERROR  # STOPPED = fermeture propre

        self._movement_in_progress = False
        self._current_config = {}  # Dictionnaire centralisé pour gérer les changements de configuration
        self.position_buffer = Position_AdaptiveBuffer()  # Buffer pour la lecture continue de la position
        if not hasattr(self, 'queue_prioritaire'):
            self.queue_prioritaire = queue.Queue()
        if not hasattr(self, 'queue_normale'):
            self.queue_normale = queue.Queue()
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_running = True
        self._worker_thread.start()


    # ========================
    # API PUBLIQUE DU STAGE MANAGER
    # ========================

    # === METHODES PRINCIPALES ===

    def add_command_to_queue(self, cmd):
        """
        Ajoute une commande à la file appropriée.
        - Stop va dans la file prioritaire
        - En mode SCANNING, les commandes normales extérieures sont ignorées/loggées
        - Sinon, ajout dans la file normale
        """
        if getattr(cmd, 'cmd_type', None) == _CommandType.STOP:
            self.queue_prioritaire.put(cmd)
        elif self.acquisition_status == _AcquisitionStatus.SCANNING and not getattr(cmd, 'is_batch', False):
            self.logMessage.emit(f"Commande ignorée (scan en cours) : {cmd.cmd_type}")
        else:
            self.queue_normale.put(cmd)

    def start_homing_monitoring(self, axes=['x', 'y'], interval=0.2):
        """
        Lance la surveillance spécialisée pour le homing.
        Vérifie le statut sw_limit_minus pour confirmer le succès du homing.
        """
        # Arrêter toute surveillance précédente
        if hasattr(self, '_homing_monitoring') and self._homing_monitoring:
            self._homing_monitoring = False
        
        self._homing_monitoring = True
        self._homing_axes = {axis: True for axis in axes}  # État de chaque axe en homing
        self._homing_interval = interval
        self._homing_last_check = time.time()
        
        # Pas besoin d'envoyer de commandes ici, la surveillance périodique dans le worker s'en charge
        self.logMessage.emit(f"[HOMING_MONITORING] Surveillance démarrée pour axes: {axes}")

    def wait_move_manager(self, axis, target, tol=2, timeout=120):
        """
        Attend que la position de l'axe atteigne la consigne (tolérance) et que l'axe ne soit plus en mouvement.
        Utilise le buffer pour la position, et is_moving pour l'état. Permet d'attendre la fin d'un mouvement sans bloquer le thread
        """

        t0 = time.time()
        tol_reached = False
        while time.time() - t0 < timeout:
            latest_samples = self.position_buffer.get_latest_samples(1)
            if latest_samples:
                pos = latest_samples[0].x if axis == 'x' else latest_samples[0].y
                if abs(pos - target) <= tol:
                    if not tol_reached:
                        print(f"[wait_move_manager] Tolérance atteinte à t={time.time()-t0:.3f}s, pos={pos}")
                        tol_reached = True
                    try:
                        moving = self.controller.is_moving(axis)
                        print(f"[wait_move_manager] is_moving={moving} à t={time.time()-t0:.3f}s")
                        if not moving:
                            print(f"[wait_move_manager] Mouvement terminé à t={time.time()-t0:.3f}s")
                            return True
                    except Exception:
                        pass
            time.sleep(0.01)  # Réduit pour le test
        print(f"[wait_move_manager] Timeout ou sortie sans succès pour axis={axis}, target={target}")
        return False


    # === METHODES DE GESTION DES ÉTATS GLOBAUX===

    def set_error(self, error_msg: str):
        """
        Centralise la gestion des erreurs:
        - Stocke le message d'erreur
        - Émet le signal error_occurred
        - Change le statut global
        
        Cette méthode doit être utilisée pour toutes les erreurs.
        """
        self.error = error_msg
        self.error_occurred.emit(error_msg)
        self.status_changed.emit("Error from StageManager")

    def set_mode(self, mode):
        """
        Définit le mode et émet le signal.
        """
        if mode not in [self.MODE_EXPLORATION, self.MODE_EXPORT]:
            raise ValueError(f"Mode inconnu : {mode}")
        self.mode = mode
        if mode == self.MODE_EXPORT:
            self.status_changed.emit("ui_buttons_disabled")
        else:
            self.status_changed.emit("ui_buttons_enabled")

    def update_configuration(self, config: dict):
        """
        Met à jour la configuration centrale et émet le signal si modifiée.
        """
        old_config = self._current_config.copy()
        self._current_config.update(config)
        if old_config != self._current_config:
            self.configuration_changed.emit(self._current_config.copy())


    # === METHODES DE SCAN 2D ===

    def inject_scan_batch(self, batch_commands):
        """
        Injecte un batch de commandes (scan) dans la file normale :
        - Purge la file normale
        - Définit l'état global en mode SCANNING
        - Accepte une configuration de scan : dict avec les clés nécessaires
        - Utilise la trajectoire segmentée
        """
        # Purge la file normale
        while not self.queue_normale.empty():
            try:
                self.queue_normale.get_nowait()
                self.queue_normale.task_done()
            except Exception:
                break
        
        # Détection du format et conversion
        parcours = []
        
        # Si c'est une config de scan (dict avec les clés nécessaires)
        if isinstance(batch_commands, dict) and all(k in batch_commands for k in ['x_min', 'x_max', 'y_min', 'y_max', 'N']):
            self.logMessage.emit("[inject_scan_batch] Configuration de scan détectée, génération de la trajectoire segmentée...")
            
            try:
                scan_config = Scan2DConfigurator(
                    batch_commands['x_min'],
                    batch_commands['x_max'],
                    batch_commands['y_min'],
                    batch_commands['y_max'],
                    batch_commands['N'],
                    batch_commands.get('y_nb', 10),  # Valeur par défaut pour y_nb
                    batch_commands.get('timer_ms', 0),  # Valeur par défaut pour timer_ms
                    batch_commands.get('mode', 'E')
                )
                
                scan_params = scan_config.to_dict()
                segments = scan_config.get_segmented_trajectory()
                parcours = scan_config.get_points_from_segments(segments)
                self.logMessage.emit(f"[inject_scan_batch] {len(segments)} segments générés, {len(parcours)} points")
            except Exception as e:
                self.set_error(f"Erreur lors de la génération de la trajectoire de scan: {e}")
                return False


        # Crée le scan manager avec info segments
        self._scan_manager = _Scan2DExecutor(parcours, stage_manager=self)
        # Active le mode SCANNING
        self.acquisition_status = _AcquisitionStatus.SCANNING
        self.logMessage.emit(f"Batch de scan injecté ({len(parcours)} points)")



# ========================
# PASS-THROUGH - API PUBLIQUES MODULES EXTERNES 
# ========================
    # === API BUFFER (PASS-THROUGH) ===

    def append_position_sample(self, sample):
        """
        Ajoute un échantillon de position au buffer courant.
        """
        return self.position_buffer.append_sample(sample)

    def get_latest_position_samples(self, count: int):
        """
        Retourne les 'count' derniers échantillons de position.
        """
        return self.position_buffer.get_latest_samples(count)

    def get_all_position_samples(self):
        """
        Retourne tous les échantillons de position disponibles.
        """
        return self.position_buffer.get_all_samples()

    def flush_position_buffer_for_export(self):
        """
        Flush les échantillons de position pour export (mode export uniquement).
        """
        return self.position_buffer.flush_for_export()

    def clear_position_buffer(self):
        """
        Vide le buffer de position courant.
        """
        return self.position_buffer.clear_buffer()

    def add_position_production_callback(self, callback):
        """
        Ajoute un callback pour le flush en mode production (positions).
        """
        return self.position_buffer.add_production_callback(callback)

    @property
    def position_buffer_mode(self):
        """
        Retourne le mode courant du buffer de position ('exploration' ou 'export').
        """
        return self.position_buffer.current_mode

    @property
    def position_buffer_size(self):
        """
        Retourne la taille actuelle du buffer de position courant.
        """
        return self.position_buffer.current_size

    # === API CONTROLLER PASS-THROUGH ===

    # --- HOMING ---
    def get_axis_homed_status(self, axis, callback):
        """
        Vérifie si un axe spécifique a été homé (asynchrone, résultat via callback).
        :param axis: Axe à vérifier ('x', 'y', 'z', 'u')
        :param callback: fonction appelée avec le résultat (True/False)
        Exemple d'utilisation :
            def on_result(result):
                print('Homed:', result)
            manager.get_axis_homed_status('x', callback=on_result)
        """
        cmd = _CommandContainer(_CommandType.GET_AXIS_HOMED_STATUS, args=[axis], callback=callback)
        self.add_command_to_queue(cmd)

    def get_all_homed_status(self, callback):
        """
        Retourne l'état du homing pour tous les axes (asynchrone, résultat via callback).
        :param callback: fonction appelée avec le résultat (liste [X, Y, Z, U] True/False)
        Exemple d'utilisation :
            def on_result(result):
                print('All homed:', result)
            manager.get_all_homed_status(callback=on_result)
        """
        cmd = _CommandContainer(_CommandType.GET_ALL_HOMED_STATUS, callback=callback)
        self.add_command_to_queue(cmd)

    def home_lock(self, axis, callback):
        """
        Homing de l'axe (bloquant, asynchrone, résultat via callback).
        :param axis: Axe à hommer
        :param callback: fonction appelée avec le résultat (True/False ou None)
        """
        cmd = _CommandContainer(_CommandType.HOME_LOCK, args=[axis], callback=callback)
        self.add_command_to_queue(cmd)

    def home(self, axis):
        print(f"[DEBUG][StageManager] home appelé - axe: {axis}")
        print(f"[DEBUG][StageManager] État homed avant home - {axis}: {self.controller.get_axis_homed_status(axis)}")
        
        # Démarrer la surveillance spécialisée pour le homing
        self.start_homing_monitoring(axes=[axis], interval=0.2)
        
        print(f"[DEBUG][StageManager] Commande HOME ajoutée à la queue pour axe: {axis}")
        cmd = _CommandContainer(_CommandType.HOME, [axis])
        self.add_command_to_queue(cmd)
        return True

    def home_both_lock(self, callback):
        """
        Homing simultané des axes X et Y (bloquant, asynchrone, résultat via callback).
        :param callback: fonction appelée avec le résultat (True/False ou None)
        """
        cmd = _CommandContainer(_CommandType.HOME_BOTH_LOCK, callback=callback)
        self.add_command_to_queue(cmd)

    def home_both(self):
        print("[DEBUG][StageManager] home_both appelé")
        
        # Démarrer la surveillance spécialisée pour le homing
        self.start_homing_monitoring(axes=['x', 'y'], interval=0.2)
        
        print("[DEBUG][StageManager] Commande HOME_BOTH ajoutée à la queue")
        cmd = _CommandContainer(_CommandType.HOME_BOTH, [])
        self.add_command_to_queue(cmd)
        return True

    def set_axis_homed(self, axis, value=True, callback=None):
        """
        Définit l'état de homing logiciel pour un axe (asynchrone, résultat via callback).
        :param axis: Axe à modifier
        :param value: True/False
        :param callback: fonction appelée avec le résultat
        """
        cmd = _CommandContainer(_CommandType.SET_AXIS_HOMED, args=[axis], kwargs={'value': value}, callback=callback)
        self.add_command_to_queue(cmd)

    def reset_homing_status(self, axis=None, callback=None):
        """
        Remet à zéro l'état du homing (asynchrone, résultat via callback).
        :param axis: Axe spécifique ou None
        :param callback: fonction appelée avec le résultat
        """
        cmd = _CommandContainer(_CommandType.RESET_HOMING_STATUS, args=[axis] if axis is not None else [], callback=callback)
        self.add_command_to_queue(cmd)

    # --- CONFIGURATION DES PARAMÈTRES (VITESSE/ACCÉLÉRATION) ---
    def get_axis_params(self, axis, callback):
        """
        Récupère les paramètres actuels d'un axe (asynchrone, résultat via callback).
        :param axis: Axe à interroger ('x' ou 'y')
        :param callback: fonction appelée avec le résultat
        """
        cmd = _CommandContainer(_CommandType.GET_AXIS_PARAMS, args=[axis], callback=callback)
        self.add_command_to_queue(cmd)

    def set_axis_params(self, axis, ls=None, hs=None, acc=None, dec=None):
        """
        Configure les paramètres de vitesse pour un axe spécifique.
        :param axis: Axe à configurer ('x' ou 'y')
        :param ls: Vitesse basse (optionnel)
        :param hs: Vitesse haute (optionnel)
        :param acc: Accélération (optionnel)
        :param dec: Décélération (optionnel)
        :return: Les paramètres effectivement appliqués
        """
        print(f'[StageManager] Reçu set_axis_params : axis={axis}, ls={ls}, hs={hs}, acc={acc}, dec={dec}')
        cmd = _CommandContainer(_CommandType.SET_AXIS_PARAMS, args=[axis], kwargs={'ls': ls, 'hs': hs, 'acc': acc, 'dec': dec})
        self.add_command_to_queue(cmd)

    def apply_axis_params(self, axis, params, callback=None):
        """
        Applique les paramètres de vitesse pour un axe spécifique (asynchrone, résultat via callback).
        :param axis: Axe à configurer ('x' ou 'y')
        :param params: Dictionnaire avec les paramètres à appliquer (ls, hs, acc, dec)
        :param callback: fonction appelée avec le résultat
        """
        cmd = _CommandContainer(_CommandType.APPLY_AXIS_PARAMS, args=[axis, params], callback=callback)
        self.add_command_to_queue(cmd)

    # --- MOUVEMENT ET CONTRÔLE ---
    def move_to(self, axis, position_inc):
        print(f"[DEBUG][StageManager] move_to appelé - axe: {axis}, position: {position_inc}")
        print(f"[DEBUG][StageManager] État homed avant move_to - {axis}: {self.controller.get_axis_homed_status(axis)}")
        
        if not self.controller.get_axis_homed_status(axis):
            error_msg = f"Erreur MOVE_TO: Homing requis pour l'axe {axis.upper()}. Utilisez home('{axis}') d'abord."
            self.set_error(error_msg)
            return False

        print(f"[DEBUG][StageManager] Envoi commande MOVE_TO au contrôleur - axe: {axis}, position: {position_inc}")
        cmd = _CommandContainer(_CommandType.MOVE_TO, [axis, position_inc])
        self.add_command_to_queue(cmd)
        return True

    def is_moving(self, axis="all", callback=None):
        """
        Vérifie si un ou plusieurs axes sont en mouvement (asynchrone).
        :param axis: Axe à vérifier ('x', 'y', 'z', 'u' ou 'all')
        :param callback: fonction appelée avec le résultat (True/False)
        """
        cmd = _CommandContainer(_CommandType.IS_MOVING, args=[axis], callback=callback)
        self.add_command_to_queue(cmd)

    def wait_move(self, axis, timeout=None, callback=None):
        """
        Attend la fin du mouvement sur l'axe spécifié (asynchrone, résultat via callback).
        :param axis: 'x' ou 'y' (obligatoire)
        :param timeout: en secondes (recommandé)
        :param callback: fonction appelée avec le résultat
        """
        cmd = _CommandContainer(_CommandType.WAIT_MOVE, args=[axis], kwargs={'timeout': timeout}, callback=callback)
        self.add_command_to_queue(cmd)

    def stop(self, axis, immediate=False):
        """
        Arrêt du mouvement de l'axe.
        :param axis: Axe à arrêter ('x' ou 'y')
        :param immediate: Si True, arrêt immédiat (ABORT), sinon arrêt progressif (STOP)
        """
        print(f'[StageManager] Reçu stop : axis={axis}, immediate={immediate}')
        cmd = _CommandContainer(_CommandType.STOP, args=[axis], kwargs={'immediate': immediate})
        self.add_command_to_queue(cmd)

    def enable(self, x_on, y_on):
        """
        Active/désactive les sorties X et Y.
        Utilise la méthode pylablib native enable_axis().
        :param x_on: True pour activer X
        :param y_on: True pour activer Y
        """
        cmd = _CommandContainer(_CommandType.ENABLE, args=[x_on, y_on])
        self.add_command_to_queue(cmd)

    # --- VITESSE ---
    def get_current_axis_speed(self, axis="all", callback=None):
        """
        Obtient la vitesse instantanée d'un axe (asynchrone, résultat via callback).
        :param axis: Axe à interroger ('x', 'y', 'z', 'u' ou 'all')
        :param callback: fonction appelée avec le résultat
        """
        cmd = _CommandContainer(_CommandType.GET_CURRENT_AXIS_SPEED, args=[axis], callback=callback)
        self.add_command_to_queue(cmd)

    def get_global_speed(self, callback=None):
        """
        Obtient la vitesse globale (asynchrone, résultat via callback).
        :param callback: fonction appelée avec le résultat
        """
        cmd = _CommandContainer(_CommandType.GET_GLOBAL_SPEED, callback=callback)
        self.add_command_to_queue(cmd)

    def get_axis_speed(self, axis="all", callback=None):
        """
        Obtient la vitesse configurée pour un axe (asynchrone, résultat via callback).
        :param axis: Axe à interroger ('x', 'y', 'z', 'u' ou 'all')
        :param callback: fonction appelée avec le résultat
        """
        cmd = _CommandContainer(_CommandType.GET_AXIS_SPEED, args=[axis], callback=callback)
        self.add_command_to_queue(cmd)

    def set_global_speed(self, speed):
        """
        Configure la vitesse globale (méthode PyLab)
        """
        cmd = _CommandContainer(_CommandType.SET_GLOBAL_SPEED, args=[speed])
        self.add_command_to_queue(cmd)

    def set_axis_speed(self, axis, speed):
        """
        Configure la vitesse pour un axe spécifique (méthode PyLab).
        :param axis: Axe à configurer ('x' ou 'y')
        :param speed: Vitesse en Hz (0 = utilise vitesse globale)
        """
        cmd = _CommandContainer(_CommandType.SET_AXIS_SPEED, args=[axis, speed])
        self.add_command_to_queue(cmd)

    def set_position_reference(self, axis, value=0):
        """
        Fixe la référence de position pour un axe (argument harmonisé : value).
        """
        cmd = _CommandContainer(_CommandType.SET_POSITION_REFERENCE, args=[axis, value])
        self.add_command_to_queue(cmd)

    # --- LECTURE D'ÉTAT ET POSITION ---
    def get_position(self, axis, callback):
        """
        Retourne la position de l'axe (asynchrone, résultat via callback).
        :param axis: Axe à interroger ('x' ou 'y')
        :param callback: fonction appelée avec le résultat
        """
        cmd = _CommandContainer(_CommandType.GET_POSITION, args=[axis], callback=callback)
        self.add_command_to_queue(cmd)

    def get_status(self, axis, callback):
        """
        Retourne le statut complet de l'axe (asynchrone, résultat via callback).
        :param axis: Axe à interroger ('x' ou 'y')
        :param callback: fonction appelée avec le résultat
        """
        cmd = _CommandContainer(_CommandType.GET_STATUS, args=[axis], callback=callback)
        self.add_command_to_queue(cmd)

    # --- FERMETURE CONTROLEUR ---

    def close(self, callback=None):
        """
        Ferme la connexion au contrôleur (asynchrone, résultat via callback).
        Arrête proprement le worker thread pour éviter toute émission de signaux après destruction Qt.
        """
        # Arrêt du worker thread
        self._worker_running = False
        if hasattr(self, '_worker_thread') and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
        # Fermeture du contrôleur bas niveau
        cmd = _CommandContainer(_CommandType.CLOSE, callback=callback)
        self.add_command_to_queue(cmd)

    # === API GEOMETRICAL PARAMETERS CONVERSION ===
    def get_bench_limits_cm(self):
        return get_bench_limits_cm()

    def clamp_rect_cm(self, x_min, x_max, y_min, y_max):
        return clamp_rect_cm(x_min, x_max, y_min, y_max)

    def inc_to_cm(self, inc):
        return inc_to_cm(inc)

    def cm_to_inc(self, cm):
        return cm_to_inc(cm)

# ========================
#  METHODES INTERNES AU STAGE MANAGER --> WORKER
# ========================

    # === WORKER ===
    def _worker_loop(self):
        """
        Boucle worker complète :
        - Traite la file prioritaire (Stop)
        - Sépare explicitement la logique RUNNING/SCANNING
        - Lecture de position continue dans tous les cas
        - En mode SCANNING, gestion non bloquante du scan via _Scan2DExecutor
        - En mode RUNNING, traitement classique des commandes
        """
        self._scan_manager = None
        while self._worker_running:
            try:
                # 1. Traiter la file prioritaire (Stop)
                try:
                    cmd = self.queue_prioritaire.get_nowait()
                    if getattr(cmd, 'cmd_type', None) == _CommandType.STOP:
                        try:
                            self.controller.stop(*cmd.args, **cmd.kwargs)
                            self.logMessage.emit(f"[STOP] Arrêt demandé (args={cmd.args}, kwargs={cmd.kwargs})")
                        except Exception as e:
                            self.set_error(f"Erreur lors du STOP: {e}")
                        # Si Stop pendant un scan, purge la file normale et stoppe le scan
                        if self.acquisition_status == _AcquisitionStatus.SCANNING:
                            while not self.queue_normale.empty():
                                try:
                                    self.queue_normale.get_nowait()
                                    self.queue_normale.task_done()
                                except Exception:
                                    break
                            self.acquisition_status = _AcquisitionStatus.RUNNING
                            self.logMessage.emit("Scan interrompu par Stop")
                        self.queue_prioritaire.task_done()
                        continue
                except queue.Empty:
                    pass

                # 2. Logique SCANNING
                if self.acquisition_status == _AcquisitionStatus.SCANNING:
                    if self._scan_manager is None:
                        self.set_error("ERREUR LOGIQUE: SCANNING sans _scan_manager initialisé")
                        self.acquisition_status = _AcquisitionStatus.ERROR
                        continue
                    # Lecture continue de position
                    try:
                        x = self.controller.get_position('x')
                        y = self.controller.get_position('y')
                        self.position_buffer.append_sample(PositionSample(x=x, y=y))
                        self.position_changed.emit(x, y)
                        pos = (x, y)
                    except Exception as e:
                        self.set_error(f"Erreur lecture continue position: {e}")
                        pos = (None, None)
                    # Avancer le scan via _scan_manager
                    self._scan_manager.step(pos, self.controller)
                    # Log progression
                    if self._scan_manager.is_elementary_move_in_progress():
                        self.logMessage.emit(f"[SCAN2D] Consigne en cours: {self._scan_manager.get_current_elementary_move()}")
                    if self._scan_manager.is_finished():
                        self.acquisition_status = _AcquisitionStatus.RUNNING
                        self._scan_manager = None
                        self.logMessage.emit("Fin du scan (batch)")
                        self.status_changed.emit('scan2d_finished')
                    time.sleep(0.01)
                    continue

                # 3. Logique RUNNING
                if self.acquisition_status == _AcquisitionStatus.RUNNING:
                    try:
                        cmd = self.queue_normale.get_nowait()
                        print(f'[StageManager] Worker: commande reçue : {getattr(cmd, "cmd_type", None)}, args={getattr(cmd, "args", None)}')
                        self._execute_worker_command(cmd)
                        self.queue_normale.task_done()
                    except queue.Empty:
                        pass
                    
                    # Surveillance périodique pour homing
                    if hasattr(self, '_homing_monitoring') and self._homing_monitoring:
                        current_time = time.time()
                        if current_time - self._homing_last_check >= self._homing_interval:
                            self._homing_last_check = current_time
                            
                            # Vérifier si au moins un axe bouge encore
                            if not any(self._homing_axes.values()):
                                self.logMessage.emit("[HOMING_MONITORING] Tous les axes ont fini de bouger, arrêt automatique")
                                self._homing_monitoring = False
                            else:
                                # Continuer la surveillance pour les axes qui bougent encore
                                for ax in self._homing_axes.keys():
                                    if self._homing_axes[ax]:
                                        def on_homing_moving_result(moving, axis=ax):
                                            if not moving and self._homing_axes.get(axis, False):
                                                self._homing_axes[axis] = False
                                                self.logMessage.emit(f"[HOMING_MONITORING] Axe {axis} a fini de bouger, vérification du statut...")
                                                
                                                # Vérifier le statut sw_limit_minus pour confirmer le homing
                                                def on_status_result(status, current_axis=axis):
                                                    if 'sw_limit_minus' in status:
                                                        self.controller.set_axis_homed(current_axis, True)
                                                        self.logMessage.emit(f"[HOMING_MONITORING] Homing réussi pour axe {current_axis} (sw_limit_minus détecté)")
                                                    else:
                                                        self.logMessage.emit(f"[HOMING_MONITORING] Homing échoué pour axe {current_axis} (sw_limit_minus non détecté)")
                                                    
                                                    # Vérifier si tous les axes ont fini
                                                    if not any(self._homing_axes.values()):
                                                        self._homing_monitoring = False
                                                        self.logMessage.emit("[HOMING_MONITORING] Surveillance terminée pour tous les axes")
                                                
                                                self.add_command_to_queue(_CommandContainer(_CommandType.GET_STATUS, args=[axis], callback=on_status_result))
                                        
                                        self.add_command_to_queue(_CommandContainer(_CommandType.IS_MOVING, args=[ax], callback=on_homing_moving_result))
                
                    # Lecture continue de position
                    try:
                        x = self.controller.get_position('x')
                        y = self.controller.get_position('y')
                        self.position_buffer.append_sample(PositionSample(x=x, y=y))
                        self.position_changed.emit(x, y)
                    except Exception as e:
                        self.set_error(f"Erreur lecture continue position: {e}")
                    time.sleep(0.01)
                    continue

            except Exception as e:
                self.set_error(f"Erreur worker: {e}")
                time.sleep(0.1)


    def _execute_worker_command(self, cmd):
        """
        Exécute une commande classique du worker (hors STOP, batch/scan).
        La commande doit être de type StageCommand.
        """
        if getattr(cmd, 'cmd_type', None) == _CommandType.GET_AXIS_HOMED_STATUS:
            axis = cmd.args[0]
            try:
                result = self.controller.get_axis_homed_status(axis)
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[GET_AXIS_HOMED_STATUS] {axis} -> {result}")
            except Exception as e:
                self.set_error(f"Erreur GET_AXIS_HOMED_STATUS: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.GET_ALL_HOMED_STATUS:
            try:
                result = self.controller.get_all_homed_status()
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[GET_ALL_HOMED_STATUS] -> {result}")
            except Exception as e:
                self.set_error(f"Erreur GET_ALL_HOMED_STATUS: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.HOME_LOCK:
            axis = cmd.args[0]
            try:
                result = self.controller.home_lock(axis)
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[HOME_LOCK] {axis} -> {result}")
            except Exception as e:
                self.set_error(f"Erreur HOME_LOCK: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.HOME_BOTH_LOCK:
            try:
                result = self.controller.home_both_lock()
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[HOME_BOTH_LOCK] -> {result}")
            except Exception as e:
                self.set_error(f"Erreur HOME_BOTH_LOCK: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.SET_AXIS_HOMED:
            axis = cmd.args[0]
            value = cmd.kwargs.get('value', True)
            try:
                result = self.controller.set_axis_homed(axis, value)
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[SET_AXIS_HOMED] {axis} = {value} -> {result}")
            except Exception as e:
                self.set_error(f"Erreur SET_AXIS_HOMED: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.RESET_HOMING_STATUS:
            axis = cmd.args[0] if cmd.args else None
            try:
                result = self.controller.reset_homing_status(axis)
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[RESET_HOMING_STATUS] {axis} -> {result}")
            except Exception as e:
                self.set_error(f"Erreur RESET_HOMING_STATUS: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.GET_AXIS_PARAMS:
            axis = cmd.args[0]
            try:
                result = self.controller.get_axis_params(axis)
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[GET_AXIS_PARAMS] {axis} -> {result}")
            except Exception as e:
                self.set_error(f"Erreur GET_AXIS_PARAMS: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.GET_CURRENT_AXIS_SPEED:
            axis = cmd.args[0]
            try:
                result = self.controller.get_current_axis_speed(axis)
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[GET_CURRENT_AXIS_SPEED] {axis} -> {result}")
            except Exception as e:
                self.set_error(f"Erreur GET_CURRENT_AXIS_SPEED: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.GET_GLOBAL_SPEED:
            try:
                result = self.controller.get_global_speed()
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[GET_GLOBAL_SPEED] -> {result}")
            except Exception as e:
                self.set_error(f"Erreur GET_GLOBAL_SPEED: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.GET_AXIS_SPEED:
            axis = cmd.args[0]
            try:
                result = self.controller.get_axis_speed(axis)
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[GET_AXIS_SPEED] {axis} -> {result}")
            except Exception as e:
                self.set_error(f"Erreur GET_AXIS_SPEED: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.WAIT_MOVE:
            axis = cmd.args[0]
            timeout = cmd.kwargs.get('timeout', None)
            try:
                result = self.controller.wait_move(axis, timeout)
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[WAIT_MOVE] {axis} -> {result}")
            except Exception as e:
                self.set_error(f"Erreur WAIT_MOVE: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.GET_POSITION:
            axis = cmd.args[0]
            try:
                result = self.controller.get_position(axis)
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[GET_POSITION] {axis} -> {result}")
            except Exception as e:
                self.set_error(f"Erreur GET_POSITION: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.GET_STATUS:
            axis = cmd.args[0]
            try:
                result = self.controller.get_status(axis)
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[GET_STATUS] {axis} -> {result}")
            except Exception as e:
                self.set_error(f"Erreur GET_STATUS: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.CLOSE:
            try:
                result = self.controller.close()
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[CLOSE] -> {result}")
            except Exception as e:
                self.set_error(f"Erreur CLOSE: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.MOVE_TO:
            axis, target = cmd.args
            try:
                self.controller.move_to(axis, target)
                self.logMessage.emit(f"[MOVE_TO] {axis} -> {target}")
            except Exception as e:
                self.set_error(f"Erreur MOVE_TO: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.HOME:
            axis = cmd.args[0]
            try:
                self.controller.home(axis)
                self.logMessage.emit(f"[HOME] Homing axe {axis}")
            except Exception as e:
                self.set_error(f"Erreur HOME: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.HOME_BOTH:
            try:
                self.controller.home_both()
                self.logMessage.emit("[HOME_BOTH] Homing X et Y")
            except Exception as e:
                self.set_error(f"Erreur HOME_BOTH: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.SET_AXIS_PARAMS:
            try:
                self.controller.set_axis_params(*cmd.args, **cmd.kwargs)
                self.logMessage.emit(f"[SET_AXIS_PARAMS] args={cmd.args}, kwargs={cmd.kwargs}")
            except Exception as e:
                self.set_error(f"Erreur SET_AXIS_PARAMS: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.APPLY_AXIS_PARAMS:
            try:
                self.controller.apply_axis_params(*cmd.args, **cmd.kwargs)
                self.logMessage.emit(f"[APPLY_AXIS_PARAMS] args={cmd.args}, kwargs={cmd.kwargs}")
            except Exception as e:
                self.set_error(f"Erreur APPLY_AXIS_PARAMS: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.SET_AXIS_SPEED:
            try:
                self.controller.set_axis_speed(*cmd.args, **cmd.kwargs)
                self.logMessage.emit(f"[SET_AXIS_SPEED] args={cmd.args}, kwargs={cmd.kwargs}")
            except Exception as e:
                self.set_error(f"Erreur SET_AXIS_SPEED: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.SET_GLOBAL_SPEED:
            try:
                self.controller.set_global_speed(*cmd.args, **cmd.kwargs)
                self.logMessage.emit(f"[SET_GLOBAL_SPEED] args={cmd.args}, kwargs={cmd.kwargs}")
            except Exception as e:
                self.set_error(f"Erreur SET_GLOBAL_SPEED: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.ENABLE:
            try:
                self.controller.enable(*cmd.args, **cmd.kwargs)
                self.logMessage.emit(f"[ENABLE] args={cmd.args}, kwargs={cmd.kwargs}")
            except Exception as e:
                self.set_error(f"Erreur ENABLE: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.SET_POSITION_REFERENCE:
            try:
                self.controller.set_position_reference(*cmd.args, **cmd.kwargs)
                self.logMessage.emit(f"[SET_POSITION_REFERENCE] args={cmd.args}, kwargs={cmd.kwargs}")
            except Exception as e:
                self.set_error(f"Erreur SET_POSITION_REFERENCE: {e}")
        elif getattr(cmd, 'cmd_type', None) == _CommandType.SCAN_2D:
            # déjà géré dans la partie SCANNING
            pass
        elif getattr(cmd, 'cmd_type', None) == _CommandType.IS_MOVING:
            axis = cmd.args[0]
            try:
                moving = self.controller.is_moving(axis)
                if cmd.callback:
                    cmd.callback(moving)
                self.logMessage.emit(f"[IS_MOVING] {axis} -> {moving}")
                
                # Logique de surveillance périodique pour mouvements normaux
                if hasattr(self, '_is_moving_polling') and self._is_moving_polling:
                    current_time = time.time()
                    if current_time - self._is_moving_last_check >= self._is_moving_interval:
                        self._is_moving_last_check = current_time
                        
                        # Vérifier si au moins un axe bouge encore
                        if not any(self._axes_moving.values()):
                            self.logMessage.emit("[PERIODIC_IS_MOVING] Tous les axes ont fini de bouger, arrêt automatique")
                            self._is_moving_polling = False
                        else:
                            # Continuer la surveillance pour les axes qui bougent encore
                            for ax in self._axes_moving.keys():
                                if self._axes_moving[ax]:
                                    def on_moving_result(moving, axis=ax):
                                        if not moving and self._axes_moving.get(axis, False):
                                            self._axes_moving[axis] = False
                                            self.logMessage.emit(f"[PERIODIC_IS_MOVING] Axe {axis} a fini de bouger")
                                    
                                    self.add_command_to_queue(_CommandContainer(_CommandType.IS_MOVING, args=[axis], callback=on_moving_result))
                

            except Exception as e:
                self.set_error(f"Erreur IS_MOVING: {e}")
        else:
            self.logMessage.emit(f"[WORKER] Commande inconnue ou non gérée: {getattr(cmd, 'cmd_type', None)}")


# =========================
# CLASSES INTERNES
# =========================

class _AcquisitionStatus(Enum):
    """
    États possibles de l'acquisition
    - STOPPED : fermeture propre, déclenche le processus de fermeture du système
    - RUNNING : acquisition active
    - ERROR : erreur critique
    - SCANNING : mode scan en cours
    """
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"
    SCANNING = "scanning"

class _CommandType(Enum):
    MOVE_TO = auto()
    HOME = auto()
    HOME_BOTH = auto()
    STOP = auto()
    SET_AXIS_PARAMS = auto()
    APPLY_AXIS_PARAMS = auto()
    SET_AXIS_SPEED = auto()
    SET_GLOBAL_SPEED = auto()
    ENABLE = auto()
    SET_POSITION_REFERENCE = auto()
    SCAN_2D = auto()
    IS_MOVING = auto()
    GET_AXIS_HOMED_STATUS = auto()
    GET_ALL_HOMED_STATUS = auto()
    HOME_LOCK = auto()
    HOME_BOTH_LOCK = auto()
    SET_AXIS_HOMED = auto()
    RESET_HOMING_STATUS = auto()
    GET_AXIS_PARAMS = auto()
    GET_CURRENT_AXIS_SPEED = auto()
    GET_GLOBAL_SPEED = auto()
    GET_AXIS_SPEED = auto()
    WAIT_MOVE = auto()
    GET_POSITION = auto()
    GET_STATUS = auto()
    CLOSE = auto()
    OTHER = auto()

class _CommandContainer:
    def __init__(self, cmd_type, args=None, kwargs=None, callback=None):
        self.cmd_type = cmd_type
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}
        self.callback = callback  # Pour retour asynchrone si besoin

class _Scan2DExecutor:
    def __init__(self, parcours, tol=2, timeout=120, stage_manager=None):
        """
        parcours : liste ordonnée de consignes (x, y) ou (x, y, segment_info)
        tol : tolérance sur la position (même unité que x, y)
        timeout : temps max par consigne (secondes)
        stage_manager : référence au StageManager pour émettre des signaux
        """
        self.parcours = list(parcours)
        self.tol = tol
        self.timeout = timeout
        self.stage_manager = stage_manager
        self.current_idx = -1
        self.current_target = None
        self.current_segment = None
        self.is_moving = False
        self.move_start_time = None
        self.pending_segment = None  # Segment à activer une fois arrivé

    def start_next_move(self, controller):
        """Lance la consigne suivante si disponible, sinon marque le scan comme terminé."""
        self.current_idx += 1
        if self.current_idx < len(self.parcours):
            # Extraire les infos du point
            if len(self.parcours[self.current_idx]) == 3 and isinstance(self.parcours[self.current_idx][2], dict):
                x, y, segment_info = self.parcours[self.current_idx]
                self.current_target = (x, y)
                
                # Stocker le segment pour l'activer une fois arrivé
                if segment_info != self.current_segment:
                    self.pending_segment = segment_info
            else:
                # Format simple sans segment info
                self.current_target = self.parcours[self.current_idx][:2]
                x, y = self.current_target
            
            controller.move_to('x', x)
            controller.move_to('y', y)
            self.is_moving = True
            self.move_start_time = time.time()
        else:
            # Scan terminé
            print(f"[SCAN2D] Fin du parcours 2D ({self.current_idx+1} points parcourus)")
            if self.stage_manager:
                # Émettre signal de fin avec segment vide
                self.stage_manager.scan_segment_changed.emit("", "finished", False)
                # Émettre statut de fin
                self.stage_manager.status_changed.emit('scan2d_finished')

    def check_move_completed(self, controller):
        """Vérifie si le mouvement est terminé."""
        if not self.is_moving:
            return False
        
        # Vérifier si les deux axes sont arrivés
        x_arrived = controller.is_at_target('x')
        y_arrived = controller.is_at_target('y')
        
        if x_arrived and y_arrived:
            self.is_moving = False
            
            # Activer le segment maintenant qu'on est arrivé
            if self.pending_segment is not None:
                previous_segment = self.current_segment
                self.current_segment = self.pending_segment
                self.pending_segment = None
                
                if self.stage_manager:
                    is_active_line = (self.current_segment['type'] == 'scan_line')
                    self.stage_manager.scan_segment_changed.emit(
                        self.current_segment['id'],
                        self.current_segment['type'],
                        is_active_line
                    )
                    print(f"[SCAN2D] Arrivé au segment: {self.current_segment['id']} ({self.current_segment['type']})")
                    self.stage_manager.logMessage.emit(
                        f"[SCAN2D] Arrivé au segment: {self.current_segment['id']} ({self.current_segment['type']})"
                    )
                    
                    # Émettre signaux spécifiques pour début/fin de scan_line
                    if is_active_line:
                        self.stage_manager.scan_line_started.emit(self.current_segment['id'])
                        print(f"[SCAN2D] Début ligne de scan: {self.current_segment['id']}")
                    elif previous_segment and previous_segment['type'] == 'scan_line':
                        self.stage_manager.scan_line_ended.emit(previous_segment['id'])
                        print(f"[SCAN2D] Fin ligne de scan: {previous_segment['id']}")
            
            return True
        
        # Timeout de sécurité
        if time.time() - self.move_start_time > 30:
            print(f"[SCAN2D] TIMEOUT mouvement vers {self.current_target}")
            self.is_moving = False
            return True
        
        return False

    def step(self, position, controller):
        """
        À appeler à chaque itération du worker.
        - Si aucun mouvement en cours, lance la prochaine consigne.
        - Sinon, vérifie si le mouvement est terminé.
        """
        if not self.is_moving:
            self.start_next_move(controller)
        else:
            if self.check_move_completed(controller):
                # Mouvement terminé, on peut lancer le suivant
                self.start_next_move(controller)

    def get_current_elementary_move(self):
        """Retourne la consigne en cours, ou None si fini."""
        if 0 <= self.current_idx < len(self.parcours):
            return self.parcours[self.current_idx][:2]  # Retourne juste (x, y)
        return None

    def is_elementary_move_in_progress(self):
        """Retourne True si un parcours élémentaire est en cours."""
        return self.is_moving

    def is_finished(self):
        """Retourne True si le scan est terminé."""
        return self.current_idx >= len(self.parcours) - 1
    
    def get_current_segment_info(self):
        """Retourne les infos du segment actuel."""
        return self.current_segment 
