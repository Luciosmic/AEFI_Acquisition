# -*- coding: utf-8 -*-
import os, sys
import sys
import os

# Trouve la racine du projet (celle qui contient 'core')
def find_project_root(marker='core'):
    d = os.path.abspath(os.path.dirname(__file__))
    while d != os.path.dirname(d):
        if marker in os.listdir(d):
            return d
        d = os.path.dirname(d)
    return None

project_root = find_project_root('core')
if project_root and project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.EFImagingBench_metaManager import MetaManager
import time

# === Callbacks pour les signaux ===
def on_error(msg):
    print("[MetaManager][ERROR]", msg)

def on_status(status):
    print("[MetaManager][STATUS]", status)

def on_data_ready_stage(data):
    print("[MetaManager][DATA_READY_STAGE]", data)

def on_data_ready_acq(data):
    print("[MetaManager][DATA_READY_ACQ]", data)

def on_config_stage(cfg):
    print("[MetaManager][CONFIG_STAGE]", cfg)

def on_config_acq(cfg):
    print("[MetaManager][CONFIG_ACQ]", cfg)

def on_mode_stage(mode):
    print("[MetaManager][MODE_STAGE]", mode)

def on_mode_acq(mode):
    print("[MetaManager][MODE_ACQ]", mode)

# === Instanciation ===
meta = MetaManager()

# === Connexion des signaux ===
meta.error_occurred.connect(on_error)
meta.status_changed.connect(on_status)
meta.data_ready_stage.connect(on_data_ready_stage)
meta.data_ready_acquisition.connect(on_data_ready_acq)
meta.configuration_changed_stage.connect(on_config_stage)
meta.configuration_changed_acquisition.connect(on_config_acq)
meta.mode_changed_stage.connect(on_mode_stage)
meta.mode_changed_acquisition.connect(on_mode_acq)

print("[TEST] Homing des deux axes...")
meta.home_both_stages()
print("[TEST] Merci de valider que le homing est terminé (vérification visuelle ou via l'interface).")
input("Appuyez sur Entrée pour continuer après le homing...")

print("[TEST] Déplacement de l'axe X à 10 000 (unités incréments)...")
meta.move_stage_to('x', 10000)
time.sleep(2)

print("[TEST] Démarrage de l'acquisition (exploration, n_avg=10)...")
meta.start_acquisition('exploration', {'n_avg': 10})
time.sleep(5)

print("[TEST] Arrêt de l'acquisition...")
meta.stop_acquisition()

print("[TEST] Fin du test. Vous pouvez fermer le script.") 