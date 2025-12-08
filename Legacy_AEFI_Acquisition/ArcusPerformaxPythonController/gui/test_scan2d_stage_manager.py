import sys
import time
import os
from PyQt5.QtCore import QCoreApplication

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ArcusPerformaxPythonController.gui.components.ArcusPerformax4EXStage_StageManager import StageManager



def log(msg):
    print(f"[TEST] {msg}")

def wait_scan_finished(stage_manager, timeout=60):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if stage_manager._scan_manager is None or stage_manager._scan_manager.is_finished():
            return True
        time.sleep(0.1)
    return False

def main():
    stage_manager = StageManager()
    # Connexion des signaux à des logs
    stage_manager.logMessage.connect(lambda msg: log(msg))
    stage_manager.status_changed.connect(lambda status: log(f"Status: {status}"))

    # 1. Homing initial
    log("Démarrage du homing initial...")
    stage_manager.home_both()
    time.sleep(1)  # Adapter selon le matériel
    #input("Appuie sur Entrée pour lancer le scan S...")
    stage_manager.wait_move(axis="all")
    # 2. Scan 2D en mode 'S'
    x_min = y_min = 3000
    x_max = y_max = 6000
    x_nb = 4
    log("Génération du scan 2D en mode S...")
    scan_S = StageManager.generate_scan2d(x_min, x_max, y_min, y_max, x_nb, mode='S')
    log(f"Scan S généré : {scan_S}")
    log("Injection du scan S...")
    stage_manager.inject_scan_batch(scan_S)
    log("Attente de la fin du scan S...")
    wait_scan_finished(stage_manager)
    log("Scan S terminé.")
    input("Appuie sur Entrée pour lancer le homing intermédiaire (lock)...")

    # 3. Homing intermédiaire (lock)
    log("Homing intermédiaire (lock)...")
    import threading
    homing_done_event = threading.Event()
    def on_homing_done(result):
        log("Homing X+Y terminé (lock). Résultat : {}".format(result))
        homing_done_event.set()
    stage_manager.home_both_lock(on_homing_done)
    log("Attente de la fin du homing (lock)...")
    homing_done_event.wait()
    log("Fin du homing intermédiaire (lock).")
    input("Appuie sur Entrée pour lancer le scan E...")

    # 4. Scan 2D en mode 'E'
    log("Génération du scan 2D en mode E...")
    scan_E = StageManager.generate_scan2d(x_min, x_max, y_min, y_max, x_nb, mode='E')
    log(f"Scan E généré : {scan_E}")
    log("Injection du scan E...")
    stage_manager.inject_scan_batch(scan_E)
    log("Attente de la fin du scan E...")
    wait_scan_finished(stage_manager)
    log("Scan E terminé.")

    log("Test terminé.")

if __name__ == "__main__":
    main() 