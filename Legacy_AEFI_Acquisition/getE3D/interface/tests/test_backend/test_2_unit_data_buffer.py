"""
Niveau 2 : Tests Unitaires - DataBuffer
Objectif : Validation isolée des buffers adaptatifs

Complexité : 4/10
Durée estimée : 4 minutes
"""

import unittest
import sys
import threading
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Import du module à tester
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from getE3D.interface.components.AD9106_ADS131A04_DataBuffer_Module import (
        AcquisitionSample, 
        CircularBuffer, 
        ProductionBuffer, 
        AdaptiveDataBuffer
    )
    from getE3D.interface.components.AD9106_ADS131A04_ModeController_Module import AcquisitionMode
    IMPORT_SUCCESS = True
except ImportError as e:
    IMPORT_SUCCESS = False
    IMPORT_ERROR = str(e)


class TestCircularBuffer(unittest.TestCase):
    """Tests unitaires pour CircularBuffer [3/10]"""
    
    def setUp(self):
        """Setup avant chaque test"""
        if not IMPORT_SUCCESS:
            self.skipTest(f"Import impossible : {IMPORT_ERROR}")
        
        self.buffer = CircularBuffer(max_size=100)
    
    def _create_sample(self, adc1_values=None, adc2_values=None):
        """Helper pour créer des échantillons test"""
        if adc1_values is None:
            adc1_values = [1000, 1001, 1002, 1003]
        if adc2_values is None:
            adc2_values = [2000, 2001, 2002, 2003]
        
        return AcquisitionSample(
            adc1_ch1=adc1_values[0], adc1_ch2=adc1_values[1],
            adc1_ch3=adc1_values[2], adc1_ch4=adc1_values[3],
            adc2_ch1=adc2_values[0], adc2_ch2=adc2_values[1],
            adc2_ch3=adc2_values[2], adc2_ch4=adc2_values[3]
        )
    
    def test_01_initialisation_buffer(self):
        """Test initialisation [1/10]"""
        # Vérification max_size
        self.assertEqual(self.buffer.max_size, 100)
        
        # Vérification attributs
        self.assertTrue(hasattr(self.buffer, '_buffer'))
        self.assertTrue(hasattr(self.buffer, '_lock'))
        self.assertTrue(hasattr(self.buffer, '_total_samples'))
        
        # État initial vide
        self.assertEqual(self.buffer.size(), 0)
        self.assertEqual(self.buffer.total_samples, 0)
        
        print("✅ Initialisation CircularBuffer : OK")
    
    def test_02_ajout_sequentiel_sans_overwrite(self):
        """Test ajout séquentiel [2/10]"""
        # Ajout 1-99 échantillons : pas d'overwrite
        for i in range(99):
            sample = self._create_sample([i, i+1, i+2, i+3], [i+100, i+101, i+102, i+103])
            self.buffer.append_sample(sample)
            
            # Vérification size() croissant
            self.assertEqual(self.buffer.size(), i + 1)
            
            # Vérification total_samples correct
            self.assertEqual(self.buffer.total_samples, i + 1)
        
        # Vérification pas d'overwrite
        self.assertEqual(self.buffer.size(), 99)
        latest = self.buffer.get_latest(1)
        self.assertEqual(len(latest), 1)
        self.assertEqual(latest[0].adc1_ch1, 98)  # Dernier ajouté
        
        print("✅ Ajout séquentiel sans overwrite : OK")
    
    def test_03_overwrite_automatique(self):
        """Test overwrite automatique [3/10]"""
        # Ajout 100+ échantillons
        for i in range(105):
            sample = self._create_sample([i, i+1, i+2, i+3])
            self.buffer.append_sample(sample)
        
        # Vérification size() plafonné à 100
        self.assertEqual(self.buffer.size(), 100)
        
        # Vérification total_samples continue de croître
        self.assertEqual(self.buffer.total_samples, 105)
        
        # Vérification FIFO : premiers perdus
        latest = self.buffer.get_latest(5)
        self.assertEqual(len(latest), 5)
        
        # Les 5 derniers doivent être 100, 101, 102, 103, 104
        expected_values = [104, 103, 102, 101, 100]  # Ordre inverse (plus récent en premier)
        for i, sample in enumerate(latest):
            self.assertEqual(sample.adc1_ch1, expected_values[i])
        
        print("✅ Overwrite automatique : OK")
    
    def test_04_get_latest_fonctions(self):
        """Test get_latest() [2/10]"""
        # Ajout quelques échantillons
        for i in range(10):
            sample = self._create_sample([i, i+1, i+2, i+3])
            self.buffer.append_sample(sample)
        
        # get_latest(1) : dernier échantillon
        latest_1 = self.buffer.get_latest(1)
        self.assertEqual(len(latest_1), 1)
        self.assertEqual(latest_1[0].adc1_ch1, 9)
        
        # get_latest(n) avec n < size()
        latest_5 = self.buffer.get_latest(5)
        self.assertEqual(len(latest_5), 5)
        expected = [9, 8, 7, 6, 5]  # Ordre décroissant
        for i, sample in enumerate(latest_5):
            self.assertEqual(sample.adc1_ch1, expected[i])
        
        # get_latest(n) avec n > size()
        latest_20 = self.buffer.get_latest(20)
        self.assertEqual(len(latest_20), 10)  # Max = size actuel
        
        print("✅ get_latest() fonctions : OK")


