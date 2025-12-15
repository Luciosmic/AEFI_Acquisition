#!/usr/bin/env python3
"""
Configuration des chemins d'accès pour le projet EFImagingBench
===============================================================

Ce fichier centralise tous les chemins d'accès utilisés dans les différents scripts
pour faciliter la maintenance et l'adaptation à différents environnements.
"""

import os
from pathlib import Path

# Répertoire racine du projet (répertoire parent de EFImagingBench)
PROJECT_ROOT = Path(__file__).parent.parent

# Chemins vers les modules
LSM9D_PATH = PROJECT_ROOT / 'LSM9D'
ARCUS_CONTROLLER_PATH = PROJECT_ROOT / 'ArcusPerformaxPythonController' / 'controller'
ARCUS_DLL_PATH = PROJECT_ROOT / 'ArcusPerformaxPythonController' / 'DLL64'

# Répertoires de données et résultats (dans EFImagingBench)
EFIMAGINGBENCH_DIR = Path(__file__).parent
DATA_DIRECTORY = EFIMAGINGBENCH_DIR / 'accelerometer_data'
RESULTS_DIRECTORY = EFIMAGINGBENCH_DIR / 'analysis_results'

# Configuration des ports par défaut
DEFAULT_LSM9D_PORT = 'COM5'
DEFAULT_BAUDRATE = 256000

# Paramètres d'acquisition par défaut
DEFAULT_SAMPLING_RATE = 20  # Hz
DEFAULT_LSM9D_MODE = 'ALL_SENSORS'

def setup_paths():
    """
    Configure les chemins d'import Python et crée les répertoires nécessaires.
    
    :return: True si la configuration réussit, False sinon
    """
    import sys
    
    # Ajouter les chemins aux modules Python
    paths_to_add = [
        str(LSM9D_PATH),
        str(ARCUS_CONTROLLER_PATH)
    ]
    
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.append(path)
    
    # Créer les répertoires de données et résultats s'ils n'existent pas
    DATA_DIRECTORY.mkdir(exist_ok=True)
    RESULTS_DIRECTORY.mkdir(exist_ok=True)
    
    # Vérifier que les modules essentiels sont accessibles
    missing_paths = []
    
    if not LSM9D_PATH.exists():
        missing_paths.append(f"LSM9D: {LSM9D_PATH}")
    
    if not ARCUS_CONTROLLER_PATH.exists():
        missing_paths.append(f"ArcusController: {ARCUS_CONTROLLER_PATH}")
    
    if not ARCUS_DLL_PATH.exists():
        missing_paths.append(f"ArcusDLL: {ARCUS_DLL_PATH}")
    
    if missing_paths:
        print("⚠️  Attention: Certains chemins sont introuvables:")
        for path in missing_paths:
            print(f"   ❌ {path}")
        print("💡 Vérifiez l'organisation des répertoires du projet")
        return False
    
    print("✅ Configuration des chemins réussie")
    return True

def get_config():
    """
    Retourne un dictionnaire avec toute la configuration.
    
    :return: Dictionnaire de configuration
    """
    return {
        'paths': {
            'project_root': str(PROJECT_ROOT),
            'lsm9d_path': str(LSM9D_PATH),
            'arcus_controller_path': str(ARCUS_CONTROLLER_PATH),
            'arcus_dll_path': str(ARCUS_DLL_PATH),
            'data_directory': str(DATA_DIRECTORY),
            'results_directory': str(RESULTS_DIRECTORY)
        },
        'hardware': {
            'lsm9d_port': DEFAULT_LSM9D_PORT,
            'baudrate': DEFAULT_BAUDRATE
        },
        'acquisition': {
            'sampling_rate': DEFAULT_SAMPLING_RATE,
            'lsm9d_mode': DEFAULT_LSM9D_MODE
        }
    }

def print_config():
    """Affiche la configuration actuelle."""
    config = get_config()
    
    print("🔧 CONFIGURATION EFIMAGINGBENCH")
    print("=" * 50)
    
    print("\n📁 Chemins:")
    for name, path in config['paths'].items():
        status = "✅" if Path(path).exists() else "❌"
        print(f"   {status} {name}: {path}")
    
    print("\n🔌 Matériel:")
    for name, value in config['hardware'].items():
        print(f"   📡 {name}: {value}")
    
    print("\n⚙️  Acquisition:")
    for name, value in config['acquisition'].items():
        print(f"   📊 {name}: {value}")

if __name__ == "__main__":
    print_config()
    print("\n🔧 Test de configuration...")
    success = setup_paths()
    
    if success:
        print("🎉 Configuration prête!")
    else:
        print("❌ Problèmes de configuration détectés") 