# 2025-01-15 Luis Saluden - Version 2
# Script de test Arcus Performax utilisant les méthodes pylablib recommandées

# -*- coding: utf-8 -*-

import pylablib as pll
import time

# Configuration du chemin vers les DLLs
pll.par["devices/dlls/arcus_performax"] = r"C:/Users/manip/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/Dev/ArcusPerformaxPythonController/DLL64"

from pylablib.devices import Arcus

# Paramètres de vitesse par défaut
DEFAULT_SPEED_PARAMS = {
    "low_speed": 10,      # LS - Vitesse basse
    "high_speed": 800,    # HS - Vitesse haute  
    "acceleration": 300,  # ACC - Accélération
    "deceleration": 300   # DEC - Décélération
}

class ArcusPerformaxController:
    """
    Classe pour contrôler un stage Arcus Performax 4EX en utilisant les méthodes pylablib.
    """
    
    def __init__(self):
        """Initialise la connexion avec le contrôleur."""
        self.stage = None
        self.axes = ["x", "y"]  # Axes disponibles pour un contrôleur 2-4 axes
        
    def connect(self):
        """Établit la connexion avec le contrôleur."""
        try:
            print("[INFO] Recherche des contrôleurs Arcus Performax...")
            devices = Arcus.list_usb_performax_devices()
            print(f"Appareils trouvés : {devices}")
            
            if not devices:
                raise Exception("Aucun contrôleur Arcus Performax trouvé")
            
            print("[INFO] Connexion au contrôleur...")
            self.stage = Arcus.Performax4EXStage()
            
            # Récupération des axes disponibles
            available_axes = self.stage.get_all_axes()
            print(f"Axes disponibles : {available_axes}")
            
            print("[OK] Connexion établie avec succès")
            return True
            
        except Exception as e:
            print(f"[ERREUR] Erreur de connexion : {e}")
            return False
    
    def enable_motors(self):
        """Active les moteurs sur tous les axes."""
        try:
            print("\n[INFO] Activation des moteurs...")
            
            # Méthode 1: Utiliser la commande ASCII EO pour activer les sorties
            # EO=3 active les axes X et Y (bits 0 et 1)
            #response = self.stage.query("EO=3")
            #print(f"Commande EO=3 envoyée, réponse : {response}")
            
            # Méthode 2: Utiliser enable_axis pour chaque axe (si disponible)
            for axis in self.axes:
                try:
                    self.stage.enable_axis(axis, True)
                    print(f"Axe {axis.upper()} activé via enable_axis()")
                except Exception as e:
                    print(f"enable_axis() non disponible pour {axis}: {e}")
            
            print("[OK] Moteurs activés")
            return True
            
        except Exception as e:
            print(f"[ERREUR] Erreur lors de l'activation des moteurs : {e}")
            return False
    
    def set_speed_parameters(self, **params):
        """
        Configure les paramètres de vitesse globaux.
        
        Args:
            low_speed: Vitesse basse (LS)
            high_speed: Vitesse haute (HS) 
            acceleration: Accélération (ACC)
            deceleration: Décélération (DEC)
        """
        try:
            print("\n[INFO] Configuration des paramètres de vitesse...")
            
            # Utiliser les valeurs fournies ou les valeurs par défaut
            ls = params.get('low_speed', DEFAULT_SPEED_PARAMS['low_speed'])
            hs = params.get('high_speed', DEFAULT_SPEED_PARAMS['high_speed'])
            acc = params.get('acceleration', DEFAULT_SPEED_PARAMS['acceleration'])
            dec = params.get('deceleration', DEFAULT_SPEED_PARAMS['deceleration'])
            
            # Application des paramètres globaux
            self.stage.query(f"LS={ls}")
            self.stage.query(f"HS={hs}")
            self.stage.query(f"ACC={acc}")
            self.stage.query(f"DEC={dec}")
            
            print(f"Paramètres appliqués : LS={ls}, HS={hs}, ACC={acc}, DEC={dec}")
            
            # Vérification des paramètres appliqués
            ls_read = self.stage.query("LS")
            hs_read = self.stage.query("HS")
            acc_read = self.stage.query("ACC")
            dec_read = self.stage.query("DEC")
            
            print(f"Paramètres vérifiés : LS={ls_read}, HS={hs_read}, ACC={acc_read}, DEC={dec_read}")
            print("[OK] Paramètres de vitesse configurés")
            return True
            
        except Exception as e:
            print(f"[ERREUR] Erreur lors de la configuration de vitesse : {e}")
            return False
    
    def home_axes(self):
        """Effectue le homing sur les axes X et Y."""
        try:
            print("\n[INFO] Démarrage du processus de homing...")
            
            for axis in self.axes:
                print(f"\n[INFO] Homing de l'axe {axis.upper()}...")
                
                # Vérifier si l'axe est déjà à l'origine
                try:
                    is_homed = self.stage.is_homed(axis)
                    print(f"Statut homing axe {axis.upper()} : {is_homed}")
                except Exception:
                    print(f"is_homed() non disponible pour l'axe {axis}")
                
                # Effectuer le homing (direction négative par défaut)
                self.stage.home(axis, direction="-", home_mode="only_home_input")
                print(f"Commande de homing envoyée pour l'axe {axis.upper()}")
                
                # Attendre la fin du homing
                print(f"Attente de la fin du homing pour l'axe {axis.upper()}...")
                self.stage.wait_for_home(axis)
                
                # Vérifier la position après homing
                position = self.stage.get_position(axis)
                print(f"[OK] Homing terminé pour l'axe {axis.upper()}, position : {position}")
            
            print("[OK] Homing terminé sur tous les axes")
            return True
            
        except Exception as e:
            print(f"[ERREUR] Erreur lors du homing : {e}")
            return False
    
    def move_axis(self, axis, position, wait=True):
        """
        Déplace un axe vers une position absolue.
        
        Args:
            axis: Axe à déplacer ('x' ou 'y')
            position: Position cible
            wait: Attendre la fin du mouvement
        """
        try:
            if axis not in self.axes:
                raise ValueError(f"Axe invalide : {axis}. Utilisez {self.axes}")
            
            print(f"\n[INFO] Déplacement de l'axe {axis.upper()} vers la position {position}")
            
            # Obtenir la position actuelle
            current_pos = self.stage.get_position(axis)
            print(f"Position actuelle de {axis.upper()} : {current_pos}")
            
            # Effectuer le mouvement
            self.stage.move_to(axis, position)
            print(f"Commande de déplacement envoyée")
            
            if wait:
                print(f"Attente de la fin du mouvement...")
                self.stage.wait_move(axis)
                
                # Vérifier la position finale
                final_pos = self.stage.get_position(axis)
                print(f"[OK] Déplacement terminé, position finale : {final_pos}")
            else:
                print("Mouvement initié (mode asynchrone)")
            
            return True
            
        except Exception as e:
            print(f"[ERREUR] Erreur lors du déplacement : {e}")
            return False
    
    def stop_axis(self, axis):
        """
        Arrête le mouvement d'un axe.
        
        Args:
            axis: Axe à arrêter ('x' ou 'y')
        """
        try:
            if axis not in self.axes:
                raise ValueError(f"Axe invalide : {axis}. Utilisez {self.axes}")
            
            print(f"\n[INFO] Arrêt du mouvement de l'axe {axis.upper()}")
            
            # Vérifier si l'axe est en mouvement
            is_moving = self.stage.is_moving(axis)
            print(f"Axe {axis.upper()} en mouvement : {is_moving}")
            
            if is_moving:
                self.stage.stop(axis)
                print(f"[OK] Commande d'arrêt envoyée pour l'axe {axis.upper()}")
                
                # Attendre un court instant puis vérifier l'arrêt
                time.sleep(0.1)
                is_still_moving = self.stage.is_moving(axis)
                if not is_still_moving:
                    print(f"[OK] Axe {axis.upper()} arrêté")
                else:
                    print(f"[WARN] Axe {axis.upper()} encore en mouvement")
            else:
                print(f"[INFO] Axe {axis.upper()} n'était pas en mouvement")
            
            return True
            
        except Exception as e:
            print(f"[ERREUR] Erreur lors de l'arrêt : {e}")
            return False
    
    def get_status(self, axis):
        """Affiche le statut complet d'un axe."""
        try:
            print(f"\n[STATUS] STATUT DE L'AXE {axis.upper()}")
            print("=" * 30)
            
            # Position
            position = self.stage.get_position(axis)
            print(f"Position : {position}")
            
            # Statut du mouvement
            is_moving = self.stage.is_moving(axis)
            print(f"En mouvement : {is_moving}")
            
            # Statut général
            try:
                status = self.stage.get_status(axis)
                print(f"Statut : {status}")
            except Exception:
                print("Statut détaillé non disponible")
            
            # Vitesse actuelle
            try:
                speed = self.stage.get_current_speed(axis)
                print(f"Vitesse actuelle : {speed}")
            except Exception:
                print("Vitesse actuelle non disponible")
            
            return True
            
        except Exception as e:
            print(f"[ERREUR] Erreur lors de la lecture du statut : {e}")
            return False
    
    def disconnect(self):
        """Ferme la connexion avec le contrôleur."""
        try:
            if self.stage:
                self.stage.close()
                print("[INFO] Connexion fermée")
            return True
        except Exception as e:
            print(f"[ERREUR] Erreur lors de la déconnexion : {e}")
            return False

