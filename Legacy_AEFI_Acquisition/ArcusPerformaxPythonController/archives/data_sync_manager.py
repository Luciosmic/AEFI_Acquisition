"""
Gestionnaire de synchronisation des flux de données pour banc d'imagerie EF.
Synchronise l'acquisition de données avec l'état des moteurs Arcus Performax 4EX.

Architecture:
- Flux 1: Données de mesure (acquisition continue)
- Flux 2: État moteur (position + statut mouvement)
- Synchronisation: Calage temporel basé sur état moteur (sans encodeur)
"""

import time
import threading
from queue import Queue, Empty
from dataclasses import dataclass
from typing import Optional, Callable, List, Dict, Any
from ArcusPerformaxPythonController.controller.ArcusPerformax4EXStage_Controller import EFImagingStageController


@dataclass
class MotorState:
    """État instantané du moteur pour synchronisation"""
    axis: str
    position: float
    is_moving: bool
    status: Any
    timestamp: float
    is_homed: bool


@dataclass
class SyncEvent:
    """Événement de synchronisation"""
    event_type: str  # 'move_start', 'move_end', 'position_update'
    motor_state: MotorState
    trigger_timestamp: float


class DataSyncManager:
    """Gestionnaire principal de synchronisation des flux de données"""
    
    def __init__(self, motor_controller: EFImagingStageController):
        """
        Initialise le gestionnaire de synchronisation.
        
        :param motor_controller: Instance du contrôleur moteur
        """
        self.controller = motor_controller
        
        # Files de données pour synchronisation
        self.motor_data_queue = Queue()
        self.sync_events_queue = Queue()
        
        # État de monitoring
        self.is_monitoring = False
        self.monitor_thread = None
        
        # Callbacks utilisateur
        self.callbacks = {
            'move_start': [],
            'move_end': [],
            'position_update': [],
            'data_sync': []
        }
        
        # Configuration de polling
        self.poll_rate = 0.01  # 100Hz par défaut
        self.last_motor_states = {}
    
    def is_moving(self, axis: str) -> bool:
        """
        Vérifie si l'axe est en mouvement.
        
        :param axis: Axe à vérifier ('x' ou 'y')
        :return: True si en mouvement, False si arrêté
        """
        try:
            # Méthode pylablib pour vérifier le mouvement
            return self.controller.stage.is_moving(axis)
        except:
            # Fallback : interroger directement le statut
            status = self.controller.get_status(axis)
            return "moving" in str(status).lower() or "busy" in str(status).lower()
    
    def get_motor_state(self, axis: str) -> MotorState:
        """
        Capture l'état complet du moteur à un instant donné.
        
        :param axis: Axe à interroger ('x' ou 'y')
        :return: État complet du moteur
        """
        return MotorState(
            axis=axis.upper(),
            position=self.controller.get_position(axis),
            is_moving=self.is_moving(axis),
            status=self.controller.get_status(axis),
            timestamp=time.time(),
            is_homed=self.controller.is_axis_homed(axis)
        )
    
    def add_callback(self, event_type: str, callback: Callable):
        """
        Ajoute un callback pour un type d'événement.
        
        :param event_type: Type d'événement ('move_start', 'move_end', 'position_update', 'data_sync')
        :param callback: Fonction callback à appeler
        """
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
        else:
            raise ValueError(f"Type d'événement inconnu: {event_type}")
    
    def remove_callback(self, event_type: str, callback: Callable):
        """Retire un callback."""
        if event_type in self.callbacks and callback in self.callbacks[event_type]:
            self.callbacks[event_type].remove(callback)
    
    def _trigger_callbacks(self, event_type: str, *args, **kwargs):
        """Déclenche tous les callbacks d'un type d'événement."""
        for callback in self.callbacks[event_type]:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"Erreur dans callback {event_type}: {e}")
    
    def _monitor_loop(self, axes: List[str]):
        """Boucle principale de monitoring (thread séparé)."""
        print(f"Démarrage monitoring axes {axes} à {1/self.poll_rate:.0f}Hz")
        
        while self.is_monitoring:
            try:
                for axis in axes:
                    # Capturer état actuel
                    current_state = self.get_motor_state(axis)
                    
                    # Détecter changements d'état
                    if axis in self.last_motor_states:
                        last_state = self.last_motor_states[axis]
                        
                        # Détection début de mouvement
                        if not last_state.is_moving and current_state.is_moving:
                            event = SyncEvent('move_start', current_state, time.time())
                            self.sync_events_queue.put(event)
                            self._trigger_callbacks('move_start', current_state)
                        
                        # Détection fin de mouvement
                        elif last_state.is_moving and not current_state.is_moving:
                            event = SyncEvent('move_end', current_state, time.time())
                            self.sync_events_queue.put(event)
                            self._trigger_callbacks('move_end', current_state)
                        
                        # Mise à jour position (si en mouvement)
                        elif current_state.is_moving:
                            event = SyncEvent('position_update', current_state, time.time())
                            self._trigger_callbacks('position_update', current_state)
                    
                    # Stocker état pour prochaine itération
                    self.last_motor_states[axis] = current_state
                    self.motor_data_queue.put(current_state)
                
                # Callback général de synchronisation
                self._trigger_callbacks('data_sync', time.time())
                
                time.sleep(self.poll_rate)
                
            except Exception as e:
                print(f"Erreur dans monitoring: {e}")
                time.sleep(self.poll_rate)
    
    def start_monitoring(self, axes: List[str], poll_rate: float = 0.01):
        """
        Démarre le monitoring continu des axes.
        
        :param axes: Liste des axes à surveiller ['x', 'y']
        :param poll_rate: Fréquence de polling en secondes
        """
        if self.is_monitoring:
            print("Monitoring déjà actif")
            return
        
        self.poll_rate = poll_rate
        self.is_monitoring = True
        
        # Démarrer thread de monitoring
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(axes,), 
            daemon=True
        )
        self.monitor_thread.start()
        
        print(f"Monitoring démarré pour axes {axes}")
    
    def stop_monitoring(self):
        """Arrête le monitoring."""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        print("Monitoring arrêté")
    
    def wait_move_start(self, axis: str, timeout: float = 5.0) -> bool:
        """
        Attend que l'axe commence à bouger (pour synchroniser début d'acquisition).
        
        :param axis: Axe à surveiller ('x' ou 'y')
        :param timeout: Timeout en secondes
        :return: True si mouvement détecté, False si timeout
        """
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            if self.is_moving(axis):
                return True
            time.sleep(0.001)  # Polling très rapide pour déclenchement précis
        
        return False
    
    def wait_move_completion(self, axis: str, timeout: float = 30.0) -> bool:
        """
        Attend la fin du mouvement.
        
        :param axis: Axe à surveiller ('x' ou 'y')
        :param timeout: Timeout en secondes
        :return: True si mouvement terminé, False si timeout
        """
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            if not self.is_moving(axis):
                # Double vérification après petit délai
                time.sleep(self.poll_rate * 5)
                if not self.is_moving(axis):
                    return True
            time.sleep(self.poll_rate)
        
        return False
    
    def get_sync_events(self, max_events: int = 100) -> List[SyncEvent]:
        """
        Récupère les événements de synchronisation en attente.
        
        :param max_events: Nombre maximum d'événements à récupérer
        :return: Liste des événements
        """
        events = []
        for _ in range(max_events):
            try:
                event = self.sync_events_queue.get_nowait()
                events.append(event)
            except Empty:
                break
        return events
    
    def get_motor_data(self, max_records: int = 100) -> List[MotorState]:
        """
        Récupère les données moteur en attente.
        
        :param max_records: Nombre maximum d'enregistrements
        :return: Liste des états moteur
        """
        data = []
        for _ in range(max_records):
            try:
                state = self.motor_data_queue.get_nowait()
                data.append(state)
            except Empty:
                break
        return data
    
    def clear_queues(self):
        """Vide toutes les files de données."""
        while not self.motor_data_queue.empty():
            try:
                self.motor_data_queue.get_nowait()
            except Empty:
                break
        
        while not self.sync_events_queue.empty():
            try:
                self.sync_events_queue.get_nowait()
            except Empty:
                break


