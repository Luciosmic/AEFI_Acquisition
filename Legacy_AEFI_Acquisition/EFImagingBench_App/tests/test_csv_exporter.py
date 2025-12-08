#!/usr/bin/env python3
"""
Test unitaire pour le module EFImagingBench_CSVExporter_Module
Vérifie la création des fichiers CSV et l'export des données
"""

import sys
import os
import time
from pathlib import Path
import tempfile
import shutil

# Ajoute le chemin pour importer les modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Import du module à tester
from core.EFImagingBench_CSVExporter_Module import EFImagingBenchCSVExporter, ExportConfig, CSVSensorExporter, CSVPositionExporter

# Création de classes de test pour AcquisitionSample et PositionSample
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AcquisitionSample:
    """Mock de AcquisitionSample pour tests"""
    adc1_ch1: float = 1.0
    adc1_ch2: float = 2.0
    adc1_ch3: float = 3.0
    adc1_ch4: float = 4.0
    adc2_ch1: float = 5.0
    adc2_ch2: float = 6.0
    adc2_ch3: float = 7.0
    adc2_ch4: float = 8.0

@dataclass
class PositionSample:
    """Mock de PositionSample pour tests"""
    x: float
    y: float
    timestamp: datetime


def test_csv_sensor_exporter():
    """Test l'exporteur de données capteur"""
    print("=== Test CSVSensorExporter ===")
    
    # Créer un dossier temporaire
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Dossier temporaire: {temp_dir}")
        
        # Configuration
        config = ExportConfig(
            output_dir=temp_dir,
            filename_base="TestSensor",
            metadata={"test": "sensor", "version": "1.0"}
        )
        
        # Créer l'exporteur
        exporter = CSVSensorExporter()
        
        # Démarrer l'export
        success = exporter.start_export(config)
        print(f"Démarrage export: {success}")
        assert success, "Échec du démarrage de l'export"
        
        # Ajouter des échantillons
        for i in range(10):
            sample = AcquisitionSample(
                adc1_ch1=i*0.1, adc1_ch2=i*0.2, adc1_ch3=i*0.3, adc1_ch4=i*0.4,
                adc2_ch1=i*0.5, adc2_ch2=i*0.6, adc2_ch3=i*0.7, adc2_ch4=i*0.8
            )
            exporter.add_sample(sample)
            time.sleep(0.01)  # Petit délai pour simuler acquisition
        
        # Attendre un peu pour que les données soient écrites
        time.sleep(0.5)
        
        # Arrêter l'export
        stop_success = exporter.stop_export()
        print(f"Arrêt export: {stop_success}")
        assert stop_success, "Échec de l'arrêt de l'export"
        
        # Vérifier que le fichier existe
        csv_files = list(Path(temp_dir).glob("*_TestSensor_E_all.csv"))
        print(f"Fichiers trouvés: {csv_files}")
        assert len(csv_files) == 1, f"Attendu 1 fichier, trouvé {len(csv_files)}"
        
        # Lire et vérifier le contenu
        with open(csv_files[0], 'r') as f:
            content = f.read()
            print(f"\nContenu du fichier (premières lignes):")
            print('\n'.join(content.split('\n')[:20]))
            
            assert "# Metadata" in content
            assert "test" in content
            assert "ADC1_Ch1 Ex_real" in content
            assert str(exporter._samples_written) in content
            print(f"Échantillons écrits: {exporter._samples_written}")


def test_csv_position_exporter():
    """Test l'exporteur de positions"""
    print("\n=== Test CSVPositionExporter ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Dossier temporaire: {temp_dir}")
        
        config = ExportConfig(
            output_dir=temp_dir,
            filename_base="TestPosition",
            metadata={"test": "position", "scan": "2D"}
        )
        
        exporter = CSVPositionExporter()
        success = exporter.start_export(config)
        print(f"Démarrage export: {success}")
        assert success
        
        # Ajouter des positions
        for i in range(5):
            sample = PositionSample(x=i*10.0, y=i*5.0, timestamp=datetime.now())
            exporter.add_sample(sample)
            time.sleep(0.01)
        
        time.sleep(0.5)
        stop_success = exporter.stop_export()
        print(f"Arrêt export: {stop_success}")
        assert stop_success
        
        csv_files = list(Path(temp_dir).glob("*_TestPosition_Position_all.csv"))
        print(f"Fichiers trouvés: {csv_files}")
        assert len(csv_files) == 1
        
        with open(csv_files[0], 'r') as f:
            content = f.read()
            print(f"\nContenu du fichier:")
            print(content)
            assert "timestamp_rel" in content
            assert "x" in content and "y" in content


