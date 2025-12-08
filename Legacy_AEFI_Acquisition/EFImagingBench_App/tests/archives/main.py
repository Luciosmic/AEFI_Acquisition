3#!/usr/bin/env python3
"""
Script Principal - Analyse Accéléromètre LSM9D avec Banc d'Imagerie EF
=======================================================================

Point d'entrée principal pour tous les outils d'analyse de l'accéléromètre.
Offre un menu interactif pour :
- Configuration et test du système
- Acquisition de données
- Analyse spectrale
- Tests avec données simulées

Auteur: Banc d'imagerie EF
Date: 2024
"""

import sys
import os
from pathlib import Path
import argparse

# Configuration initiale
try:
    from config_paths import setup_paths, print_config, get_config
    
    print("🔧 Configuration du système...")
    if not setup_paths():
        print("❌ Erreur de configuration. Veuillez vérifier l'organisation des répertoires.")
        sys.exit(1)
        
except ImportError:
    print("❌ Fichier config_paths.py introuvable. Assurez-vous d'être dans le bon répertoire.")
    sys.exit(1)

def check_dependencies():
    """Vérifie que toutes les dépendances sont installées."""
    print("📦 Vérification des dépendances...")
    
    missing_deps = []
    
    # Dépendances de base
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        import pandas
    except ImportError:
        missing_deps.append("pandas")
    
    try:
        import matplotlib
    except ImportError:
        missing_deps.append("matplotlib")
    
    try:
        import scipy
    except ImportError:
        missing_deps.append("scipy")
    
    try:
        import serial
    except ImportError:
        missing_deps.append("pyserial")
    
    if missing_deps:
        print("❌ Dépendances manquantes:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\n💡 Installation:")
        print("   pip install -r requirements_analysis.txt")
        return False
    
    print("✅ Toutes les dépendances sont installées")
    return True

def test_hardware_connection():
    """Teste la connexion aux équipements."""
    print("\n🔌 Test de connexion aux équipements...")
    
    config = get_config()
    
    # Test LSM9D
    try:
        from LSM9D_Backend import LSM9D_Backend
        
        print(f"📡 Test LSM9D sur {config['hardware']['lsm9d_port']}...")
        lsm9d = LSM9D_Backend(port=config['hardware']['lsm9d_port'])
        
        if lsm9d.connect():
            print("   ✅ LSM9D connecté")
            lsm9d.disconnect()
        else:
            print("   ❌ LSM9D non connecté")
            
    except Exception as e:
        print(f"   ❌ Erreur LSM9D: {e}")
    
    # Test Arcus
    try:
        from EFImagingBench_Controller_ArcusPerformax4EXStage import EFImagingStageController
        
        print("🎮 Test contrôleur Arcus...")
        stage = EFImagingStageController(config['paths']['arcus_dll_path'])
        print("   ✅ Contrôleur Arcus initialisé")
        stage.close()
        
    except Exception as e:
        print(f"   ❌ Erreur Arcus: {e}")

def run_acquisition():
    """Lance le script d'acquisition."""
    print("\n🔬 Lancement de l'acquisition...")
    
    try:
        from accelerometer_analysis_script import main as acquisition_main
        acquisition_main()
    except Exception as e:
        print(f"❌ Erreur lors de l'acquisition: {e}")

def run_spectral_analysis():
    """Lance l'analyse spectrale."""
    print("\n📊 Lancement de l'analyse spectrale...")
    
    try:
        from accelerometer_spectral_analysis import main as analysis_main
        analysis_main()
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")

def run_test_demo():
    """Lance la démonstration avec données de test."""
    print("\n🧪 Lancement de la démonstration...")
    
    try:
        from test_spectral_analysis import run_analysis_demo
        run_analysis_demo()
    except Exception as e:
        print(f"❌ Erreur lors de la démonstration: {e}")