class ScanSyncManager(DataSyncManager):
    """Gestionnaire spécialisé pour scans 2D avec synchronisation ligne par ligne"""
    
    def __init__(self, motor_controller: EFImagingStageController):
        super().__init__(motor_controller)
        self.scan_data = []
        self.current_line = 0
    
    def setup_line_scan(self, axis: str, start_pos: float, end_pos: float, 
                       scan_speed: float, line_callback: Optional[Callable] = None):
        """
        Configure un scan ligne avec synchronisation automatique.
        
        :param axis: Axe de scan ('x' ou 'y')
        :param start_pos: Position de début
        :param end_pos: Position de fin
        :param scan_speed: Vitesse de scan
        :param line_callback: Callback appelé à chaque ligne
        """
        # Configurer vitesse constante pour synchronisation
        self.controller.set_axis_params(axis, hs=scan_speed, ls=scan_speed)
        
        def on_line_start(motor_state):
            print(f"=== DÉBUT LIGNE {self.current_line} - Position: {motor_state.position} ===")
            if line_callback:
                line_callback('start', self.current_line, motor_state)
        
        def on_line_end(motor_state):
            print(f"=== FIN LIGNE {self.current_line} - Position: {motor_state.position} ===")
            if line_callback:
                line_callback('end', self.current_line, motor_state)
            self.current_line += 1
        
        # Enregistrer callbacks
        self.add_callback('move_start', on_line_start)
        self.add_callback('move_end', on_line_end)
    
    def execute_line_scan(self, axis: str, target_pos: float, timeout: float = 30.0) -> bool:
        """
        Exécute un scan de ligne avec synchronisation automatique.
        
        :param axis: Axe de scan
        :param target_pos: Position cible
        :param timeout: Timeout pour le mouvement
        :return: True si succès, False si échec
        """
        # Lancer mouvement
        self.controller.move_to(axis, target_pos)
        
        # Attendre début mouvement pour déclenchement acquisition
        if not self.wait_move_start(axis, timeout=2.0):
            print("ERREUR: Mouvement non détecté")
            return False
        
        # Attendre fin mouvement
        if not self.wait_move_completion(axis, timeout=timeout):
            print("ERREUR: Timeout mouvement")
            return False
        
        return True


