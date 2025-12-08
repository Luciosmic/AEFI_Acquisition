# -*- coding: utf-8 -*-

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from ArcusPerformaxPythonController.gui.components.ArcusPerformax4EXStage_GeometricalParametersConversion_Module import (
    get_bench_limits_cm, clamp_rect_cm, inc_to_cm, cm_to_inc
)
from dataclasses import dataclass, field
from datetime import datetime
from .ArcusPerformax4EXStage_DataBuffer_Module import Position_AdaptiveBuffer, PositionSample
import threading
import queue
from enum import Enum, auto
import time # Centralisé ici
from ArcusPerformaxPythonController.controller.ArcusPerformax4EXStage_Controller import ArcusPerformax4EXStageController
        


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
    # API PUBLIQUE DU MODULE
    # ========================

    # === METHODES DE GESTION DES ÉTATS GLOBAUX===

    def set_error(self, error_msg: str):
        self.error = error_msg
        self.error_occured.emit(error_msg)
        self.status_changed.emit("error")

    def set_mode(self, mode):
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

    # === METHODES PRINCIPALES ===

    def add_command(self, cmd):
        """
        Ajoute une commande à la file appropriée.
        - Stop va dans la file prioritaire
        - En mode SCANNING, les commandes normales extérieures sont ignorées/loggées
        - Sinon, ajout dans la file normale
        """
        if getattr(cmd, 'cmd_type', None) == _StageCommandType.STOP:
            self.queue_prioritaire.put(cmd)
        elif self.acquisition_status == _AcquisitionStatus.SCANNING and not getattr(cmd, 'is_batch', False):
            self.logMessage.emit(f"Commande ignorée (scan en cours) : {cmd.cmd_type}")
        else:
            self.queue_normale.put(cmd)


    def start_periodic_is_moving(self, axes=['x', 'y'], interval=0.2):
        """
        Lance un thread qui ajoute périodiquement une commande IS_MOVING à la queue pour chaque axe.
        Peut être stoppé proprement avec stop_periodic_is_moving.
        """
        import threading, time
        self._is_moving_polling = True
        def periodic():
            while self._is_moving_polling and self._worker_running:
                for axis in axes:
                    self.add_command(_StageCommandType.IS_MOVING, axis)
                time.sleep(interval)
        t = threading.Thread(target=periodic, daemon=True)
        t.start()
        self._is_moving_thread = t

    def stop_periodic_is_moving(self):
        """
        Stoppe le thread de polling IS_MOVING.
        """
        self._is_moving_polling = False

    def wait_move_manager(self, axis, target, tol=2, timeout=120):
        """
        Attend que la position de l'axe atteigne la consigne (tolérance) et que l'axe ne soit plus en mouvement.
        Utilise le buffer pour la position, et is_moving pour l'état.
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

    # === METHODES DE SCAN 2D ===

    def inject_scan_batch(self, batch_commands):
        """
        Injecte un batch de commandes (scan) dans la file normale :
        - Purge la file normale
        - Définit l'état global en mode SCANNING
        - Accepte une liste de points (x, y) ou de lignes (x, y_start, y_end)
        - Si lignes, transforme en points (x, y_start) puis (x, y_end)
        """
        # Purge la file normale
        while not self.queue_normale.empty():
            try:
                self.queue_normale.get_nowait()
                self.queue_normale.task_done()
            except Exception:
                break
        # Détection du format et conversion si besoin
        parcours = []
        if batch_commands and len(batch_commands[0]) == 3:
            self.logMessage.emit("[inject_scan_batch] Format lignes détecté, conversion en points...")
            for x, y1, y2 in batch_commands:
                parcours.append((x, y1))
                parcours.append((x, y2))
        else:
            self.logMessage.emit("[inject_scan_batch] Format points détecté.")
            parcours = list(batch_commands)
        # Crée le scan manager
        self._scan_manager = _Scan2DManager(parcours)
        # Active le mode SCANNING
        self.acquisition_status = _AcquisitionStatus.SCANNING
        self.logMessage.emit(f"Batch de scan injecté ({len(parcours)} points)")
    # === SCAN 2D ===
    @staticmethod
    def generate_scan2d(x_min, x_max, y_min, y_max, N, mode='E'):
        """
        Génère la liste des lignes de scan 2D (x, y_start, y_end) selon les paramètres.
        - x_min, x_max, y_min, y_max : bornes du scan (en incréments)
        - N : nombre de lignes (positions X)
        - mode : 'E' (unidirectionnel) ou 'S' (aller-retour)
        Retourne une liste de tuples (x, y_start, y_end)
        """
        x_min = int(x_min)
        x_max = int(x_max)
        y_min = int(y_min)
        y_max = int(y_max)
        N = int(N)
        mode = mode.upper()
        if N == 1:
            x_list = [x_min]
        else:
            x_list = [int(round(x_min + i*(x_max-x_min)/(N-1))) for i in range(N)]
        lines = []
        for i, x in enumerate(x_list):
            if mode == 'E':
                lines.append((x, y_min, y_max))
            elif mode == 'S':
                if i % 2 == 0:
                    lines.append((x, y_min, y_max))
                else:
                    lines.append((x, y_max, y_min))
            else:
                raise ValueError("Mode inconnu : 'E' ou 'S' attendu")
        return lines



# ========================
# API PUBLIQUES MODULES EXTERNES - PASS-THROUGH
# ========================

    # === API GEOMETRICAL PARAMETERS CONVERSION ===
    def get_bench_limits_cm(self):
        return get_bench_limits_cm()

    def clamp_rect_cm(self, x_min, x_max, y_min, y_max):
        return clamp_rect_cm(x_min, x_max, y_min, y_max)

    def inc_to_cm(self, inc):
        return inc_to_cm(inc)

    def cm_to_inc(self, cm):
        return cm_to_inc(cm)

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

    # === API CONTROLLER (ORDRE STRICT DU CONTRÔLEUR, AVEC DOCSTRINGS) ===

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
        cmd = _StageCommand(_StageCommandType.GET_AXIS_HOMED_STATUS, args=[axis], callback=callback)
        self.add_command(cmd)

    def get_all_homed_status(self, callback):
        """
        Retourne l'état du homing pour tous les axes (asynchrone, résultat via callback).
        :param callback: fonction appelée avec le résultat (liste [X, Y, Z, U] True/False)
        Exemple d'utilisation :
            def on_result(result):
                print('All homed:', result)
            manager.get_all_homed_status(callback=on_result)
        """
        cmd = _StageCommand(_StageCommandType.GET_ALL_HOMED_STATUS, callback=callback)
        self.add_command(cmd)

    def home_lock(self, axis, callback):
        """
        Homing de l'axe (bloquant, asynchrone, résultat via callback).
        :param axis: Axe à hommer
        :param callback: fonction appelée avec le résultat (True/False ou None)
        """
        cmd = _StageCommand(_StageCommandType.HOME_LOCK, args=[axis], callback=callback)
        self.add_command(cmd)

    def home(self, axis):
        """
        Homing de l'axe (non bloquant) : lance le homing sans attendre la fin du mouvement.
        À utiliser avec une gestion asynchrone de l'attente (ex : worker/manager).
        """
        cmd = _StageCommand(_StageCommandType.HOME, args=[axis])
        self.add_command(cmd)

    def home_both_lock(self, callback):
        """
        Homing simultané des axes X et Y (bloquant, asynchrone, résultat via callback).
        :param callback: fonction appelée avec le résultat (True/False ou None)
        """
        cmd = _StageCommand(_StageCommandType.HOME_BOTH_LOCK, callback=callback)
        self.add_command(cmd)

    def home_both(self):
        """
        Homing simultané des axes X et Y (non bloquant) : lance le homing sans attendre la fin des mouvements.
        À utiliser avec une gestion asynchrone de l'attente (ex : worker/manager).
        """
        cmd = _StageCommand(_StageCommandType.HOME_BOTH)
        self.add_command(cmd)

    def set_axis_homed(self, axis, value=True, callback=None):
        """
        Définit l'état de homing logiciel pour un axe (asynchrone, résultat via callback).
        :param axis: Axe à modifier
        :param value: True/False
        :param callback: fonction appelée avec le résultat
        """
        cmd = _StageCommand(_StageCommandType.SET_AXIS_HOMED, args=[axis], kwargs={'value': value}, callback=callback)
        self.add_command(cmd)

    def reset_homing_status(self, axis=None, callback=None):
        """
        Remet à zéro l'état du homing (asynchrone, résultat via callback).
        :param axis: Axe spécifique ou None
        :param callback: fonction appelée avec le résultat
        """
        cmd = _StageCommand(_StageCommandType.RESET_HOMING_STATUS, args=[axis] if axis is not None else [], callback=callback)
        self.add_command(cmd)

    # --- CONFIGURATION DES PARAMÈTRES (VITESSE/ACCÉLÉRATION) ---
    def get_axis_params(self, axis, callback):
        """
        Récupère les paramètres actuels d'un axe (asynchrone, résultat via callback).
        :param axis: Axe à interroger ('x' ou 'y')
        :param callback: fonction appelée avec le résultat
        """
        cmd = _StageCommand(_StageCommandType.GET_AXIS_PARAMS, args=[axis], callback=callback)
        self.add_command(cmd)

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
        cmd = _StageCommand(_StageCommandType.SET_AXIS_PARAMS, args=[axis], kwargs={'ls': ls, 'hs': hs, 'acc': acc, 'dec': dec})
        self.add_command(cmd)

    def apply_axis_params(self, axis, params, callback=None):
        """
        Applique les paramètres de vitesse pour un axe spécifique (asynchrone, résultat via callback).
        :param axis: Axe à configurer ('x' ou 'y')
        :param params: Dictionnaire avec les paramètres à appliquer (ls, hs, acc, dec)
        :param callback: fonction appelée avec le résultat
        """
        cmd = _StageCommand(_StageCommandType.APPLY_AXIS_PARAMS, args=[axis, params], callback=callback)
        self.add_command(cmd)

    # --- MOUVEMENT ET CONTRÔLE ---
    def move_to(self, axis, target):
        """
        Déplacement absolu de l'axe à la position cible (argument harmonisé : target).
        Protection par vérification du homing + butées hardware.
        :param axis: Axe à déplacer ('x' ou 'y')
        :param target: Position cible
        """
        cmd = _StageCommand(_StageCommandType.MOVE_TO, args=[axis, target])
        self.add_command(cmd)

    def is_moving(self, axis="all", callback=None):
        """
        Vérifie si un ou plusieurs axes sont en mouvement (asynchrone).
        :param axis: Axe à vérifier ('x', 'y', 'z', 'u' ou 'all')
        :param callback: fonction appelée avec le résultat (True/False)
        """
        cmd = _StageCommand(_StageCommandType.IS_MOVING, args=[axis], callback=callback)
        self.add_command(cmd)

    def wait_move(self, axis, timeout=None, callback=None):
        """
        Attend la fin du mouvement sur l'axe spécifié (asynchrone, résultat via callback).
        :param axis: 'x' ou 'y' (obligatoire)
        :param timeout: en secondes (recommandé)
        :param callback: fonction appelée avec le résultat
        """
        cmd = _StageCommand(_StageCommandType.WAIT_MOVE, args=[axis], kwargs={'timeout': timeout}, callback=callback)
        self.add_command(cmd)

    def stop(self, axis, immediate=False):
        """
        Arrêt du mouvement de l'axe.
        :param axis: Axe à arrêter ('x' ou 'y')
        :param immediate: Si True, arrêt immédiat (ABORT), sinon arrêt progressif (STOP)
        """
        cmd = _StageCommand(_StageCommandType.STOP, args=[axis], kwargs={'immediate': immediate})
        self.add_command(cmd)

    def enable(self, x_on, y_on):
        """
        Active/désactive les sorties X et Y.
        Utilise la méthode pylablib native enable_axis().
        :param x_on: True pour activer X
        :param y_on: True pour activer Y
        """
        cmd = _StageCommand(_StageCommandType.ENABLE, args=[x_on, y_on])
        self.add_command(cmd)

    # --- VITESSE ---
    def get_current_axis_speed(self, axis="all", callback=None):
        """
        Obtient la vitesse instantanée d'un axe (asynchrone, résultat via callback).
        :param axis: Axe à interroger ('x', 'y', 'z', 'u' ou 'all')
        :param callback: fonction appelée avec le résultat
        """
        cmd = _StageCommand(_StageCommandType.GET_CURRENT_AXIS_SPEED, args=[axis], callback=callback)
        self.add_command(cmd)

    def get_global_speed(self, callback=None):
        """
        Obtient la vitesse globale (asynchrone, résultat via callback).
        :param callback: fonction appelée avec le résultat
        """
        cmd = _StageCommand(_StageCommandType.GET_GLOBAL_SPEED, callback=callback)
        self.add_command(cmd)

    def get_axis_speed(self, axis="all", callback=None):
        """
        Obtient la vitesse configurée pour un axe (asynchrone, résultat via callback).
        :param axis: Axe à interroger ('x', 'y', 'z', 'u' ou 'all')
        :param callback: fonction appelée avec le résultat
        """
        cmd = _StageCommand(_StageCommandType.GET_AXIS_SPEED, args=[axis], callback=callback)
        self.add_command(cmd)

    def set_global_speed(self, speed):
        """
        Configure la vitesse globale (méthode PyLab)
        """
        cmd = _StageCommand(_StageCommandType.SET_GLOBAL_SPEED, args=[speed])
        self.add_command(cmd)

    def set_axis_speed(self, axis, speed):
        """
        Configure la vitesse pour un axe spécifique (méthode PyLab).
        :param axis: Axe à configurer ('x' ou 'y')
        :param speed: Vitesse en Hz (0 = utilise vitesse globale)
        """
        cmd = _StageCommand(_StageCommandType.SET_AXIS_SPEED, args=[axis, speed])
        self.add_command(cmd)

    def set_position_reference(self, axis, value=0):
        """
        Fixe la référence de position pour un axe (argument harmonisé : value).
        """
        cmd = _StageCommand(_StageCommandType.SET_POSITION_REFERENCE, args=[axis, value])
        self.add_command(cmd)

    # --- LECTURE D'ÉTAT ET POSITION ---
    def get_position(self, axis, callback):
        """
        Retourne la position de l'axe (asynchrone, résultat via callback).
        :param axis: Axe à interroger ('x' ou 'y')
        :param callback: fonction appelée avec le résultat
        """
        cmd = _StageCommand(_StageCommandType.GET_POSITION, args=[axis], callback=callback)
        self.add_command(cmd)

    def get_status(self, axis, callback):
        """
        Retourne le statut complet de l'axe (asynchrone, résultat via callback).
        :param axis: Axe à interroger ('x' ou 'y')
        :param callback: fonction appelée avec le résultat
        """
        cmd = _StageCommand(_StageCommandType.GET_STATUS, args=[axis], callback=callback)
        self.add_command(cmd)

    # --- FERMETURE ---

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
        cmd = _StageCommand(_StageCommandType.CLOSE, callback=callback)
        self.add_command(cmd)

# ========================
#  METHODES INTERNES
# ========================

    # === WORKER (NOUVEAU) ===
    def _worker_loop(self):
        """
        Boucle worker complète :
        - Traite la file prioritaire (Stop)
        - Sépare explicitement la logique RUNNING/SCANNING
        - Lecture de position continue dans tous les cas
        - En mode SCANNING, gestion non bloquante du scan via _Scan2DManager
        - En mode RUNNING, traitement classique des commandes
        """
        import queue, time
        self._scan_manager = None
        while self._worker_running:
            try:
                # 1. Traiter la file prioritaire (Stop)
                try:
                    cmd = self.queue_prioritaire.get_nowait()
                    if getattr(cmd, 'cmd_type', None) == _StageCommandType.STOP:
                        try:
                            self.controller.stop(*cmd.args, **cmd.kwargs)
                            self.logMessage.emit(f"[STOP] Arrêt demandé (args={cmd.args}, kwargs={cmd.kwargs})")
                        except Exception as e:
                            self.error_occurred.emit(f"Erreur lors du STOP: {e}")
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
                        self.error_occurred.emit("ERREUR LOGIQUE: SCANNING sans _scan_manager initialisé")
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
                        self.error_occurred.emit(f"Erreur lecture continue position: {e}")
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
                        self._execute_worker_command(cmd)
                        self.queue_normale.task_done()
                    except queue.Empty:
                        pass
                    # Lecture continue de position
                    try:
                        x = self.controller.get_position('x')
                        y = self.controller.get_position('y')
                        self.position_buffer.append_sample(PositionSample(x=x, y=y))
                        self.position_changed.emit(x, y)
                    except Exception as e:
                        self.error_occurred.emit(f"Erreur lecture continue position: {e}")
                    time.sleep(0.01)
                    continue

            except Exception as e:
                self.error_occurred.emit(f"Erreur worker: {e}")
                time.sleep(0.1)

    # ========================
    #  METHODES INTERNES
    # ========================

    def _execute_worker_command(self, cmd):
        """
        Exécute une commande classique du worker (hors STOP, batch/scan).
        La commande doit être de type StageCommand.
        """
        if getattr(cmd, 'cmd_type', None) == _StageCommandType.GET_AXIS_HOMED_STATUS:
            axis = cmd.args[0]
            try:
                result = self.controller.get_axis_homed_status(axis)
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[GET_AXIS_HOMED_STATUS] {axis} -> {result}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur GET_AXIS_HOMED_STATUS: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.GET_ALL_HOMED_STATUS:
            try:
                result = self.controller.get_all_homed_status()
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[GET_ALL_HOMED_STATUS] -> {result}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur GET_ALL_HOMED_STATUS: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.HOME_LOCK:
            axis = cmd.args[0]
            try:
                result = self.controller.home_lock(axis)
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[HOME_LOCK] {axis} -> {result}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur HOME_LOCK: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.HOME_BOTH_LOCK:
            try:
                result = self.controller.home_both_lock()
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[HOME_BOTH_LOCK] -> {result}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur HOME_BOTH_LOCK: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.SET_AXIS_HOMED:
            axis = cmd.args[0]
            value = cmd.kwargs.get('value', True)
            try:
                result = self.controller.set_axis_homed(axis, value)
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[SET_AXIS_HOMED] {axis} = {value} -> {result}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur SET_AXIS_HOMED: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.RESET_HOMING_STATUS:
            axis = cmd.args[0] if cmd.args else None
            try:
                result = self.controller.reset_homing_status(axis)
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[RESET_HOMING_STATUS] {axis} -> {result}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur RESET_HOMING_STATUS: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.GET_AXIS_PARAMS:
            axis = cmd.args[0]
            try:
                result = self.controller.get_axis_params(axis)
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[GET_AXIS_PARAMS] {axis} -> {result}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur GET_AXIS_PARAMS: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.GET_CURRENT_AXIS_SPEED:
            axis = cmd.args[0]
            try:
                result = self.controller.get_current_axis_speed(axis)
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[GET_CURRENT_AXIS_SPEED] {axis} -> {result}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur GET_CURRENT_AXIS_SPEED: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.GET_GLOBAL_SPEED:
            try:
                result = self.controller.get_global_speed()
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[GET_GLOBAL_SPEED] -> {result}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur GET_GLOBAL_SPEED: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.GET_AXIS_SPEED:
            axis = cmd.args[0]
            try:
                result = self.controller.get_axis_speed(axis)
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[GET_AXIS_SPEED] {axis} -> {result}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur GET_AXIS_SPEED: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.WAIT_MOVE:
            axis = cmd.args[0]
            timeout = cmd.kwargs.get('timeout', None)
            try:
                result = self.controller.wait_move(axis, timeout)
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[WAIT_MOVE] {axis} -> {result}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur WAIT_MOVE: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.GET_POSITION:
            axis = cmd.args[0]
            try:
                result = self.controller.get_position(axis)
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[GET_POSITION] {axis} -> {result}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur GET_POSITION: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.GET_STATUS:
            axis = cmd.args[0]
            try:
                result = self.controller.get_status(axis)
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[GET_STATUS] {axis} -> {result}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur GET_STATUS: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.CLOSE:
            try:
                result = self.controller.close()
                if cmd.callback:
                    cmd.callback(result)
                self.logMessage.emit(f"[CLOSE] -> {result}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur CLOSE: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.MOVE_TO:
            axis, target = cmd.args
            try:
                self.controller.move_to(axis, target)
                self.logMessage.emit(f"[MOVE_TO] {axis} -> {target}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur MOVE_TO: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.HOME:
            axis = cmd.args[0]
            try:
                self.controller.home(axis)
                self.logMessage.emit(f"[HOME] Homing axe {axis}")
                # Attendre la fin du mouvement
                t0 = time.time()
                while self.controller.is_moving(axis) and (time.time() - t0 < 20):
                    time.sleep(0.05)
                self.status_changed.emit('ready')
            except Exception as e:
                self.error_occurred.emit(f"Erreur HOME: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.HOME_BOTH:
            try:
                self.controller.home_both()
                self.logMessage.emit("[HOME_BOTH] Homing X et Y")
                t0 = time.time()
                while (self.controller.is_moving('x') or self.controller.is_moving('y')) and (time.time() - t0 < 20):
                    time.sleep(0.05)
                self.status_changed.emit('ready')
            except Exception as e:
                self.error_occurred.emit(f"Erreur HOME_BOTH: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.SET_AXIS_PARAMS:
            try:
                self.controller.set_axis_params(*cmd.args, **cmd.kwargs)
                self.logMessage.emit(f"[SET_AXIS_PARAMS] args={cmd.args}, kwargs={cmd.kwargs}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur SET_AXIS_PARAMS: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.APPLY_AXIS_PARAMS:
            try:
                self.controller.apply_axis_params(*cmd.args, **cmd.kwargs)
                self.logMessage.emit(f"[APPLY_AXIS_PARAMS] args={cmd.args}, kwargs={cmd.kwargs}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur APPLY_AXIS_PARAMS: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.SET_AXIS_SPEED:
            try:
                self.controller.set_axis_speed(*cmd.args, **cmd.kwargs)
                self.logMessage.emit(f"[SET_AXIS_SPEED] args={cmd.args}, kwargs={cmd.kwargs}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur SET_AXIS_SPEED: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.SET_GLOBAL_SPEED:
            try:
                self.controller.set_global_speed(*cmd.args, **cmd.kwargs)
                self.logMessage.emit(f"[SET_GLOBAL_SPEED] args={cmd.args}, kwargs={cmd.kwargs}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur SET_GLOBAL_SPEED: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.ENABLE:
            try:
                self.controller.enable(*cmd.args, **cmd.kwargs)
                self.logMessage.emit(f"[ENABLE] args={cmd.args}, kwargs={cmd.kwargs}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur ENABLE: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.SET_POSITION_REFERENCE:
            try:
                self.controller.set_position_reference(*cmd.args, **cmd.kwargs)
                self.logMessage.emit(f"[SET_POSITION_REFERENCE] args={cmd.args}, kwargs={cmd.kwargs}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur SET_POSITION_REFERENCE: {e}")
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.SCAN_2D:
            # déjà géré dans la partie SCANNING
            pass
        elif getattr(cmd, 'cmd_type', None) == _StageCommandType.IS_MOVING:
            axis = cmd.args[0]
            try:
                moving = self.controller.is_moving(axis)
                if cmd.callback:
                    cmd.callback(moving)
                self.logMessage.emit(f"[IS_MOVING] {axis} -> {moving}")
            except Exception as e:
                self.error_occurred.emit(f"Erreur IS_MOVING: {e}")
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

class _StageCommandType(Enum):
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

class _StageCommand:
    def __init__(self, cmd_type, args=None, kwargs=None, callback=None):
        self.cmd_type = cmd_type
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}
        self.callback = callback  # Pour retour asynchrone si besoin

class _Scan2DManager:
    def __init__(self, parcours, tol=2, timeout=120):
        """
        parcours : liste ordonnée de consignes (x, y)
        tol : tolérance sur la position (même unité que x, y)
        timeout : temps max par consigne (secondes)
        """
        self.parcours = list(parcours)
        self.tol = tol
        self.timeout = timeout
        self.current_idx = -1
        self.current_target = None
        self.is_moving = False
        self.move_start_time = None
        self.finished = False

    def start_next_move(self, controller):
        """Lance la consigne suivante si disponible, sinon marque le scan comme terminé."""
        self.current_idx += 1
        if self.current_idx < len(self.parcours):
            self.current_target = self.parcours[self.current_idx]
            x, y = self.current_target
            controller.move_to('x', x)
            controller.move_to('y', y)
            self.is_moving = True
            self.move_start_time = time.time()
        else:
            self.current_target = None
            self.is_moving = False
            self.finished = True

    def check_progress(self, position, controller):
        """
        À appeler à chaque lecture de position.
        Si dans la tolérance, vérifie le hardware. Si le mouvement est fini, prépare la consigne suivante.
        """
        if not self.is_moving or self.current_target is None or self.finished:
            return
        x, y = position
        tx, ty = self.current_target
        # Vérifie la tolérance
        if abs(x - tx) <= self.tol and abs(y - ty) <= self.tol:
            # Vérifie le hardware uniquement si dans la tolérance
            if not controller.is_moving('x') and not controller.is_moving('y'):
                self.is_moving = False
        # Timeout de sécurité
        if self.move_start_time and (time.time() - self.move_start_time > self.timeout):
            self.is_moving = False
            print(f"[Scan2DManager] Timeout sur la consigne {self.current_idx}")

    def step(self, position, controller):
        """
        À appeler à chaque itération du worker.
        - Si aucun mouvement en cours, lance la prochaine consigne.
        - Sinon, vérifie la progression.
        """
        if self.finished:
            return
        if not self.is_moving:
            self.start_next_move(controller)
        else:
            self.check_progress(position, controller)

    def get_current_elementary_move(self):
        """Retourne la consigne en cours, ou None si fini."""
        if 0 <= self.current_idx < len(self.parcours):
            return self.parcours[self.current_idx]
        return None

    def is_elementary_move_in_progress(self):
        """Retourne True si un parcours élémentaire est en cours."""
        return self.is_moving

    def is_finished(self):
        """Retourne True si le scan est terminé."""
        return self.finished 
