"""
Service spécialisé pour la gestion du homing des axes du banc.
Extrait du ArcusPerformax4EXStageController pour respecter le principe SOLID.
"""

class HomingService:
    """
    Service dédié à la gestion du homing des axes.
    Responsabilités:
    - Suivi de l'état de homing de chaque axe
    - Exécution des opérations de homing
    - Validation des conditions de homing
    """
    
    def __init__(self, stage_hardware):
        """
        Initialise le service de homing.
        :param stage_hardware: Référence au contrôleur matériel bas-niveau (pylablib)
        """
        self.stage_hardware = stage_hardware
        self.axis_mapping = {"x": 0, "y": 1, "z": 2, "u": 3}
        
        # Initialisation de l'état du homing selon le statut matériel réel
        self.is_homed = [False, False, False, False]
        self._initialize_homing_status()
        
    def _initialize_homing_status(self):
        """Initialise l'état du homing en vérifiant les butées matérielles."""
        for axis, idx in self.axis_mapping.items():
            if axis in ["x", "y"]:  # Limité aux axes utilisés
                status_list = self.stage_hardware.get_status(axis)
                if 'sw_minus_lim' in status_list:
                    self.is_homed[idx] = True
        print(f"[HomingService] État initial du homing: [X, Y, Z, U] = {self.is_homed}")
    
    def validate_axis(self, axis):
        """Valide que l'axe est supporté."""
        if axis not in ["x", "y"]:
            raise ValueError("L'axe doit être 'x' ou 'y'")
        return True
        
    def get_axis_homed_status(self, axis):
        """
        Vérifie si un axe spécifique a été homé.
        :param axis: Axe à vérifier ('x', 'y', 'z', 'u')
        :return: True si l'axe a été homé, False sinon
        """
        if axis not in self.axis_mapping:
            raise ValueError("L'axe doit être 'x', 'y', 'z' ou 'u'")
        return self.is_homed[self.axis_mapping[axis]]
    
    def get_all_homed_status(self):
        """
        Retourne l'état du homing pour tous les axes.
        :return: Liste [X, Y, Z, U] avec True/False pour chaque axe
        """
        return self.is_homed.copy()

    def home_lock(self, axis):
        """
        Homing de l'axe (bloquant) : lance le homing et attend la fin du mouvement (wait_move).
        À utiliser pour des scripts/processus séquentiels où le blocage est acceptable.
        """
        self.validate_axis(axis)
        
        # Vérifier et activer l'axe si nécessaire
        enabled_axes = self.stage_hardware.is_enabled()
        axis_idx = 0 if axis == "x" else 1
        if not enabled_axes[axis_idx]:
            self.stage_hardware.enable_axis(axis)
            
        print(f"[HomingService] Lancement du homing {axis.upper()} (direction -)...")
        self.stage_hardware.home(axis, direction="-", home_mode="only_home_input")
        print(f"[HomingService] Attente de la fin du homing {axis.upper()}...")
        self.stage_hardware.wait_move(axis, timeout=120)
        self.stage_hardware.set_position_reference(axis, 0)
        self.is_homed[self.axis_mapping[axis]] = True
        print(f"[HomingService] Homing de {axis.upper()} terminé. Position de référence mise à 0.")
        print(f"[HomingService] État du homing: [X, Y, Z, U] = {self.is_homed}")
        print(f"[HomingService] Position actuelle: {self.stage_hardware.get_position()}")

    def home(self, axis):
        """
        Homing de l'axe (non bloquant) : lance le homing sans attendre la fin du mouvement.
        À utiliser avec une gestion asynchrone de l'attente (ex : worker/manager).
        """
        self.validate_axis(axis)
        
        # Vérifier et activer l'axe si nécessaire
        enabled_axes = self.stage_hardware.is_enabled()
        axis_idx = 0 if axis == "x" else 1
        if not enabled_axes[axis_idx]:
            self.stage_hardware.enable_axis(axis)
            
        print(f"[HomingService] Lancement du homing {axis.upper()} (direction -) [non bloquant]...")
        self.stage_hardware.home(axis, direction="-", home_mode="only_home_input")
        # Pas de wait_move ici
        # La gestion de l'attente doit être faite côté manager

    def home_both_lock(self):
        """
        Homing simultané des axes X et Y (bloquant) : lance le homing et attend la fin des deux mouvements (wait_move).
        À utiliser pour des scripts/processus séquentiels où le blocage est acceptable.
        """
        # Vérifier et activer les axes si nécessaire
        enabled_axes = self.stage_hardware.is_enabled()
        if not enabled_axes[0]:
            self.stage_hardware.enable_axis('x')
        if not enabled_axes[1]:
            self.stage_hardware.enable_axis('y')
            
        print("[HomingService] Lancement du homing X et Y (simultané)...")
        self.stage_hardware.home('x', direction='-', home_mode='only_home_input')
        self.stage_hardware.home('y', direction='-', home_mode='only_home_input')
        print("[HomingService] Attente de la fin du homing X et Y...")
        self.stage_hardware.wait_move('x', timeout=120)
        self.stage_hardware.wait_move('y', timeout=120)
        self.stage_hardware.set_position_reference('x', 0)
        self.stage_hardware.set_position_reference('y', 0)
        self.is_homed[self.axis_mapping['x']] = True
        self.is_homed[self.axis_mapping['y']] = True
        print("[HomingService] Homing X et Y terminé. Références mises à 0.")
        print(f"[HomingService] État du homing: [X, Y, Z, U] = {self.is_homed}")
        print(f"[HomingService] Position actuelle: {self.stage_hardware.get_position()}")

    def home_both(self):
        """
        Homing simultané des axes X et Y (non bloquant) : lance le homing sans attendre la fin des mouvements.
        À utiliser avec une gestion asynchrone de l'attente (ex : worker/manager).
        """
        # Vérifier et activer les axes si nécessaire
        enabled_axes = self.stage_hardware.is_enabled()
        if not enabled_axes[0]:
            self.stage_hardware.enable_axis('x')
        if not enabled_axes[1]:
            self.stage_hardware.enable_axis('y')
            
        print("[HomingService] Lancement du homing X et Y (simultané) [non bloquant]...")
        self.stage_hardware.home('x', direction='-', home_mode='only_home_input')
        self.stage_hardware.home('y', direction='-', home_mode='only_home_input')
        # Pas de wait_move ici
        # La gestion de l'attente doit être faite côté manager

    def set_axis_homed(self, axis, value=True):
        """
        Définit manuellement l'état de homing d'un axe.
        :param axis: Axe à modifier ('x', 'y', 'z', 'u')
        :param value: True si homé, False sinon
        """
        if axis not in self.axis_mapping:
            raise ValueError("L'axe doit être 'x', 'y', 'z' ou 'u'")
        self.is_homed[self.axis_mapping[axis]] = value

    def reset_homing_status(self, axis=None):
        """
        Remet à zéro l'état du homing.
        :param axis: Axe spécifique à remettre à zéro ('x', 'y', 'z', 'u'), ou None pour tous les axes
        """
        if axis is None:
            self.is_homed = [False, False, False, False]
            print("[HomingService] État du homing remis à zéro pour tous les axes: [X, Y, Z, U] =", self.is_homed)
        elif axis in self.axis_mapping:
            self.is_homed[self.axis_mapping[axis]] = False
            print(f"[HomingService] État du homing remis à zéro pour l'axe {axis.upper()}")
            print(f"[HomingService] État actuel: [X, Y, Z, U] = {self.is_homed}")
        else:
            raise ValueError("L'axe doit être 'x', 'y', 'z', 'u' ou None")