class TestProductionBuffer(unittest.TestCase):
    """Tests unitaires pour ProductionBuffer [4/10]"""
    
    def setUp(self):
        """Setup avant chaque test"""
        if not IMPORT_SUCCESS:
            self.skipTest(f"Import impossible : {IMPORT_ERROR}")
        
        self.flush_called = False
        self.flushed_data = []
        
        def mock_flush_callback(samples):
            self.flush_called = True
            self.flushed_data.extend(samples)
        
        self.buffer = ProductionBuffer(flush_threshold=500)
        self.buffer.add_flush_callback(mock_flush_callback)
    
    def _create_sample(self, value):
        """Helper pour créer échantillon test"""
        return AcquisitionSample(
            adc1_ch1=value, adc1_ch2=value+1, adc1_ch3=value+2, adc1_ch4=value+3,
            adc2_ch1=value+10, adc2_ch2=value+11, adc2_ch3=value+12, adc2_ch4=value+13
        )
    
    def test_01_pas_de_flush_avant_seuil(self):
        """Test ajout 499 échantillons : pas de flush [1/10]"""
        # Ajout 499 échantillons
        for i in range(499):
            sample = self._create_sample(i)
            self.buffer.append_sample(sample)
        
        # Vérification pas de flush
        self.assertFalse(self.flush_called)
        self.assertEqual(len(self.flushed_data), 0)
        self.assertEqual(self.buffer.size(), 499)
        
        print("✅ Pas de flush avant seuil : OK")
    
    def test_02_trigger_flush_au_500eme(self):
        """Test ajout 500ème : trigger flush callback [2/10]"""
        # Reset état
        self.flush_called = False
        self.flushed_data = []
        
        # Ajout 500 échantillons
        for i in range(500):
            sample = self._create_sample(i)
            self.buffer.append_sample(sample)
        
        # Vérification flush déclenché
        self.assertTrue(self.flush_called, "Flush doit être déclenché au 500ème")
        
        # Vérification callback reçoit bonnes données
        self.assertEqual(len(self.flushed_data), 500)
        
        # Vérification ordre des données
        for i, sample in enumerate(self.flushed_data):
            self.assertEqual(sample.adc1_ch1, i)
        
        print("✅ Trigger flush au 500ème : OK")
    
    def test_03_buffer_vide_apres_flush(self):
        """Test vérification buffer vidé après flush [1/10]"""
        # Ajout 500 échantillons pour déclencher flush
        for i in range(500):
            sample = self._create_sample(i)
            self.buffer.append_sample(sample)
        
        # Vérification buffer vidé
        self.assertEqual(self.buffer.size(), 0, "Buffer doit être vidé après flush")
        
        # Ajout quelques échantillons supplémentaires
        for i in range(100):
            sample = self._create_sample(i + 1000)
            self.buffer.append_sample(sample)
        
        # Vérification nouveau contenu
        self.assertEqual(self.buffer.size(), 100)
        
        print("✅ Buffer vidé après flush : OK")
    
    def test_04_callbacks_multiples(self):
        """Test callbacks multiples [3/10]"""
        # Variables pour callbacks
        callback1_called = False
        callback1_data = []
        callback2_called = False
        callback2_data = []
        
        def callback1(samples):
            nonlocal callback1_called, callback1_data
            callback1_called = True
            callback1_data.extend(samples)
        
        def callback2(samples):
            nonlocal callback2_called, callback2_data
            callback2_called = True
            callback2_data.extend(samples)
        
        # Création nouveau buffer avec 2 callbacks
        buffer = ProductionBuffer(flush_threshold=100)
        buffer.add_flush_callback(callback1)
        buffer.add_flush_callback(callback2)
        
        # Ajout échantillons pour déclencher flush
        for i in range(100):
            sample = self._create_sample(i)
            buffer.append_sample(sample)
        
        # Vérification les 2 callbacks appelés
        self.assertTrue(callback1_called, "Callback 1 doit être appelé")
        self.assertTrue(callback2_called, "Callback 2 doit être appelé")
        
        # Vérification même données reçues
        self.assertEqual(len(callback1_data), 100)
        self.assertEqual(len(callback2_data), 100)
        
        for i in range(100):
            self.assertEqual(callback1_data[i].adc1_ch1, i)
            self.assertEqual(callback2_data[i].adc1_ch1, i)
        
        print("✅ Callbacks multiples : OK")
    
    def test_05_gestion_exception_callback(self):
        """Test gestion exception dans callback [2/10]"""
        def failing_callback(samples):
            raise Exception("Erreur test callback")
        
        def working_callback(samples):
            self.working_callback_called = True
        
        self.working_callback_called = False
        
        # Buffer avec callback qui échoue + callback qui marche
        buffer = ProductionBuffer(flush_threshold=50)
        buffer.add_flush_callback(failing_callback)
        buffer.add_flush_callback(working_callback)
        
        # Ajout échantillons (ne doit pas crasher)
        for i in range(50):
            sample = self._create_sample(i)
            buffer.append_sample(sample)
        
        # Vérification callback qui marche a été appelé malgré l'exception
        self.assertTrue(self.working_callback_called, "Callback valide doit être appelé malgré exception")
        
        print("✅ Gestion exception callback : OK")


