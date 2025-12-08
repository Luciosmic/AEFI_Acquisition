"""
Niveau 2 : Tests Unitaires - ModeController
Objectif : Validation isolée de la gestion des modes

Complexité : 3/10
Durée estimée : 3 minutes
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import du module à tester
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from getE3D.interface.components.AD9106_ADS131A04_ModeController_Module import ModeController, AcquisitionMode
    IMPORT_SUCCESS = True
except ImportError as e:
    IMPORT_SUCCESS = False
    IMPORT_ERROR = str(e)


class TestModeController(unittest.TestCase):
    """Tests unitaires pour ModeController"""
    
    def setUp(self):
        """Setup avant chaque test"""
        if not IMPORT_SUCCESS:
            self.skipTest(f"Import impossible : {IMPORT_ERROR}")
        
        # Configuration test par défaut
        self.test_config = {
            'gain_dds': 5000,
            'freq_hz': 1000.0,
            'n_avg': 10
        }
        
        # Mock du SerialCommunicator
        self.mock_serial = Mock()
        self.mock_serial.memory_state = {'config': self.test_config.copy()}
        
        # Création instance ModeController
        self.controller = ModeController(self.mock_serial)
    
    def test_01_initialisation_mode_exploration(self):
        """Test initialisation : Mode EXPLORATION par défaut [1/10]"""
        # Vérification mode initial
        self.assertEqual(
            self.controller.current_mode, 
            AcquisitionMode.EXPLORATION,
            "Mode initial doit être EXPLORATION"
        )
        
        # Vérification config initiale
        current_config = self.controller.get_current_configuration()
        self.assertEqual(current_config['gain_dds'], 5000)
        self.assertEqual(current_config['freq_hz'], 1000.0)
        self.assertEqual(current_config['n_avg'], 10)
        
        print("✅ Initialisation mode EXPLORATION : OK")
    
    def test_02_transition_exploration_vers_export(self):
        """Test transitions valides : EXPLORATION → EXPORT [2/10]"""
        # Configuration pour export
        export_config = {
            'export_dir': '/tmp/test',
            'export_filename': 'test_export',
            'duration_seconds': 30
        }
        
        # Mock des signaux PyQt5
        with patch.object(self.controller, 'mode_changed') as mock_signal:
            # Demande transition vers EXPORT
            success = self.controller.request_export_mode(export_config)
            
            # Vérifications
            self.assertTrue(success, "Transition vers EXPORT doit réussir")
            self.assertEqual(self.controller.current_mode, AcquisitionMode.EXPORT)
            
            # Vérification signal émis
            mock_signal.emit.assert_called_once_with(AcquisitionMode.EXPORT)
        
        print("✅ Transition EXPLORATION → EXPORT : OK")
    
    def test_03_transition_export_vers_exploration(self):
        """Test transitions valides : EXPORT → EXPLORATION [2/10]"""
        # Mettre en mode EXPORT d'abord
        export_config = {'export_dir': '/tmp', 'export_filename': 'test', 'duration_seconds': 10}
        self.controller.request_export_mode(export_config)
        
        # Mock des signaux PyQt5
        with patch.object(self.controller, 'mode_changed') as mock_signal:
            # Retour vers EXPLORATION
            success = self.controller.return_to_exploration()
            
            # Vérifications
            self.assertTrue(success, "Retour vers EXPLORATION doit réussir")
            self.assertEqual(self.controller.current_mode, AcquisitionMode.EXPLORATION)
            
            # Vérification signal émis
            mock_signal.emit.assert_called_once_with(AcquisitionMode.EXPLORATION)
        
        print("✅ Transition EXPORT → EXPLORATION : OK")
    
    def test_04_validation_config_gain_dds_range(self):
        """Test validation config : Range gain_dds [2/10]"""
        # Test valeurs valides
        valid_configs = [
            {'gain_dds': 0, 'freq_hz': 1000.0, 'n_avg': 1},
            {'gain_dds': 8000, 'freq_hz': 1000.0, 'n_avg': 1},
            {'gain_dds': 16376, 'freq_hz': 1000.0, 'n_avg': 1}
        ]
        
        for config in valid_configs:
            is_valid, _ = self.controller.validate_configuration(config)
            self.assertTrue(is_valid, f"Config {config['gain_dds']} doit être valide")
        
        # Test valeurs invalides
        invalid_configs = [
            {'gain_dds': -1, 'freq_hz': 1000.0, 'n_avg': 1},
            {'gain_dds': 16377, 'freq_hz': 1000.0, 'n_avg': 1},
            {'gain_dds': 50000, 'freq_hz': 1000.0, 'n_avg': 1}
        ]
        
        for config in invalid_configs:
            is_valid, error_msg = self.controller.validate_configuration(config)
            self.assertFalse(is_valid, f"Config {config['gain_dds']} doit être invalide")
            self.assertIn('gain_dds', error_msg.lower())
        
        print("✅ Validation range gain_dds : OK")
    
    def test_05_validation_config_freq_hz_range(self):
        """Test validation config : Range freq_hz [2/10]"""
        # Test valeurs valides
        valid_configs = [
            {'gain_dds': 5000, 'freq_hz': 0.1, 'n_avg': 1},
            {'gain_dds': 5000, 'freq_hz': 500000.0, 'n_avg': 1},
            {'gain_dds': 5000, 'freq_hz': 1000000.0, 'n_avg': 1}
        ]
        
        for config in valid_configs:
            is_valid, _ = self.controller.validate_configuration(config)
            self.assertTrue(is_valid, f"Freq {config['freq_hz']} Hz doit être valide")
        
        # Test valeurs invalides
        invalid_configs = [
            {'gain_dds': 5000, 'freq_hz': 0.05, 'n_avg': 1},
            {'gain_dds': 5000, 'freq_hz': 1000001.0, 'n_avg': 1},
            {'gain_dds': 5000, 'freq_hz': -10.0, 'n_avg': 1}
        ]
        
        for config in invalid_configs:
            is_valid, error_msg = self.controller.validate_configuration(config)
            self.assertFalse(is_valid, f"Freq {config['freq_hz']} Hz doit être invalide")
            self.assertIn('freq_hz', error_msg.lower())
        
        print("✅ Validation range freq_hz : OK")
    
    def test_06_validation_config_n_avg(self):
        """Test validation config : n_avg > 0 [1/10]"""
        # Test valeurs valides
        valid_configs = [
            {'gain_dds': 5000, 'freq_hz': 1000.0, 'n_avg': 1},
            {'gain_dds': 5000, 'freq_hz': 1000.0, 'n_avg': 100},
            {'gain_dds': 5000, 'freq_hz': 1000.0, 'n_avg': 1000}
        ]
        
        for config in valid_configs:
            is_valid, _ = self.controller.validate_configuration(config)
            self.assertTrue(is_valid, f"N_avg {config['n_avg']} doit être valide")
        
        # Test valeurs invalides
        invalid_configs = [
            {'gain_dds': 5000, 'freq_hz': 1000.0, 'n_avg': 0},
            {'gain_dds': 5000, 'freq_hz': 1000.0, 'n_avg': -1},
            {'gain_dds': 5000, 'freq_hz': 1000.0, 'n_avg': -10}
        ]
        
        for config in invalid_configs:
            is_valid, error_msg = self.controller.validate_configuration(config)
            self.assertFalse(is_valid, f"N_avg {config['n_avg']} doit être invalide")
            self.assertIn('n_avg', error_msg.lower())
        
        print("✅ Validation n_avg > 0 : OK")
    
    def test_07_emission_signaux_pyqt5(self):
        """Test signaux PyQt5 : Émission correcte lors transitions [2/10]"""
        # Mock des signaux
        with patch.object(self.controller, 'mode_changed') as mock_mode_signal:
            with patch.object(self.controller, 'configuration_changed') as mock_config_signal:
                
                # Test changement configuration
                new_config = {'gain_dds': 8000, 'freq_hz': 2000.0, 'n_avg': 20}
                success = self.controller.update_configuration(new_config)
                
                self.assertTrue(success, "Update configuration doit réussir")
                
                # Vérification signal config émis
                mock_config_signal.emit.assert_called_once()
                
                # Test transition mode
                export_config = {'export_dir': '/tmp', 'export_filename': 'test', 'duration_seconds': 10}
                self.controller.request_export_mode(export_config)
                
                # Vérification signal mode émis
                mock_mode_signal.emit.assert_called_with(AcquisitionMode.EXPORT)
        
        print("✅ Émission signaux PyQt5 : OK")
    
    def test_08_rollback_echec_transition(self):
        """Test rollback : Reset état si transition échoue [3/10]"""
        # Configuration initiale
        initial_config = self.controller.get_current_configuration()
        initial_mode = self.controller.current_mode
        
        # Mock échec lors de la transition
        with patch.object(self.controller, '_apply_export_configuration') as mock_apply:
            mock_apply.side_effect = Exception("Échec application config")
            
            # Tentative transition qui doit échouer
            export_config = {'export_dir': '/invalid/path', 'export_filename': 'test', 'duration_seconds': 10}
            success = self.controller.request_export_mode(export_config)
            
            # Vérifications rollback
            self.assertFalse(success, "Transition doit échouer")
            self.assertEqual(self.controller.current_mode, initial_mode, "Mode doit être restauré")
            
            current_config = self.controller.get_current_configuration()
            self.assertEqual(current_config, initial_config, "Configuration doit être restaurée")
        
        print("✅ Rollback échec transition : OK")
    
    def test_09_sauvegarde_restauration_config(self):
        """Test sauvegarde/restauration config pendant transitions [2/10]"""
        # Configuration initiale
        initial_config = {
            'gain_dds': 7500,
            'freq_hz': 1500.0,
            'n_avg': 25
        }
        self.controller.update_configuration(initial_config)
        
        # Transition vers EXPORT
        export_config = {'export_dir': '/tmp', 'export_filename': 'test', 'duration_seconds': 10}
        success = self.controller.request_export_mode(export_config)
        self.assertTrue(success)
        
        # Vérification que config est sauvegardée
        self.assertTrue(hasattr(self.controller, '_saved_configuration'))
        
        # Retour vers EXPLORATION
        self.controller.return_to_exploration()
        
        # Vérification restauration
        restored_config = self.controller.get_current_configuration()
        self.assertEqual(restored_config['gain_dds'], initial_config['gain_dds'])
        self.assertEqual(restored_config['freq_hz'], initial_config['freq_hz'])
        self.assertEqual(restored_config['n_avg'], initial_config['n_avg'])
        
        print("✅ Sauvegarde/restauration config : OK")
    
    def test_10_hash_configuration_tracabilite(self):
        """Test hash configuration pour traçabilité [1/10]"""
        # Test même configuration → même hash
        config1 = {'gain_dds': 5000, 'freq_hz': 1000.0, 'n_avg': 10}
        config2 = {'gain_dds': 5000, 'freq_hz': 1000.0, 'n_avg': 10}
        
        hash1 = self.controller.get_configuration_hash(config1)
        hash2 = self.controller.get_configuration_hash(config2)
        
        self.assertEqual(hash1, hash2, "Même config doit donner même hash")
        self.assertIsInstance(hash1, str, "Hash doit être string")
        self.assertEqual(len(hash1), 32, "Hash MD5 doit faire 32 caractères")
        
        # Test configurations différentes → hash différents
        config3 = {'gain_dds': 6000, 'freq_hz': 1000.0, 'n_avg': 10}
        hash3 = self.controller.get_configuration_hash(config3)
        
        self.assertNotEqual(hash1, hash3, "Configs différentes doivent donner hash différents")
        
        print("✅ Hash configuration traçabilité : OK")


def run_mode_controller_tests():
    """Lance les tests unitaires ModeController"""
    print("🎯 === TESTS NIVEAU 2 : ModeController ===")
    print("⏱️  Durée estimée : 3 minutes")
    print("🔧 Objectif : Validation isolée gestion des modes\n")
    
    # Configuration du test runner
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestModeController)
    
    # Exécution avec verbosité
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Rapport final
    print(f"\n📊 === RÉSULTATS ModeController ===")
    print(f"Tests exécutés : {result.testsRun}")
    print(f"Succès : {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Échecs : {len(result.failures)}")
    print(f"Erreurs : {len(result.errors)}")
    
    if result.failures:
        print("\n❌ ÉCHECS :")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\n🚨 ERREURS :")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    if success:
        print("\n🎉 ModeController : TOUS LES TESTS PASSENT !")
    else:
        print("\n⚠️  ModeController : ÉCHECS DÉTECTÉS")
    
    return success


if __name__ == "__main__":
    # Exécution directe
    success = run_mode_controller_tests()
    sys.exit(0 if success else 1) 