def run_final_tests():
    """Exécute la séquence de tests finaux demandée."""
    
    controller = ArcusPerformaxController()
    
    try:
        # 1. Connexion
        print("DEMARRAGE DES TESTS FINAUX")
        print("=" * 50)
        if not controller.connect():
            return False
        
        # 2. Activation des moteurs
        print("\n" + "=" * 50)
        print("TEST 1: ACTIVATION DES MOTEURS")
        print("=" * 50)
        if not controller.enable_motors():
            return False
        
        # 3. Configuration des paramètres de vitesse
        print("\n" + "=" * 50)
        print("TEST 2: CONFIGURATION DES PARAMETRES DE VITESSE")
        print("=" * 50)
        if not controller.set_speed_parameters(
            low_speed=20,
            high_speed=1000,
            acceleration=500,
            deceleration=500
        ):
            return False
        
        # 4. Homing sur les axes X et Y
        print("\n" + "=" * 50)
        print("TEST 3: HOMING DES AXES X ET Y")
        print("=" * 50)
        if not controller.home_axes():
            return False
        
        # 5. Déplacement des axes
        print("\n" + "=" * 50)
        print("TEST 4: DEPLACEMENTS")
        print("=" * 50)
        
        # Déplacement de l'axe X
        if not controller.move_axis("x", 5000, wait=True):
            return False
        
        # Déplacement de l'axe Y 
        if not controller.move_axis("y", 3000, wait=True):
            return False
        
        # Déplacement simultané (asynchrone)
        print("\n[INFO] Déplacement simultané des deux axes...")
        controller.move_axis("x", 10000, wait=False)
        controller.move_axis("y", 8000, wait=False)
        
        # Attendre 2 secondes puis effectuer un arrêt
        time.sleep(2.0)
        
        # 6. Test d'arrêt
        print("\n" + "=" * 50)
        print("TEST 5: ARRET DES MOUVEMENTS")
        print("=" * 50)
        
        controller.stop_axis("x")
        controller.stop_axis("y")
        
        # Affichage du statut final
        print("\n" + "=" * 50)
        print("STATUT FINAL")
        print("=" * 50)
        
        controller.get_status("x")
        controller.get_status("y")
        
        print("\n[OK] TOUS LES TESTS TERMINES AVEC SUCCES!")
        return True
        
    except Exception as e:
        print(f"\n[ERREUR] ERREUR CRITIQUE PENDANT LES TESTS : {e}")
        return False
        
    finally:
        # Nettoyage
        controller.disconnect()

