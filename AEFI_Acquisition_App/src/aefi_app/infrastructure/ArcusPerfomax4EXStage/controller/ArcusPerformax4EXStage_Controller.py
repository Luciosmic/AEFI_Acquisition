"""
Module de contrôle pour Arcus Performax 4EX.
Facilement intégrable à d'autres modules (ex : acquisition DDS).
Utilise les méthodes pylablib natives pour plus de robustesse.
"""

import os
from pylablib.devices import Arcus
import pylablib as pll
import time

from .HomingService import HomingService

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

        # Création du service de homing
        self.homing_service = HomingService(self.stage)
        
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
        """Délégué à HomingService"""
        return self.homing_service.get_axis_homed_status(axis)
    
    def get_all_homed_status(self):
        """Délégué à HomingService"""
        return self.homing_service.get_all_homed_status()

    def home_lock(self, axis):
        """Délégué à HomingService"""
        return self.homing_service.home_lock(axis)

    def home(self, axis):
        """Délégué à HomingService"""
        return self.homing_service.home(axis)

    def home_both_lock(self):
        """Délégué à HomingService"""
        return self.homing_service.home_both_lock()

    def home_both(self):
        """Délégué à HomingService"""
        return self.homing_service.home_both()

    def set_axis_homed(self, axis, value=True):
        """Délégué à HomingService"""
        return self.homing_service.set_axis_homed(axis, value)

    def reset_homing_status(self, axis=None):
        """Délégué à HomingService"""
        return self.homing_service.reset_homing_status(axis)
    
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
        print(f"[ArcusController]Paramètres mis à jour pour l'axe {axis.upper()}:")
        print(f"[ArcusController]  LS{axis_letter}={applied_params['ls']}")
        print(f"[ArcusController]  HS{axis_letter}={applied_params['hs']}")
        print(f"[ArcusController]  ACC{axis_letter}={applied_params['acc']}")
        print(f"[ArcusController]  DEC{axis_letter}={applied_params['dec']}")
        
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
        if not self.homing_service.get_axis_homed_status(axis):
            raise Exception(f"Homing requis pour l'axe {axis.upper()}. Utilisez home('{axis}') d'abord.")
        
        # Déplacement protégé par les butées hardware
        print(f"[ArcusController]Déplacement axe {axis.upper()} vers position {pos}")
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

    def is_at_target(self, axis, tolerance=5):
        """
        Vérifie si un axe est arrivé à sa position cible (dans la tolérance).
        
        :param axis: 'x' ou 'y'
        :param tolerance: tolérance en incréments (défaut: 5)
        :return: True si l'axe est à la position cible
        """
        axis_lower = axis.lower()
        if axis_lower not in self.axis_mapping:
            raise ValueError("L'axe doit être 'x' ou 'y'")
        
        # Si l'axe est encore en mouvement, il n'est pas arrivé
        if self.is_moving(axis):
            return False
            
        # Vérifier la position actuelle vs la dernière cible
        # La position actuelle n'est pas utilisée pour l'instant, on se fie uniquement à is_moving
        # current_pos = self.get_position(axis)
        
        # Récupérer la dernière position cible depuis le contrôleur interne
        # Pour l'instant on suppose qu'on est arrivé si on n'est plus en mouvement
        # Une amélioration future pourrait stocker la position cible
        return True

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
    