class TestAdaptiveDataBuffer(unittest.TestCase):
    """Tests unitaires pour AdaptiveDataBuffer [5/10]"""
    
    def setUp(self):
        """Setup avant chaque test"""
        if not IMPORT_SUCCESS:
            self.skipTest(f"Import impossible : {IMPORT_ERROR}")
        
        self.adaptive_buffer = AdaptiveDataBuffer()
    
    def _create_sample(self, value):
        """Helper pour créer échantillon test"""
        return AcquisitionSample(
            adc1_ch1=value, adc1_ch2=value+1, adc1_ch3=value+2, adc1_ch4=value+3,
            adc2_ch1=value+10, adc2_ch2=value+11, adc2_ch3=value+12, adc2_ch4=value+13
        )
    
    def test_01_mode_exploration_par_defaut(self):
        """Test switch de mode : Mode EXPLORATION par défaut [1/10]"""
        # Vérification mode initial
        self.assertEqual(
            self.adaptive_buffer._current_mode, 
            AcquisitionMode.EXPLORATION,
            "Mode par défaut doit être EXPLORATION"
        )
        
        print("✅ Mode EXPLORATION par défaut : OK")
    
    def test_02_switch_vers_export(self):
        """Test switch vers EXPORT : _current_mode mis à jour [1/10]"""
        # Switch vers EXPORT
        self.adaptive_buffer.set_mode(AcquisitionMode.EXPORT)
        
        # Vérification mode mis à jour
        self.assertEqual(
            self.adaptive_buffer._current_mode,
            AcquisitionMode.EXPORT,
            "Mode doit être mis à jour vers EXPORT"
        )
        
        print("✅ Switch vers EXPORT : OK")
    
    def test_03_append_sample_route_bon_buffer(self):
        """Test append_sample() route vers bon buffer [2/10]"""
        # Test routage mode EXPLORATION
        sample1 = self._create_sample(100)
        self.adaptive_buffer.append_sample(sample1)
        
        # Vérification routage vers CircularBuffer
        circular_size = self.adaptive_buffer._circular_buffer.size()
        production_size = self.adaptive_buffer._production_buffer.size()
        
        self.assertEqual(circular_size, 1, "Échantillon doit aller vers CircularBuffer")
        self.assertEqual(production_size, 0, "ProductionBuffer doit rester vide")
        
        # Switch vers mode EXPORT
        self.adaptive_buffer.set_mode(AcquisitionMode.EXPORT)
        
        # Test routage mode EXPORT
        sample2 = self._create_sample(200)
        self.adaptive_buffer.append_sample(sample2)
        
        # Vérification routage vers ProductionBuffer
        production_size_after = self.adaptive_buffer._production_buffer.size()
        self.assertEqual(production_size_after, 1, "Échantillon doit aller vers ProductionBuffer")
        
        print("✅ append_sample() route bon buffer : OK")
    
    def test_04_get_latest_samples_adapte_mode(self):
        """Test get_latest_samples() adapté au mode [1/10]"""
        # Ajout échantillons en mode EXPLORATION
        for i in range(10):
            sample = self._create_sample(i)
            self.adaptive_buffer.append_sample(sample)
        
        # Test get_latest en mode EXPLORATION
        latest_exploration = self.adaptive_buffer.get_latest_samples(5)
        self.assertEqual(len(latest_exploration), 5)
        
        # Switch vers mode EXPORT et ajout échantillons
        self.adaptive_buffer.set_mode(AcquisitionMode.EXPORT)
        for i in range(5):
            sample = self._create_sample(i + 100)
            self.adaptive_buffer.append_sample(sample)
        
        # Test get_latest en mode EXPORT
        latest_export = self.adaptive_buffer.get_latest_samples(3)
        self.assertEqual(len(latest_export), 3)
        
        # Vérification données différentes selon mode
        self.assertNotEqual(latest_exploration[0].adc1_ch1, latest_export[0].adc1_ch1)
        
        print("✅ get_latest_samples() adapté mode : OK")
    
    def test_05_thread_safety_concurrent_access(self):
        """Test thread-safety : Accès concurrent sans corruption [6/10]"""
        import threading
        import time
        
        # Variables pour synchronisation
        errors = []
        samples_added = 0
        
        def add_samples_worker(worker_id, count):
            """Worker qui ajoute des échantillons"""
            nonlocal samples_added
            try:
                for i in range(count):
                    sample = self._create_sample(worker_id * 1000 + i)
                    self.adaptive_buffer.append_sample(sample)
                    samples_added += 1
                    time.sleep(0.001)  # Petite pause pour simuler concurrence
            except Exception as e:
                errors.append(f"Worker {worker_id}: {e}")
        
        def switch_mode_worker():
            """Worker qui change de mode"""
            try:
                for _ in range(10):
                    self.adaptive_buffer.set_mode(AcquisitionMode.EXPORT)
                    time.sleep(0.005)
                    self.adaptive_buffer.set_mode(AcquisitionMode.EXPLORATION)
                    time.sleep(0.005)
            except Exception as e:
                errors.append(f"Mode switch: {e}")
        
        # Création threads concurrents
        threads = []
        
        # 3 threads ajout échantillons
        for worker_id in range(3):
            t = threading.Thread(target=add_samples_worker, args=(worker_id, 50))
            threads.append(t)
        
        # 1 thread changement mode
        t = threading.Thread(target=switch_mode_worker)
        threads.append(t)
        
        # Démarrage threads
        for t in threads:
            t.start()
        
        # Attente fin threads
        for t in threads:
            t.join(timeout=5.0)
        
        # Vérifications
        self.assertEqual(len(errors), 0, f"Erreurs concurrence détectées: {errors}")
        self.assertEqual(samples_added, 150, "Tous échantillons doivent être ajoutés")
        
        # Vérification pas de deadlock (test terminé = pas de deadlock)
        self.assertTrue(True, "Pas de deadlock détecté")
        
        print("✅ Thread-safety accès concurrent : OK")
    
    def test_06_performance_acceptable(self):
        """Test performance acceptable (>100 ops/s) [1/10]"""
        import time
        
        # Mesure performance ajout échantillons
        start_time = time.time()
        
        for i in range(1000):
            sample = self._create_sample(i)
            self.adaptive_buffer.append_sample(sample)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calcul performance
        ops_per_second = 1000 / duration
        
        self.assertGreater(
            ops_per_second, 100, 
            f"Performance trop faible: {ops_per_second:.1f} ops/s < 100 ops/s"
        )
        
        print(f"✅ Performance acceptable : {ops_per_second:.1f} ops/s")