def interactive_mode():
    """Mode interactif pour contrôler manuellement le stage."""
    
    controller = ArcusPerformaxController()
    
    if not controller.connect():
        return
    
    print("\n[INFO] MODE INTERACTIF ACTIVE")
    print("Commandes disponibles :")
    print("  enable          : activer les moteurs")
    print("  speed           : configurer la vitesse")
    print("  home            : homing des axes")
    print("  move <axe> <pos>: déplacer un axe")
    print("  stop <axe>      : arrêter un axe") 
    print("  status <axe>    : afficher le statut")
    print("  test            : lancer les tests finaux")
    print("  quit            : quitter")
    
    try:
        while True:
            cmd = input("\n> Commande : ").strip().lower()
            
            if cmd == "quit":
                break
            elif cmd == "enable":
                controller.enable_motors()
            elif cmd == "speed":
                controller.set_speed_parameters()
            elif cmd == "home":
                controller.home_axes()
            elif cmd == "test":
                run_final_tests()
                break
            elif cmd.startswith("move "):
                try:
                    parts = cmd.split()
                    axis = parts[1]
                    position = int(parts[2])
                    controller.move_axis(axis, position)
                except (IndexError, ValueError):
                    print("[ERREUR] Syntaxe: move <axe> <position>")
            elif cmd.startswith("stop "):
                try:
                    axis = cmd.split()[1]
                    controller.stop_axis(axis)
                except IndexError:
                    print("[ERREUR] Syntaxe: stop <axe>")
            elif cmd.startswith("status "):
                try:
                    axis = cmd.split()[1]
                    controller.get_status(axis)
                except IndexError:
                    print("[ERREUR] Syntaxe: status <axe>")
            else:
                print("[ERREUR] Commande inconnue")
                
    finally:
        controller.disconnect()

if __name__ == "__main__":
    print("CONTROLEUR ARCUS PERFORMAX - VERSION 2")
    print("Base sur les methodes pylablib recommandees")
    print("\nChoisissez le mode :")
    print("1. Tests finaux automatiques")
    print("2. Mode interactif")
    
    choice = input("\nVotre choix (1/2) : ").strip()
    
    if choice == "1":
        run_final_tests()
    elif choice == "2":
        interactive_mode()
    else:
        print("[ERREUR] Choix invalide")