def show_help():
    """Affiche l'aide détaillée."""
    print("\n📖 AIDE - ANALYSEUR ACCÉLÉROMÈTRE LSM9D")
    print("=" * 60)
    
    print("\n🎯 OBJECTIFS:")
    print("   • Mesurer le niveau de bruit de l'accéléromètre")
    print("   • Analyser l'influence des mouvements du stage")
    print("   • Caractériser le contenu fréquentiel des vibrations")
    
    print("\n🔄 WORKFLOW TYPIQUE:")
    print("   1. Configuration et test du système (option 1)")
    print("   2. Acquisition de données (option 2)")
    print("      - Mesure statique (bruit de fond)")
    print("      - Mesures dynamiques (différentes vitesses)")
    print("   3. Analyse spectrale (option 3)")
    print("      - Calcul FFT et PSD")
    print("      - Identification fréquences dominantes")
    print("      - Comparaison statique vs dynamique")
    
    print("\n📁 FICHIERS GÉNÉRÉS:")
    print("   accelerometer_data/")
    print("   ├── [experiment]_[timestamp].csv      # Données brutes")
    print("   └── [experiment]_[timestamp]_params.json  # Paramètres")
    print("   analysis_results/")
    print("   ├── spectral_analysis_[file]_[timestamp].png  # Graphiques")
    print("   ├── comparison_[timestamp].png               # Comparaisons")
    print("   └── analysis_report_[timestamp].txt          # Rapport détaillé")
    
    print("\n🔧 CONFIGURATION:")
    print("   • LSM9D: Mode ALL_SENSORS, 20 Hz")
    print("   • Arcus: Paramètres vitesse configurables")
    print("   • Bandes fréquentielles: 0.1-2 Hz, 2-8 Hz, 8-10 Hz")

def main_menu():
    """Affiche le menu principal."""
    while True:
        print("\n" + "=" * 60)
        print("🔬 ANALYSEUR ACCÉLÉROMÈTRE LSM9D - BANC IMAGERIE EF")
        print("=" * 60)
        
        print("\n📋 Options disponibles:")
        print("  1. 🔧 Configuration et test du système")
        print("  2. 📊 Acquisition de données expérimentales")
        print("  3. 📈 Analyse spectrale des données")
        print("  4. 🧪 Démonstration avec données simulées")
        print("  5. 📖 Aide et documentation")
        print("  6. 🚪 Quitter")
        
        try:
            choice = input("\nChoisissez une option (1-6): ").strip()
            
            if choice == '1':
                print_config()
                if check_dependencies():
                    test_hardware_connection()
                    
            elif choice == '2':
                if check_dependencies():
                    run_acquisition()
                    
            elif choice == '3':
                if check_dependencies():
                    run_spectral_analysis()
                    
            elif choice == '4':
                if check_dependencies():
                    run_test_demo()
                    
            elif choice == '5':
                show_help()
                
            elif choice == '6':
                print("\n👋 Au revoir !")
                break
                
            else:
                print("❌ Choix invalide. Utilisez 1, 2, 3, 4, 5 ou 6.")
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Arrêt demandé par l'utilisateur")
            break
        except Exception as e:
            print(f"\n❌ Erreur: {e}")

def main():
    """Fonction principale avec support des arguments en ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Analyseur d'accéléromètre LSM9D pour banc d'imagerie EF"
    )
    parser.add_argument(
        '--config', 
        action='store_true',
        help='Afficher la configuration et quitter'
    )
    parser.add_argument(
        '--test', 
        action='store_true',
        help='Tester les connexions et quitter'
    )
    parser.add_argument(
        '--acquire', 
        action='store_true',
        help='Lancer directement l\'acquisition'
    )
    parser.add_argument(
        '--analyze', 
        action='store_true',
        help='Lancer directement l\'analyse spectrale'
    )
    parser.add_argument(
        '--demo', 
        action='store_true',
        help='Lancer la démonstration avec données simulées'
    )
    
    args = parser.parse_args()
    
    # Commandes directes
    if args.config:
        print_config()
        return
        
    if args.test:
        if check_dependencies():
            test_hardware_connection()
        return
        
    if args.acquire:
        if check_dependencies():
            run_acquisition()
        return
        
    if args.analyze:
        if check_dependencies():
            run_spectral_analysis()
        return
        
    if args.demo:
        if check_dependencies():
            run_test_demo()
        return
    
    # Menu interactif par défaut
    main_menu()

if __name__ == "__main__":
    main() 