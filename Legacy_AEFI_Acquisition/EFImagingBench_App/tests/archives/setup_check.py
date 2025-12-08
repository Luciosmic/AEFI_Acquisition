#!/usr/bin/env python3
"""
Script de Vérification de l'Installation - EFImagingBench
=========================================================

Ce script vérifie que tout est correctement configuré pour utiliser
l'analyseur d'accéléromètre LSM9D avec le banc d'imagerie EF.

Usage:
    python setup_check.py
"""

import sys
import os
from pathlib import Path
import importlib.util

def check_python_version():
    """Vérifie la version de Python."""
    print("🐍 Vérification de la version Python...")
    
    if sys.version_info < (3, 7):
        print(f"   ❌ Python {sys.version_info.major}.{sys.version_info.minor} détecté")
        print("   ⚠️  Python 3.7+ requis")
        return False
    else:
        print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        return True

def check_config_file():
    """Vérifie le fichier de configuration."""
    print("\n🔧 Vérification du fichier de configuration...")
    
    config_file = Path(__file__).parent / 'config_paths.py'
    
    if not config_file.exists():
        print("   ❌ config_paths.py introuvable")
        return False
    
    try:
        from config_paths import setup_paths, get_config, print_config
        
        print("   ✅ config_paths.py importé avec succès")
        
        # Test de la configuration
        if setup_paths():
            print("   ✅ Configuration des chemins réussie")
            return True
        else:
            print("   ❌ Erreur dans la configuration des chemins")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur lors de l'import: {e}")
        return False

def check_dependencies():
    """Vérifie toutes les dépendances Python."""
    print("\n📦 Vérification des dépendances Python...")
    
    dependencies = {
        'numpy': 'Calcul scientifique',
        'pandas': 'Manipulation de données',
        'matplotlib': 'Visualisation',
        'scipy': 'Traitement du signal',
        'serial': 'Communication série (pyserial)'
    }
    
    all_ok = True
    
    for package, description in dependencies.items():
        try:
            if package == 'serial':
                import serial
            else:
                importlib.import_module(package)
            print(f"   ✅ {package} - {description}")
        except ImportError:
            print(f"   ❌ {package} - {description} (MANQUANT)")
            all_ok = False
    
    if not all_ok:
        print("\n💡 Pour installer les dépendances manquantes:")
        print("   pip install -r requirements_analysis.txt")
    
    return all_ok

def check_project_structure():
    """Vérifie la structure du projet."""
    print("\n📁 Vérification de la structure du projet...")
    
    base_dir = Path(__file__).parent.parent
    
    expected_structure = {
        'LSM9D': 'Modules du capteur LSM9D',
        'LSM9D/LSM9D_Backend.py': 'Backend LSM9D',
        'ArcusPerformaxPythonController': 'Contrôleur Arcus',
        'ArcusPerformaxPythonController/controller': 'Scripts de contrôle',
        'ArcusPerformaxPythonController/DLL64': 'DLLs Arcus 64-bit'
    }
    
    all_ok = True
    
    for path, description in expected_structure.items():
        full_path = base_dir / path
        if full_path.exists():
            print(f"   ✅ {path} - {description}")
        else:
            print(f"   ❌ {path} - {description} (MANQUANT)")
            all_ok = False
    
    return all_ok

def check_efimagingbench_files():
    """Vérifie les fichiers du répertoire EFImagingBench."""
    print("\n📋 Vérification des fichiers EFImagingBench...")
    
    efi_dir = Path(__file__).parent
    
    required_files = {
        'config_paths.py': 'Configuration centralisée',
        'accelerometer_analysis_script.py': 'Script d\'acquisition',
        'accelerometer_spectral_analysis.py': 'Analyseur spectral',
        'test_spectral_analysis.py': 'Tests avec données simulées',
        'main.py': 'Script principal avec menu',
        'requirements_analysis.txt': 'Liste des dépendances'
    }
    
    all_ok = True
    
    for filename, description in required_files.items():
        file_path = efi_dir / filename
        if file_path.exists():
            print(f"   ✅ {filename} - {description}")
        else:
            print(f"   ❌ {filename} - {description} (MANQUANT)")
            all_ok = False
    
    return all_ok

def check_data_directories():
    """Vérifie et crée les répertoires de données."""
    print("\n📂 Vérification des répertoires de données...")
    
    efi_dir = Path(__file__).parent
    
    directories = {
        'accelerometer_data': 'Données d\'acquisition',
        'analysis_results': 'Résultats d\'analyse'
    }
    
    for dirname, description in directories.items():
        dir_path = efi_dir / dirname
        
        if dir_path.exists():
            print(f"   ✅ {dirname}/ - {description}")
        else:
            try:
                dir_path.mkdir(exist_ok=True)
                print(f"   ✅ {dirname}/ - {description} (créé)")
            except Exception as e:
                print(f"   ❌ {dirname}/ - Erreur création: {e}")
                return False
    
    return True

def check_imports():
    """Teste les imports des modules principaux."""
    print("\n🔗 Test des imports des modules principaux...")
    
    # Configurer les chemins d'abord
    try:
        from config_paths import setup_paths
        setup_paths()
    except:
        print("   ❌ Impossible de configurer les chemins")
        return False
    
    modules_to_test = {
        'LSM9D_Backend': 'Backend capteur LSM9D',
        'EFImagingBench_Controller_ArcusPerformax4EXStage': 'Contrôleur Arcus'
    }
    
    all_ok = True
    
    for module_name, description in modules_to_test.items():
        try:
            importlib.import_module(module_name)
            print(f"   ✅ {module_name} - {description}")
        except ImportError as e:
            print(f"   ❌ {module_name} - {description} (Erreur: {e})")
            all_ok = False
        except Exception as e:
            print(f"   ⚠️  {module_name} - {description} (Avertissement: {e})")
    
    return all_ok

def generate_summary():
    """Génère un résumé de la vérification."""
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ DE LA VÉRIFICATION")
    print("=" * 60)
    
    checks = [
        ("Version Python", check_python_version()),
        ("Fichier de configuration", check_config_file()),
        ("Dépendances Python", check_dependencies()),
        ("Structure du projet", check_project_structure()),
        ("Fichiers EFImagingBench", check_efimagingbench_files()),
        ("Répertoires de données", check_data_directories()),
        ("Imports des modules", check_imports())
    ]
    
    passed = sum(1 for _, status in checks if status)
    total = len(checks)
    
    print(f"\n🎯 Résultat: {passed}/{total} vérifications réussies")
    
    if passed == total:
        print("\n🎉 INSTALLATION COMPLÈTE ET FONCTIONNELLE!")
        print("💡 Vous pouvez maintenant utiliser:")
        print("   python main.py")
        return True
    else:
        print("\n⚠️  PROBLÈMES DÉTECTÉS:")
        for name, status in checks:
            if not status:
                print(f"   ❌ {name}")
        
        print("\n💡 Actions recommandées:")
        print("   1. Installer les dépendances manquantes")
        print("   2. Vérifier l'organisation des répertoires")
        print("   3. Relancer cette vérification")
        return False

def main():
    """Fonction principale."""
    print("🔍 VÉRIFICATION DE L'INSTALLATION - EFIMAGINGBENCH")
    print("=" * 60)
    print("Ce script vérifie que tout est prêt pour l'analyse de l'accéléromètre")
    
    try:
        if generate_summary():
            print("\n🚀 Prêt à démarrer l'analyse!")
        else:
            print("\n🔧 Veuillez corriger les problèmes et relancer la vérification")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Vérification interrompue")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 