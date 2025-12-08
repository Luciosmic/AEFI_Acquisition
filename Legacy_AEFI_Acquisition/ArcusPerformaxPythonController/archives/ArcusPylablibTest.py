# 2025-05-15 Luis Saluden

# -*- coding: utf-8 -*-

import pylablib as pll
import time

# Précise le chemin vers le dossier contenant les DLLs
pll.par["devices/dlls/arcus_performax"] = r"C:/Users/manip/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/Dev/ArcusPerformaxPythonController/DLL64"

from pylablib.devices import Arcus

# Paramètres de vitesse par défaut
DEFAULT_PARAMS = {
    "global": {"ls": 10, "hs": 800, "acc": 300, "dec": 300},
    "X": {"ls": 10, "hs": 800, "acc": 300, "dec": 300},
    "Y": {"ls": 10, "hs": 800, "acc": 300, "dec": 300}
}

# Fonction pour appliquer les paramètres globaux de vitesse
def apply_global_params(stage, use_globals=True):
    """
    Applique les paramètres de vitesse au contrôleur.
    Si use_globals=True, utilise les commandes globales (LS, HS, etc.)
    Sinon, utilise les commandes par axe (LS1, LS2, etc.)
    """
    if use_globals:
        # Utiliser les paramètres globaux pour tous les axes
        params = DEFAULT_PARAMS["global"]
        stage.query(f"LS={params['ls']}")
        stage.query(f"HS={params['hs']}")
        stage.query(f"ACC={params['acc']}")
        stage.query(f"DEC={params['dec']}")
        print(f"Paramètres globaux appliqués: LS={params['ls']}, HS={params['hs']}, ACC={params['acc']}, DEC={params['dec']}")

def apply_axis_params(stage, axis, params):
    """
    Applique les paramètres de vitesse pour un axe spécifique.
    :param stage: Objet stage
    :param axis: Axe à configurer ('x' ou 'y')
    :param params: Dictionnaire avec les paramètres à appliquer (ls, hs, acc, dec)
    """
    axis_num = "1" if axis == "x" else "2"
    stage.query(f"LS{axis_num}={params['ls']}")
    stage.query(f"HS{axis_num}={params['hs']}")
    stage.query(f"ACC{axis_num}={params['acc']}")
    stage.query(f"DEC{axis_num}={params['dec']}")
    print(f"Paramètres appliqués pour l'axe {axis.upper()}: LS={params['ls']}, HS={params['hs']}, ACC={params['acc']}, DEC={params['dec']}")

print(Arcus.list_usb_performax_devices())

#stage = Performax4EXStage()  # USB, premier contrôleur trouvé
stage = Arcus.Performax4EXStage()

# (Optionnel) Active les sorties des axes X et Y
stage.query("EO=3")
#stage.enable_output("x", True)  # Active l'axe X
#stage.enable_output("y", True)  # Active l'axe Y

# Affichage des paramètres initiaux
print("\nParamètres initiaux :")
ls = stage.query("LS")
hs = stage.query("HS")
acc = stage.query("ACC")
dec = stage.query("DEC")
print(f"Paramètres globaux: Low Speed = {ls}, High Speed = {hs}, Acceleration = {acc}, Deceleration = {dec}")

# Affichage des paramètres par axe 
for axis in ["X", "Y"]:
    axis_num = "1" if axis == "X" else "2"
    ls_axis = stage.query(f"LS{axis_num}")
    hs_axis = stage.query(f"HS{axis_num}")
    acc_axis = stage.query(f"ACC{axis_num}")
    dec_axis = stage.query(f"DEC{axis_num}")
    print(f"Axe {axis}: Low Speed = {ls_axis}, High Speed = {hs_axis}, Acceleration = {acc_axis}, Deceleration = {dec_axis}")

# Application des paramètres globaux au démarrage
print("\nApplication des paramètres globaux :")
apply_global_params(stage, use_globals=True)

# Menu des commandes disponibles
print("\nContrôle interactif des axes X et Y. Commandes disponibles :")
print("  move <axe> <pos>   : déplacement absolu de l'axe (x ou y) à la position <pos>")
print("  get <axe>          : lire la position actuelle de l'axe (x ou y)")
print("  speed <ls> <hs> <acc> <dec> : définir vitesse basse, haute, accélération et décélération (global)")
print("  speed_axis <axe> <ls> <hs> <acc> <dec> : définir ces paramètres pour un axe spécifique")
print("  reset              : réinitialise les paramètres globaux")
print("  home <axe>         : homing de l'axe (x ou y) en direction -")
print("  stop <axe>         : arrêt du mouvement de l'axe")
print("  status <axe>       : affiche le statut complet de l'axe")
print("  query <cmd>        : envoie une commande ASCII manuelle (ex: query EO, query MST)")
print("  py <python>        : exécute une commande Python")
print("  quit               : quitter le programme\n")