# ============================================================================
# EXEMPLE D'UTILISATION
# ============================================================================

def exemple_synchronisation():
    """Exemple d'utilisation du gestionnaire de synchronisation"""
    
    # Initialiser contrôleur
    dll_path = "C:/Users/manip/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/Dev/ArcusPerformaxPythonController/DLL64"
    controller = EFImagingStageController(dll_path)
    
    # Initialiser gestionnaire de synchronisation
    sync_manager = DataSyncManager(controller)
    
    # Callbacks pour événements
    def on_move_start(motor_state):
        print(f"🟢 DÉBUT ACQUISITION - Axe {motor_state.axis} - Position: {motor_state.position}")
        # DÉMARRER VOTRE ACQUISITION ICI
    
    def on_move_end(motor_state):
        print(f"🔴 FIN ACQUISITION - Axe {motor_state.axis} - Position: {motor_state.position}")
        # ARRÊTER VOTRE ACQUISITION ICI
    
    def on_position_update(motor_state):
        # Synchronisation en temps réel pendant mouvement
        print(f"📍 Position: {motor_state.position} - Temps: {motor_state.timestamp:.3f}")
    
    # Enregistrer callbacks
    sync_manager.add_callback('move_start', on_move_start)
    sync_manager.add_callback('move_end', on_move_end)
    sync_manager.add_callback('position_update', on_position_update)
    
    try:
        # Homing obligatoire
        controller.home('x')
        
        # Démarrer monitoring en arrière-plan
        sync_manager.start_monitoring(['x'], poll_rate=0.01)  # 100Hz
        
        # Exemple de mouvement avec synchronisation automatique
        print("Lancement mouvement avec synchronisation...")
        controller.move_to('x', 5000)
        
        # Attendre fin du mouvement
        sync_manager.wait_move_completion('x')
        
        # Récupérer données collectées
        events = sync_manager.get_sync_events()
        motor_data = sync_manager.get_motor_data()
        
        print(f"Événements collectés: {len(events)}")
        print(f"Points de données moteur: {len(motor_data)}")
        
    finally:
        sync_manager.stop_monitoring()
        controller.close()


if __name__ == "__main__":
    exemple_synchronisation() 