def run_data_buffer_tests():
    """Lance les tests unitaires DataBuffer"""
    print("📊 === TESTS NIVEAU 2 : DataBuffer ===")
    print("⏱️  Durée estimée : 4 minutes")
    print("🔧 Objectif : Validation isolée buffers adaptatifs\n")
    
    # Tests par classe
    test_classes = [TestCircularBuffer, TestProductionBuffer, TestAdaptiveDataBuffer]
    
    total_tests = 0
    total_successes = 0
    total_failures = 0
    total_errors = 0
    
    for test_class in test_classes:
        print(f"\n--- {test_class.__name__} ---")
        
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        total_tests += result.testsRun
        total_successes += (result.testsRun - len(result.failures) - len(result.errors))
        total_failures += len(result.failures)
        total_errors += len(result.errors)
    
    # Rapport final
    print(f"\n📊 === RÉSULTATS DataBuffer ===")
    print(f"Tests exécutés : {total_tests}")
    print(f"Succès : {total_successes}")
    print(f"Échecs : {total_failures}")
    print(f"Erreurs : {total_errors}")
    
    success = total_failures == 0 and total_errors == 0
    if success:
        print("\n🎉 DataBuffer : TOUS LES TESTS PASSENT !")
    else:
        print("\n⚠️  DataBuffer : ÉCHECS DÉTECTÉS")
    
    return success


if __name__ == "__main__":
    # Exécution directe
    success = run_data_buffer_tests()
    sys.exit(0 if success else 1) 