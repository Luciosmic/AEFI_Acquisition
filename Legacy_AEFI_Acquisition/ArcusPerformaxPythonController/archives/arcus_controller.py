"""
Module de contrôle pour Arcus Performax 4EX.
Facilement intégrable à d'autres modules (ex : acquisition DDS).
"""

from pylablib.devices import Arcus
import pylablib as pll
import time

# Paramètres de vitesse par défaut
DEFAULT_PARAMS = {
    "X": {"ls": 10, "hs": 800, "acc": 300, "dec": 300},
    "Y": {"ls": 10, "hs": 800, "acc": 300, "dec": 300}
}

class ArcusController:
    """
    Classe de contrôle pour le moteur Arcus Performax 4EX.
    Fournit les méthodes principales de pilotage et expose l'objet stage pour les besoins avancés.
    """
    def __init__(self, dll_path):
        """
        Initialise la connexion au contrôleur Arcus Performax 4EX.
        :param dll_path: Chemin vers le dossier contenant les DLLs Arcus.
        """
        pll.par["devices/dlls/arcus_performax"] = dll_path
        self.stage = Arcus.Performax4EXStage()
        
        # Activer les axes X et Y par défaut
        self.enable(True, True)
        
        # Appliquer les paramètres par défaut pour chaque axe
        print("Initialisation des paramètres des axes...")
        for axis in ["x", "y"]:
            params = self.apply_axis_params(axis, DEFAULT_PARAMS[axis.upper()])
            print(f"Axe {axis.upper()}: LS={params['ls']}, HS={params['hs']}, ACC={params['acc']}, DEC={params['dec']}")
        
    def apply_axis_params(self, axis, params):
        """
        Applique les paramètres de vitesse pour un axe spécifique.
        :param axis: Axe à configurer ('x' ou 'y')
        :param params: Dictionnaire avec les paramètres à appliquer (ls, hs, acc, dec)
        :return: Les paramètres effectivement appliqués
        """
        if axis not in ["x", "y"]:
            raise ValueError("L'axe doit être 'x' ou 'y'")
            
        axis_letter = axis.upper()  # 'X' ou 'Y'
        
        # Application des paramètres
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
    
    def jog_to(self, axis, pos):
        """
        Déplacement absolu de l'axe à la position pos.
        :param axis: Axe à déplacer ('x' ou 'y')
        :param pos: Position cible
        """
        if axis not in ["x", "y"]:
            raise ValueError("L'axe doit être 'x' ou 'y'")
            
        self.stage.move_to(axis, pos)
        
    def home(self, axis):
        """
        Homing de l'axe (direction négative, home input).
        :param axis: Axe à homer ('x' ou 'y')
        """
        if axis not in ["x", "y"]:
            raise ValueError("L'axe doit être 'x' ou 'y'")
            
        # S'assurer que les axes sont activés (EO=3)
        self.enable(True, True)
        
        # Appliquer les paramètres par défaut pour l'axe
        params = self.apply_axis_params(axis, DEFAULT_PARAMS[axis.upper()])
        print(f"Paramètres appliqués pour l'axe {axis.upper()}: LS={params['ls']}, HS={params['hs']}, ACC={params['acc']}, DEC={params['dec']}")
        
        print(f"Lancement du homing {axis.upper()} (direction -)...")
        self.stage.home(axis, direction="-", home_mode="only_home_input")
        print(f"Homing de {axis.upper()} terminé.")
        
    def stop(self, axis, immediate=False):
        """
        Arrêt du mouvement de l'axe.
        :param axis: Axe à arrêter ('x' ou 'y')
        :param immediate: Si True, arrêt immédiat
        """
        if axis not in ["x", "y"]:
            raise ValueError("L'axe doit être 'x' ou 'y'")
            
        self.stage.stop(axis, immediate=immediate)
        
    def enable(self, x_on, y_on):
        """
        Active/désactive les sorties X et Y.
        :param x_on: True pour activer X
        :param y_on: True pour activer Y
        """
        eo_val = 1 if x_on else 0
        eo_val += 2 if y_on else 0
        self.stage.query(f"EO={eo_val}")
        
    def get_position(self, axis):
        """
        Retourne la position de l'axe.
        :param axis: Axe à interroger ('x' ou 'y')
        """
        if axis not in ["x", "y"]:
            raise ValueError("L'axe doit être 'x' ou 'y'")
            
        return self.stage.get_position(axis)
        
    def get_status(self, axis):
        """
        Retourne le statut complet de l'axe.
        :param axis: Axe à interroger ('x' ou 'y')
        """
        if axis not in ["x", "y"]:
            raise ValueError("L'axe doit être 'x' ou 'y'")
            
        return self.stage.get_status(axis)
        
    def close(self):
        """Ferme la connexion au contrôleur."""
        self.stage.close() 