while True:
    cmd = input("Commande > ").strip()
    
    if cmd.startswith("move "):
        try:
            parts = cmd.split()
            axis = parts[1].lower()
            pos = int(parts[2])
            if axis not in ["x", "y"]:
                print("Axe invalide. Utilisez 'x' ou 'y'.")
                continue
                
            # Appliquer les paramètres spécifiques à l'axe avant le mouvement
            # apply_axis_params(stage, axis, DEFAULT_PARAMS[axis.upper()])
            
            stage.move_to(axis, pos)
            print(f"Déplacement demandé à {axis.upper()} = {pos}")
        except Exception as e:
            print("Erreur de syntaxe ou de valeur :", e)
            
    elif cmd.startswith("get "):
        try:
            axis = cmd.split()[1].lower()
            if axis not in ["x", "y"]:
                print("Axe invalide. Utilisez 'x' ou 'y'.")
                continue
            pos = stage.get_position(axis)
            print(f"Position {axis.upper()} actuelle : {pos}")
        except Exception as e:
            print("Erreur :", e)
            
    elif cmd.startswith("speed ") and not cmd.startswith("speed_axis "):
        try:
            parts = cmd.split()
            ls = int(parts[1])
            hs = int(parts[2])
            acc = int(parts[3])
            dec = int(parts[4]) if len(parts) > 4 else acc  # Si DEC non spécifié, utiliser la même valeur que ACC
            
            # Mettre à jour les paramètres globaux
            DEFAULT_PARAMS["global"]["ls"] = ls
            DEFAULT_PARAMS["global"]["hs"] = hs
            DEFAULT_PARAMS["global"]["acc"] = acc
            DEFAULT_PARAMS["global"]["dec"] = dec
            
            # Appliquer les nouveaux paramètres globaux
            apply_global_params(stage, use_globals=True)
            
        except Exception as e:
            print("Erreur de syntaxe ou de valeur :", e)
            print("Syntaxe correcte : speed <ls> <hs> <acc> [<dec>]")
            
    elif cmd.startswith("speed_axis "):
        try:
            parts = cmd.split()
            axis = parts[1].lower()
            ls = int(parts[2])
            hs = int(parts[3])
            acc = int(parts[4])
            dec = int(parts[5]) if len(parts) > 5 else acc  # Si DEC non spécifié, utiliser la même valeur que ACC
            
            if axis not in ["x", "y"]:
                print("Axe invalide. Utilisez 'x' ou 'y'.")
                continue
            
            # Mettre à jour les paramètres spécifiques à l'axe
            ax_upper = axis.upper()
            DEFAULT_PARAMS[ax_upper]["ls"] = ls
            DEFAULT_PARAMS[ax_upper]["hs"] = hs
            DEFAULT_PARAMS[ax_upper]["acc"] = acc
            DEFAULT_PARAMS[ax_upper]["dec"] = dec
            
            # Appliquer les nouveaux paramètres pour cet axe
            apply_axis_params(stage, axis, DEFAULT_PARAMS[ax_upper])
            
        except Exception as e:
            print("Erreur de syntaxe ou de valeur :", e)
            print("Syntaxe correcte : speed_axis <axe> <ls> <hs> <acc> [<dec>]")
            
    elif cmd == "reset":
        try:
            apply_global_params(stage, use_globals=True)
            print("Paramètres globaux réinitialisés")
        except Exception as e:
            print("Erreur :", e)
            
    elif cmd.startswith("home "):
        try:
            axis = cmd.split()[1].lower()
            if axis not in ["x", "y"]:
                print("Axe invalide. Utilisez 'x' ou 'y'.")
                continue
                
            # S'assurer que les paramètres globaux sont appliqués avant le homing
            apply_global_params(stage, use_globals=True)
            
            print(f"Lancement du homing {axis.upper()} (direction -)...")
            stage.home(axis, direction="-", home_mode="only_home_input")
            print(f"Homing de {axis.upper()} terminé.")
        except Exception as e:
            print("Erreur :", e)
            
    elif cmd.startswith("stop "):
        try:
            axis = cmd.split()[1].lower()
            if axis not in ["x", "y"]:
                print("Axe invalide. Utilisez 'x' ou 'y'.")
                continue
            stage.stop(axis)
            print(f"Mouvement de {axis.upper()} arrêté.")
        except Exception as e:
            print("Erreur :", e)
            
    elif cmd.startswith("status "):
        try:
            axis = cmd.split()[1].lower()
            if axis not in ["x", "y"]:
                print("Axe invalide. Utilisez 'x' ou 'y'.")
                continue
            status = stage.get_status(axis)
            position = stage.get_position(axis)
            print(f"==== STATUT AXE {axis.upper()} ====")
            print(f"Position : {position}")
            print(f"Status : {status}")
            
            # Récupération des paramètres globaux
            ls = stage.query("LS")
            hs = stage.query("HS")
            acc = stage.query("ACC")
            dec = stage.query("DEC")
            print(f"Paramètres globaux : LS={ls}, HS={hs}, ACC={acc}, DEC={dec}")
            
            # Récupération des paramètres spécifiques à l'axe
            axis_num = "1" if axis == "x" else "2"
            ls_axis = stage.query(f"LS{axis_num}")
            hs_axis = stage.query(f"HS{axis_num}")
            acc_axis = stage.query(f"ACC{axis_num}")
            dec_axis = stage.query(f"DEC{axis_num}")
            print(f"Paramètres axe {axis.upper()} : LS={ls_axis}, HS={hs_axis}, ACC={acc_axis}, DEC={dec_axis}")
        except Exception as e:
            print("Erreur :", e)
            
    elif cmd.startswith("query "):
        try:
            ascii_cmd = cmd[len("query "):].strip()
            response = stage.query(ascii_cmd)
            print(f"Réponse à '{ascii_cmd}' : {response}")
        except Exception as e:
            print("Erreur lors de l'envoi de la commande :", e)
            
    elif cmd.startswith("py "):
        try:
            code = cmd[len("py "):].strip()
            result = eval(code)
            if result is not None:
                print(result)
        except Exception as e:
            try:
                exec(code)
            except Exception as e2:
                print("Erreur lors de l'exécution Python :", e2)
                
    elif cmd == "quit":
        print("Fermeture du contrôleur...")
        break
        
    else:
        print("Commande inconnue. Utilisez : move, get, speed, speed_axis, reset, home, stop, status, query, py, quit.")

stage.close()