def test_combined_exporter():
    """Test l'exporteur combiné"""
    print("\n=== Test EFImagingBenchCSVExporter (combiné) ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Dossier temporaire: {temp_dir}")
        
        config = ExportConfig(
            output_dir=temp_dir,
            filename_base="TestCombined",
            metadata={"test": "combined", "mode": "SCANNING"}
        )
        
        exporter = EFImagingBenchCSVExporter()
        success = exporter.start_export(config)
        print(f"Démarrage export combiné: {success}")
        assert success
        assert exporter.is_exporting
        
        # Ajouter des données des deux types
        for i in range(3):
            # Données capteur
            sensor_sample = AcquisitionSample()
            exporter.add_sensor_sample(sensor_sample)
            
            # Données position
            pos_sample = PositionSample(x=i*1.0, y=i*2.0, timestamp=datetime.now())
            exporter.add_position_sample(pos_sample)
            
            time.sleep(0.05)
        
        time.sleep(0.5)
        stop_success = exporter.stop_export()
        print(f"Arrêt export combiné: {stop_success}")
        assert stop_success
        assert not exporter.is_exporting
        
        # Vérifier les deux fichiers
        sensor_files = list(Path(temp_dir).glob("*_TestCombined_E_all.csv"))
        position_files = list(Path(temp_dir).glob("*_TestCombined_Position_all.csv"))
        
        print(f"Fichiers capteur: {sensor_files}")
        print(f"Fichiers position: {position_files}")
        
        assert len(sensor_files) == 1, "Fichier capteur manquant"
        assert len(position_files) == 1, "Fichier position manquant"


def test_real_path():
    """Test avec le chemin réel par défaut"""
    print("\n=== Test avec chemin réel ===")
    
    # Utiliser le chemin par défaut
    real_path = r"C:\Users\manip\Documents\Data"
    
    # Vérifier si le dossier existe, sinon utiliser temp
    if not os.path.exists(real_path):
        print(f"Le dossier {real_path} n'existe pas, utilisation d'un dossier temporaire")
        real_path = tempfile.mkdtemp()
        cleanup = True
    else:
        cleanup = False
        print(f"Utilisation du dossier réel: {real_path}")
    
    try:
        config = ExportConfig(
            output_dir=real_path,
            filename_base="TestReal",
            metadata={"test": "real_path"}
        )
        
        exporter = EFImagingBenchCSVExporter()
        success = exporter.start_export(config)
        print(f"Démarrage export: {success}")
        
        if success:
            # Ajouter un échantillon
            exporter.add_sensor_sample(AcquisitionSample())
            exporter.add_position_sample(PositionSample(x=1.0, y=2.0, timestamp=datetime.now()))
            
            time.sleep(0.5)
            exporter.stop_export()
            
            # Lister les fichiers créés
            files = list(Path(real_path).glob("*_TestReal_*.csv"))
            print(f"Fichiers créés: {files}")
            
            # Nettoyer si demandé
            if cleanup:
                for f in files:
                    f.unlink()
    finally:
        if cleanup and os.path.exists(real_path):
            shutil.rmtree(real_path)


def test_debug_integration():
    """Test de débogage pour comprendre pourquoi l'export ne fonctionne pas dans l'app principale"""
    print("\n=== Test de débogage intégration ===")
    
    # Test avec la configuration exacte de l'UI
    output_dir = r"C:\Users\manip\Documents\Data"
    
    # Vérifier si le dossier existe
    if not os.path.exists(output_dir):
        print(f"⚠️ ATTENTION: Le dossier {output_dir} n'existe pas!")
        print("  Cela pourrait expliquer pourquoi l'export ne fonctionne pas.")
        print("  Création du dossier...")
        try:
            os.makedirs(output_dir, exist_ok=True)
            print("  ✅ Dossier créé avec succès")
        except Exception as e:
            print(f"  ❌ Erreur lors de la création: {e}")
            return
    else:
        print(f"✅ Le dossier {output_dir} existe")
    
    # Test export avec config par défaut
    config = ExportConfig()
    print(f"Configuration par défaut:")
    print(f"  - output_dir: {config.output_dir}")
    print(f"  - filename_base: {config.filename_base}")
    print(f"  - metadata: {config.metadata}")
    
    exporter = EFImagingBenchCSVExporter()
    success = exporter.start_export(config)
    print(f"Démarrage export: {success}")
    
    if not success:
        print("❌ L'export n'a pas pu démarrer")
        return
        
    # Test ajout de données
    print("Test ajout de données...")
    try:
        sensor_sample = AcquisitionSample()
        exporter.add_sensor_sample(sensor_sample)
        print("  ✅ Ajout sample capteur OK")
        
        pos_sample = PositionSample(x=1.0, y=2.0, timestamp=datetime.now())
        exporter.add_position_sample(pos_sample)
        print("  ✅ Ajout sample position OK")
        
    except Exception as e:
        print(f"  ❌ Erreur lors de l'ajout: {e}")
    
    time.sleep(1.0)
    
    # Arrêt et vérification
    stop_success = exporter.stop_export()
    print(f"Arrêt export: {stop_success}")
    
    # Lister les fichiers créés
    files = list(Path(output_dir).glob("*_Default_*.csv"))
    print(f"\nFichiers créés dans {output_dir}:")
    for f in files:
        print(f"  - {f.name}")
        
    if not files:
        print("  ❌ AUCUN fichier créé!")
        print("\nVérifications supplémentaires:")
        print(f"  - L'exporteur sensor est-il en train d'exporter? {exporter.sensor_exporter._is_exporting}")
        print(f"  - L'exporteur position est-il en train d'exporter? {exporter.position_exporter._is_exporting}")


if __name__ == "__main__":
    print("Démarrage des tests du module CSV Exporter")
    print("="*50)
    
    try:
        test_csv_sensor_exporter()
        test_csv_position_exporter()
        test_combined_exporter()
        test_real_path()
        test_debug_integration()  # Nouveau test
        
        print("\n" + "="*50)
        print("✅ Tous les tests sont passés avec succès!")
        
    except AssertionError as e:
        print(f"\n❌ Échec du test: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        raise 