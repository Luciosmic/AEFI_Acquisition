"""
Module de contrôle pour Arcus Performax 4EX.
Facilement intégrable à d'autres modules (ex : acquisition DDS).
Utilise les méthodes pylablib natives pour plus de robustesse.
"""

import os
from pylablib.devices import Arcus
import pylablib as pll
import time

class ArcusPerformax4EXStageController:
    """Contrôleur spécialisé pour banc d'imagerie en champ electrique avec Arcus Performax 4EX"""
    
    # Chemin DLL par défaut (relatif au script)
    DEFAULT_DLL_PATH = os.path.join(os.path.dirname(__file__), "DLL64")
    # Paramètres de vitesse par défaut
    DEFAULT_PARAMS = {
        "X": {"ls": 10, "hs": 800, "acc": 300, "dec": 300},
        "Y": {"ls": 10, "hs": 800, "acc": 300, "dec": 300}
    }
    
    # ============================================================================
    # INITIALISATION ET FERMETURE
    # ============================================================================
    
    def __init__(self, dll_path=None, params=None):
        """
        Initialise la connexion au contrôleur Arcus Performax 4EX.
        :param dll_path: Chemin vers le dossier contenant les DLLs Arcus.
        """
        # Utilise le chemin par défaut si non fourni
        if dll_path is None:
            dll_path = self.DEFAULT_DLL_PATH
        self.dll_path = dll_path

        # Vérifie l'existence du dossier DLL
        if not os.path.isdir(self.dll_path):
            raise FileNotFoundError(f"Le dossier DLL spécifié n'existe pas : {self.dll_path}")

        # Utilise les paramètres par défaut si non fournis
        if params is None:
            params = self.DEFAULT_PARAMS
        self.params = params

        pll.par["devices/dlls/arcus_performax"] = self.dll_path
        self.stage = Arcus.Performax4EXStage()
        self.axis_mapping = {"x": 0, "y": 1, "z": 2, "u": 3}

        # Initialisation de l'état du homing selon le statut matériel réel
        self.is_homed = [False, False, False, False]
        for axis, idx in self.axis_mapping.items():
            status_list = self.stage.get_status(axis)
            if 'sw_minus_lim' in status_list:
                self.is_homed[idx] = True
                print(f"[INIT] Axe {axis.upper()} détecté en butée d'origine (sw_minus_lim) → homed=True")
            else:
                print(f"[INIT] Axe {axis.upper()} PAS en butée d'origine → homed=False")
        print(f"État initial du homing: [X, Y, Z, U] = {self.is_homed}")
        
        # Activer les axes X et Y par défaut
        self.enable(True, True)
        
        # Appliquer les paramètres par défaut pour chaque axe
        print("Initialisation des paramètres des axes...")
        for axis in ["x", "y"]:
            self.apply_axis_params(axis, self.params[axis.upper()])


    # ============================================================================
    # API PUBLIQUE DU MODULE
    # ============================================================================


    # === HOMING === 
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
        if axis not in ["x", "y"]:
            raise ValueError("L'axe doit être 'x' ou 'y'")
        enabled_axes = self.stage.is_enabled()
        axis_idx = 0 if axis == "x" else 1
        if not enabled_axes[axis_idx]:
            self.stage.enable_axis(axis)
        print(f"Lancement du homing {axis.upper()} (direction -)...")
        self.stage.home(axis, direction="-", home_mode="only_home_input")
        print(f"Attente de la fin du homing {axis.upper()}...")
        self.stage.wait_move(axis, timeout=120)
        self.stage.set_position_reference(axis, 0)
        self.is_homed[self.axis_mapping[axis]] = True
        print(f"Homing de {axis.upper()} terminé. Position de référence mise à 0.")
        print(f"État du homing: [X, Y, Z, U] = {self.is_homed}")
        print(f"Position actuelle: {self.stage.get_position()}")

    def home(self, axis):
        """
        Homing de l'axe (non bloquant) : lance le homing sans attendre la fin du mouvement.
        À utiliser avec une gestion asynchrone de l'attente (ex : worker/manager).
        """
        if axis not in ["x", "y"]:
            raise ValueError("L'axe doit être 'x' ou 'y'")
        enabled_axes = self.stage.is_enabled()
        axis_idx = 0 if axis == "x" else 1
        if not enabled_axes[axis_idx]:
            self.stage.enable_axis(axis)
        print(f"Lancement du homing {axis.upper()} (direction -) [non bloquant]...")
        self.stage.home(axis, direction="-", home_mode="only_home_input")
        # Pas de wait_move ici
        # La gestion de l'attente doit être faite côté manager

    def home_both_lock(self):
        """
        Homing simultané des axes X et Y (bloquant) : lance le homing et attend la fin des deux mouvements (wait_move).
        À utiliser pour des scripts/processus séquentiels où le blocage est acceptable.
        """
        enabled_axes = self.stage.is_enabled()
        if not enabled_axes[0]:
            self.stage.enable_axis('x')
        if not enabled_axes[1]:
            self.stage.enable_axis('y')
        print("Lancement du homing X et Y (simultané)...")
        self.stage.home('x', direction='-', home_mode='only_home_input')
        self.stage.home('y', direction='-', home_mode='only_home_input')
        print("Attente de la fin du homing X et Y...")
        self.stage.wait_move('x', timeout=120)
        self.stage.wait_move('y', timeout=120)
        self.stage.set_position_reference('x', 0)
        self.stage.set_position_reference('y', 0)
        self.is_homed[self.axis_mapping['x']] = True
        self.is_homed[self.axis_mapping['y']] = True
        print("Homing X et Y terminé. Références mises à 0.")
        print(f"État du homing: [X, Y, Z, U] = {self.is_homed}")
        print(f"Position actuelle: {self.stage.get_position()}")

    def home_both(self):
        """
        Homing simultané des axes X et Y (non bloquant) : lance le homing sans attendre la fin des mouvements.
        À utiliser avec une gestion asynchrone de l'attente (ex : worker/manager).
        """
        enabled_axes = self.stage.is_enabled()
        if not enabled_axes[0]:
            self.stage.enable_axis('x')
        if not enabled_axes[1]:
            self.stage.enable_axis('y')
        print("Lancement du homing X et Y (simultané) [non bloquant]...")
        self.stage.home('x', direction='-', home_mode='only_home_input')
        self.stage.home('y', direction='-', home_mode='only_home_input')
        # Pas de wait_move ici
        # La gestion de l'attente doit être faite côté manager

    def set_axis_homed(self, axis, value=True):
        self.is_homed[self.axis_mapping[axis]] = value

    def reset_homing_status(self, axis=None):
        """
        Remet à zéro l'état du homing.
        :param axis: Axe spécifique à remettre à zéro ('x', 'y', 'z', 'u'), ou None pour tous les axes
        """
        if axis is None:
            self.is_homed = [False, False, False, False]
            print("État du homing remis à zéro pour tous les axes: [X, Y, Z, U] =", self.is_homed)
        elif axis in self.axis_mapping:
            self.is_homed[self.axis_mapping[axis]] = False
            print(f"État du homing remis à zéro pour l'axe {axis.upper()}")
            print(f"État actuel: [X, Y, Z, U] = {self.is_homed}")
        else:
            raise ValueError("L'axe doit être 'x', 'y', 'z', 'u' ou None")
    
    # === CONFIGURATION DES PARAMÈTRES (VITESSE/ACCÉLÉRATION) ===
    
    def get_axis_params(self, axis):
        """
        Récupère les paramètres actuels d'un axe.
        :param axis: Axe à interroger ('x' ou 'y')
        """
        if axis not in ["x", "y"]:
            raise ValueError("L'axe doit être 'x' ou 'y'")
            
        axis_letter = axis.upper()  # 'X' ou 'Y'
        
        ls = self.stage.query(f"LS{axis_letter}")
        hs = self.stage.query(f"HS{axis_letter}")
        acc = self.stage.query(f"ACC{axis_letter}")
        dec = self.stage.query(f"DEC{axis_letter}")
        
        return {"ls": int(ls), "hs": int(hs), "acc": int(acc), "dec": int(dec)}
        
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
        if axis not in ["x", "y"]:
            raise ValueError("L'axe doit être 'x' ou 'y'")
            
        axis_letter = axis.upper()  # 'X' ou 'Y'
        
        # Récupérer les paramètres actuels
        current_params = self.get_axis_params(axis)
        
        # Mettre à jour les paramètres spécifiés
        if ls is not None:
            current_params["ls"] = ls
        if hs is not None:
            current_params["hs"] = hs
        if acc is not None:
            current_params["acc"] = acc
        if dec is not None:
            current_params["dec"] = dec
            
        # Appliquer les paramètres un par un avec vérification
        if ls is not None:
            self.stage.query(f"LS{axis_letter}={current_params['ls']}")
            time.sleep(0.1)  # Petit délai entre chaque commande
        if hs is not None:
            self.stage.query(f"HS{axis_letter}={current_params['hs']}")
            time.sleep(0.1)
        if acc is not None:
            self.stage.query(f"ACC{axis_letter}={current_params['acc']}")
            time.sleep(0.1)
        if dec is not None:
            self.stage.query(f"DEC{axis_letter}={current_params['dec']}")
            time.sleep(0.1)
        
        # Vérifier les paramètres appliqués
        applied_params = self.get_axis_params(axis)
        print(f"Paramètres mis à jour pour l'axe {axis.upper()}:")
        print(f"  LS{axis_letter}={applied_params['ls']}")
        print(f"  HS{axis_letter}={applied_params['hs']}")
        print(f"  ACC{axis_letter}={applied_params['acc']}")
        print(f"  DEC{axis_letter}={applied_params['dec']}")
        
        return applied_params

    def apply_axis_params(self, axis, params):
        """
        Applique les paramètres de vitesse pour un axe spécifique.
        :param axis: Axe à configurer ('x' ou 'y')
        :param params: Dictionnaire avec les paramètres à appliquer (ls, hs, acc, dec)
        :return: Les paramètres effectivement appliqués
        """
        if axis not in ["x", "y"]:
            raise ValueError("L'axe doit être 'x' ou 'y'")
            
        # Utiliser les méthodes pylablib pour configurer la vitesse
        # Pour l'instant on garde les commandes query car set_axis_speed() avait des problèmes
        axis_letter = axis.upper()  # 'X' ou 'Y'
        
        # Application des paramètres via query (car les méthodes pylablib pour les accélérations ne sont pas implémentées)
        self.stage.query(f"LS{axis_letter}={params['ls']}")
        self.stage.query(f"HS{axis_letter}={params['hs']}")
        self.stage.query(f"ACC{axis_letter}={params['acc']}")
        self.stage.query(f"DEC{axis_letter}={params['dec']}")
        
        # Vérification des paramètres appliqués
        ls = self.stage.query(f"LS{axis_letter}")
        hs = self.stage.query(f"HS{axis_letter}")
        acc = self.stage.query(f"ACC{axis_letter}")
        dec = self.stage.query(f"DEC{axis_letter}")
        
        return {"ls": int(ls), "hs": int(hs), "acc": int(acc), "dec": int(dec)}
        
    # ============================================================================
    # MOUVEMENT ET CONTRÔLE
    # ============================================================================
    
    def move_to(self, axis, pos):
        """
        Déplacement absolu de l'axe à la position pos.
        Protection par vérification du homing + butées hardware.
        :param axis: Axe à déplacer ('x' ou 'y')
        :param pos: Position cible
        """
        if axis not in ["x", "y"]:
            raise ValueError("L'axe doit être 'x' ou 'y'")
        
        # Vérifier homing obligatoire
        if not self.is_homed[self.axis_mapping[axis]]:
            raise Exception(f"Homing requis pour l'axe {axis.upper()}. Utilisez home('{axis}') d'abord.")
        
        # Déplacement protégé par les butées hardware
        print(f"Déplacement axe {axis.upper()} vers position {pos}")
        self.stage.move_to(axis, pos)

    def is_moving(self, axis="all"):
        """
        Vérifie si un ou plusieurs axes sont en mouvement (méthode PyLab).
        :param axis: Axe à vérifier ('x', 'y', 'z', 'u' ou 'all')
        :return: Boolean ou liste de booleans
        """
        if axis == "all":
            return self.stage.is_moving()
        else:
            axis_lower = axis.lower()
            if axis_lower not in self.axis_mapping:
                raise ValueError("L'axe doit être 'x', 'y', 'z', 'u' ou 'all'")
            
            moving_status = self.stage.is_moving()
            axis_index = self.axis_mapping[axis_lower]
            return moving_status[axis_index]

    def wait_move(self, axis, timeout=None):
        """
        Attend la fin du mouvement sur l'axe spécifié.
        
        USAGE :
        - Obligatoire après home() et move_to()
        - Toujours spécifier un timeout
        
        EXEMPLES :
        wait_move('x', timeout=30)  # Pour homing
        wait_move('y', timeout=15)  # Pour mouvement normal
        
        IMPORTANT :
        - Crucial pour la synchronisation avec l'acquisition
        - Permet de détecter précisément début/fin des mouvements
        
        :param axis: 'x' ou 'y' (obligatoire)
        :param timeout: en secondes (recommandé)
        :raises ValueError: Si axis invalide
        :raises TimeoutError: Si timeout atteint
        """
        if axis not in ["x", "y"]:
            raise ValueError("L'axe doit être 'x' ou 'y'")
        self.stage.wait_move(axis, timeout=timeout)

    def stop(self, axis, immediate=False):
        """
        Arrêt du mouvement de l'axe.
        :param axis: Axe à arrêter ('x' ou 'y')
        :param immediate: Si True, arrêt immédiat (ABORT), sinon arrêt progressif (STOP)
        """
        if axis not in ["x", "y"]:
            raise ValueError("L'axe doit être 'x' ou 'y'")
            
        # Utiliser la commande ASCII appropriée selon le type d'arrêt
        comm = "ABORT" if immediate else "STOP"
        self.stage.query(f"{comm}{axis.upper()}")
        
    def enable(self, x_on, y_on):
        """
        Active/désactive les sorties X et Y.
        Utilise la méthode pylablib native enable_axis().
        :param x_on: True pour activer X
        :param y_on: True pour activer Y
        """
        # Utiliser les méthodes pylablib natives
        if x_on:
            self.stage.enable_axis("x")
        if y_on:
            self.stage.enable_axis("y")
        
        # Note: pylablib n'a pas de méthode disable_axis() documentée


    # === VITESSE ===
    def get_current_axis_speed(self, axis="all"):
        """
        Obtient la vitesse instantanée d'un axe (méthode PyLab).
        :param axis: Axe à interroger ('x', 'y', 'z', 'u' ou 'all')
        :return: Vitesse actuelle en steps/sec (Hz)
        """
        if axis == "all":
            # Pour tous les axes, retourne une liste [X, Y, Z, U]
            speeds_str = self.stage.query("PS")
            speeds = [int(x) for x in speeds_str.split(":") if x]
            return speeds
        else:
            # Pour un axe spécifique, utilise l'index dans le résultat global
            axis_lower = axis.lower()
            if axis_lower not in self.axis_mapping:
                raise ValueError("L'axe doit être 'x', 'y', 'z', 'u' ou 'all'")
            
            speeds_str = self.stage.query("PS")
            speeds = [int(x) for x in speeds_str.split(":") if x]
            axis_index = self.axis_mapping[axis_lower]
            return speeds[axis_index]
    
    def get_global_speed(self):
        """Obtient la vitesse globale (méthode PyLab)"""
        return int(self.stage.query("HS"))
    
    def get_axis_speed(self, axis="all"):
        """
        Obtient la vitesse configurée pour un axe (méthode PyLab).
        :param axis: Axe à interroger ('x', 'y', 'z', 'u' ou 'all')
        :return: Vitesse configurée en Hz (0 = utilise vitesse globale)
        """
        if axis == "all":
            # Retourner la vitesse pour tous les axes utilisés (X et Y)
            return {
                "x": int(self.stage.query("HSX")),
                "y": int(self.stage.query("HSY"))
            }
        else:
            axis_lower = axis.lower()
            if axis_lower not in ["x", "y"]:  # Limité aux axes utilisés
                raise ValueError("L'axe doit être 'x', 'y' ou 'all'")
            
            axis_letter = axis_lower.upper()
            return int(self.stage.query(f"HS{axis_letter}"))
    
    def set_global_speed(self, speed):
        """Configure la vitesse globale (méthode PyLab)"""
        self.stage.query(f"HS={speed}")
        return self.get_global_speed()
    
    def set_axis_speed(self, axis, speed):
        """
        Configure la vitesse pour un axe spécifique (méthode PyLab).
        :param axis: Axe à configurer ('x' ou 'y')
        :param speed: Vitesse en Hz (0 = utilise vitesse globale)
        """
        if axis.lower() not in ["x", "y"]:
            raise ValueError("L'axe doit être 'x' ou 'y'")
        
        axis_letter = axis.upper()
        self.stage.query(f"HS{axis_letter}={speed}")
        return self.get_axis_speed(axis)
    
    def set_position_reference(self, axis, position=0):
        """Fixe la référence de position pour un axe (pass-through vers self.stage)."""
        return self.stage.set_position_reference(axis, position)


    # === LECTURE D'ÉTAT ET POSITION ===
    def get_position(self, axis):
        """
        Retourne la position de l'axe.
        Utilise la méthode pylablib native get_position().
        :param axis: Axe à interroger ('x' ou 'y')
        """
        if axis not in ["x", "y"]:
            raise ValueError("L'axe doit être 'x' ou 'y'")
            
        # Utiliser la méthode pylablib native
        return self.stage.get_position(axis)
        
    def get_status(self, axis):
        """
        Retourne le statut complet de l'axe.
        Utilise la méthode pylablib native get_status().
        :param axis: Axe à interroger ('x' ou 'y')
        """
        if axis not in ["x", "y"]:
            raise ValueError("L'axe doit être 'x' ou 'y'")
            
        # Utiliser la méthode pylablib native
        return self.stage.get_status(axis)
    
    def is_opened(self):
        """
        Vérifie si la connexion au contrôleur matériel est active.
        Retourne True si la connexion est ouverte, False sinon.
        """
        # On suppose que self.stage possède un attribut ou une méthode is_open
        # (adapter selon l'API réelle de Arcus.Performax4EXStage)
        try:
            return self.stage.is_opened()
        except Exception:
            return False

    # === FERMETURE ===
    def close(self):
        """Ferme la connexion au contrôleur."""
        self.stage.close()
    
