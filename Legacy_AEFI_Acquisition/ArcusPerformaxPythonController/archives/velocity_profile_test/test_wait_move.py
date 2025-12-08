"""
Script de test simple pour la methode wait_move() - version securisee
"""

import sys
import os
import time

# Import du controleur
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from ArcusPerformaxPythonController.controller.ArcusPerformax4EXStage_Controller import EFImagingStageController

# Parametres
DLL_PATH = r"C:/Users/manip/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/Dev/ArcusPerformaxPythonController/controller/DLL64"

def wait_for_all_axes_stop(stage, timeout=10):
    """Attendre que tous les axes soient arretes"""
    print("Verification que tous les axes sont arretes...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            is_moving = stage.stage.is_moving()
            if all(not moving for moving in is_moving):
                print("Tous les axes sont arretes")
                return True
            print(f"Axes en mouvement: {is_moving}, attente...")
            time.sleep(0.5)
        except Exception as e:
            print(f"Erreur verification mouvement: {e}")
            time.sleep(0.5)
    
    print("Timeout: certains axes bougent encore")
    return False

def safe_home_axis(stage, axis):
    """Homing securise d'un axe"""
    print(f"\n--- Homing securise de l'axe {axis.upper()} ---")
    
    # 1. Attendre que tous les axes soient arretes
    if not wait_for_all_axes_stop(stage, timeout=10):
        print(f"Attention: des axes bougent encore avant homing {axis}")
    
    # 2. Verifier si deja home
    if stage.is_axis_homed(axis):
        print(f"Axe {axis.upper()} deja home, skip")
        return True
    
    # 3. Faire le homing
    try:
        print(f"Lancement du homing {axis.upper()}...")
        stage.home(axis)
        
        # 4. Attendre que le homing soit termine
        print(f"Attente fin homing {axis.upper()}...")
        stage.wait_move(axis, timeout=30)
        
        print(f"Homing {axis.upper()} termine avec succes")
        return True
        
    except Exception as e:
        print(f"Erreur pendant homing {axis}: {e}")
        return False

def safe_move_to(stage, axis, position):
    """Mouvement securise vers une position"""
    print(f"\n--- Mouvement securise {axis.upper()} vers {position} ---")
    
    # 1. Verifier que l'axe est home
    if not stage.is_axis_homed(axis):
        print(f"Erreur: axe {axis.upper()} pas home")
        return False
    
    # 2. Attendre que l'axe soit arrete
    if not wait_for_all_axes_stop(stage, timeout=5):
        print(f"Attention: des axes bougent encore avant mouvement {axis}")
    
    # 3. Position actuelle
    pos_initial = stage.get_position(axis)
    print(f"Position initiale {axis.upper()}: {pos_initial}")
    
    # 4. Faire le mouvement
    try:
        print(f"Lancement mouvement {axis.upper()} vers {position}...")
        stage.move_to(axis, position)
        
        # 5. Attendre que le mouvement soit termine
        print(f"Attente fin mouvement {axis.upper()}...")
        stage.wait_move(axis, timeout=15)
        
        # 6. Position finale
        pos_final = stage.get_position(axis)
        print(f"Position finale {axis.upper()}: {pos_final}")
        print(f"Mouvement {axis.upper()} termine avec succes")
        return True
        
    except Exception as e:
        print(f"Erreur pendant mouvement {axis}: {e}")
        return False

def test_wait_move():
    """Test complet et securise de wait_move"""
    
    print("=== TEST SECURISE DE WAIT_MOVE ===")
    print("Initialisation du controleur...")
    stage = EFImagingStageController(DLL_PATH)
    
    try:
        # Test 1: Verifier les methodes disponibles
        print("\n1. Verification des methodes disponibles...")
        print(f"Methodes wait: {[m for m in dir(stage.stage) if 'wait' in m.lower()]}")
        print(f"Type objet: {type(stage.stage)}")
        
        # Test 2: Etat initial
        print(f"\n2. Etat initial...")
        is_moving = stage.stage.is_moving()
        print(f"is_moving(): {is_moving}")
        
        # Attendre que tout soit arrete au debut
        wait_for_all_axes_stop(stage, timeout=5)
        
        # Test 3: Syntaxes wait_move (tests rapides)
        print(f"\n3. Tests syntaxe wait_move...")
        
        try:
            print("Test wait_move('x', timeout=1)...")
            stage.stage.wait_move('x', timeout=1)
            print("OK: wait_move('x', timeout=1) fonctionne")
        except Exception as e:
            print(f"Erreur wait_move('x', timeout=1): {e}")
        
        # Test 4: Homing securise
        print(f"\n4. Tests homing securise...")
        
        success_x = safe_home_axis(stage, 'x')
        if success_x:
            time.sleep(1)
            
        # Test 5: Mouvement securise
        if success_x:
            print(f"\n5. Test mouvement securise...")
            
            # Petit mouvement
            success_move1 = safe_move_to(stage, 'x', 500)
            time.sleep(1)
            
            # Retour origine
            if success_move1:
                success_move2 = safe_move_to(stage, 'x', 0)
            
        print("\n=== FIN DES TESTS SECURISES ===")
        
    except Exception as e:
        print(f"Erreur generale: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # S'assurer que tout est arrete avant fermeture
        try:
            wait_for_all_axes_stop(stage, timeout=5)
        except:
            pass
        stage.close()
        print("Connexion fermee")

if __name__ == "__main__":
    test_wait_move() 