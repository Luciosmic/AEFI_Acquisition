"""
Niveau 1 : Tests d'Import et Syntaxe
Objectif : Vérifier que le code se charge sans erreur

Complexité : 2/10
Durée estimée : 2 minutes
"""

import unittest
import sys
import os
from pathlib import Path


class TestLevel1Imports(unittest.TestCase):
    """Tests d'import et validation syntaxe"""
    
    def setUp(self):
        """Setup des chemins pour les imports"""
        # Ajouter le chemin du répertoire interface (parent des tests)
        self.interface_path = Path(__file__).parent.parent
        if str(self.interface_path) not in sys.path:
            sys.path.insert(0, str(self.interface_path))
    
    def test_01_import_components_init(self):
        """Test import du package components"""
        try:
            # Import du package components
            import components
            self.assertTrue(hasattr(components, '__version__'))
            print("✅ Import components.__init__ : OK")
        except ImportError as e:
            self.fail(f"❌ Échec import components.__init__ : {e}")
    
    def test_02_import_mode_controller(self):
        """Test import ModeController"""
        try:
            from getE3D.interface.components.AD9106_ADS131A04_ModeController_Module import ModeController, AcquisitionMode
            # Vérifications de base
            self.assertTrue(hasattr(ModeController, '__init__'))
            self.assertTrue(hasattr(AcquisitionMode, 'EXPLORATION'))
            self.assertTrue(hasattr(AcquisitionMode, 'EXPORT'))
            print("✅ Import ModeController : OK")
        except ImportError as e:
            self.fail(f"❌ Échec import ModeController : {e}")
    
    def test_03_import_data_buffer(self):
        """Test import DataBuffer classes"""
        try:
            from getE3D.interface.components.AD9106_ADS131A04_DataBuffer_Module import (
                AcquisitionSample, 
                CircularBuffer, 
                ProductionBuffer, 
                AdaptiveDataBuffer
            )
            # Vérifications de base
            self.assertTrue(hasattr(AcquisitionSample, '__init__'))
            self.assertTrue(hasattr(CircularBuffer, 'append_sample'))
            self.assertTrue(hasattr(ProductionBuffer, 'append_sample'))
            self.assertTrue(hasattr(AdaptiveDataBuffer, 'set_mode'))
            print("✅ Import DataBuffer classes : OK")
        except ImportError as e:
            self.fail(f"❌ Échec import DataBuffer : {e}")
    
    def test_04_import_adc_converter(self):
        """Test import ADCConverter"""
        try:
            from getE3D.interface.components.ADS131A04_Converter_Module import ADCConverter, ADCUnit
            # Vérifications de base
            self.assertTrue(hasattr(ADCConverter, 'convert_sample'))
            self.assertTrue(hasattr(ADCUnit, 'CODES_ADC'))
            self.assertTrue(hasattr(ADCUnit, 'VOLTS'))
            print("✅ Import ADCConverter : OK")
        except ImportError as e:
            self.fail(f"❌ Échec import ADCConverter : {e}")
    
    def test_05_import_csv_exporter(self):
        """Test import CSVExporter"""
        try:
            from getE3D.interface.components.AD9106_ADS131A04_CSVexporter_Module import CSVExporter
            # Vérifications de base
            self.assertTrue(hasattr(CSVExporter, 'start_export'))
            self.assertTrue(hasattr(CSVExporter, 'add_samples'))
            print("✅ Import CSVExporter : OK")
        except ImportError as e:
            self.fail(f"❌ Échec import CSVExporter : {e}")
    
    def test_06_import_acquisition_manager(self):
        """Test import AcquisitionManager"""
        try:
            from getE3D.interface.components.AD9106_ADS131A04_acquisition_manager import AcquisitionManager
            # Vérifications de base
            self.assertTrue(hasattr(AcquisitionManager, 'start_acquisition'))
            self.assertTrue(hasattr(AcquisitionManager, 'stop_acquisition'))
            print("✅ Import AcquisitionManager : OK")
        except ImportError as e:
            self.fail(f"❌ Échec import AcquisitionManager : {e}")
    
    def test_07_validation_dependencies(self):
        """Test validation des dépendances PyQt5"""
        try:
            from PyQt5.QtCore import QObject, pyqtSignal, QThread, QTimer
            from PyQt5.QtWidgets import QApplication
            print("✅ Import PyQt5 : OK")
        except ImportError as e:
            self.fail(f"❌ PyQt5 non disponible : {e}")
        
        try:
            import threading
            import queue
            import hashlib
            import json
            import csv
            print("✅ Import modules standards : OK")
        except ImportError as e:
            self.fail(f"❌ Modules standards manquants : {e}")
    
    def test_08_validation_types_hints(self):
        """Test validation types hints"""
        try:
            from typing import List, Dict, Optional, Callable, Union
            from dataclasses import dataclass
            from enum import Enum
            print("✅ Import typing : OK")
        except ImportError as e:
            self.fail(f"❌ Modules typing manquants : {e}")
    
    def test_09_verification_fichiers_backend(self):
        """Vérification que tous les fichiers backend existent"""
        expected_files = [
            "mode_controller.py",
            "data_buffer.py", 
            "adc_converter.py",
            "csv_exporter.py",
            "acquisition_manager.py"
        ]
        
        components_dir = Path(__file__).parent.parent / "components"
        
        for filename in expected_files:
            file_path = components_dir / filename
            self.assertTrue(
                file_path.exists(), 
                f"❌ Fichier manquant : {filename}"
            )
            print(f"✅ Fichier {filename} : présent")


def run_level1_tests():
    """Lance tous les tests niveau 1"""
    print("🔧 === TESTS NIVEAU 1 : Imports et Syntaxe ===")
    print("⏱️  Durée estimée : 2 minutes")
    print("🎯 Objectif : Vérifier que le code se charge sans erreur\n")
    
    # Configuration du test runner
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestLevel1Imports)
    
    # Exécution avec verbosité
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Rapport final
    print(f"\n📊 === RÉSULTATS NIVEAU 1 ===")
    print(f"Tests exécutés : {result.testsRun}")
    print(f"Succès : {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Échecs : {len(result.failures)}")
    print(f"Erreurs : {len(result.errors)}")
    
    if result.failures:
        print("\n❌ ÉCHECS :")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n🚨 ERREURS :")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    if success:
        print("\n🎉 NIVEAU 1 : TOUS LES TESTS PASSENT !")
        print("✅ Prêt pour les tests niveau 2")
    else:
        print("\n⚠️  NIVEAU 1 : ÉCHECS DÉTECTÉS")
        print("🔧 Corriger les imports avant de continuer")
    
    return success


if __name__ == "__main__":
    # Exécution directe
    success = run_level1_tests()
    sys.exit(0 if success else 1) 