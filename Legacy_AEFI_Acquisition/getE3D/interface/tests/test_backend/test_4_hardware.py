"""
Test hardware niveau 4 - Backend AD9106/ADS131A04
Conforme à la todo Backend_Testing_Strategy_tasks.md
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

import unittest
import time
import serial.tools.list_ports
from PyQt5.QtCore import QCoreApplication, QTimer
from threading import Event

from getE3D.instruments.AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator
from getE3D.interface.components.AD9106_ADS131A04_acquisition_manager import AcquisitionManager, AcquisitionStatus
from getE3D.interface.components.AD9106_ADS131A04_DataBuffer_Module import AdaptiveDataBuffer, AcquisitionSample
from getE3D.interface.components.AD9106_ADS131A04_ModeController_Module import AcquisitionMode

class TestHardwareIntegrationBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Forcer le port série à COM10 (adapter si besoin)
        cls.port = "COM10"
        cls.serial = SerialCommunicator(port=cls.port)
        success, msg = cls.serial.connect(cls.port)
        if not success:
            raise unittest.SkipTest(f"Connexion série impossible : {msg}")
        print(f"[HARDWARE] Connecté à {cls.port}")

    @classmethod
    def tearDownClass(cls):
        cls.serial.disconnect()
        print("[HARDWARE] Connexion série fermée")

    def setUp(self):
        if QCoreApplication.instance() is None:
            self._app = QCoreApplication(sys.argv)
        else:
            self._app = QCoreApplication.instance()
        self.data_buffer = AdaptiveDataBuffer()
        self.manager = AcquisitionManager(
            serial_communicator=self.serial,
            data_buffer=self.data_buffer,
            mode_controller=None
        )
        self.manager.set_mode(AcquisitionMode.EXPLORATION)
        self.data_ready_event = Event()
        self.samples_received = []
        def on_data_ready(sample):
            self.samples_received.append(sample)
            self.data_ready_event.set()
        self.manager.data_ready.connect(on_data_ready)

    def tearDown(self):
        self.manager.stop_acquisition()
        time.sleep(0.2)

    def wait_for_signal(self, event, timeout=2000):
        timer = QTimer()
        timer.setSingleShot(True)
        timer.start(timeout)
        while not event.is_set() and timer.isActive():
            self._app.processEvents()
            time.sleep(0.01)
        return event.is_set()

    def test_acquisition_throughput_stable(self):
        """Test de débit d'acquisition sans changement de paramètres"""
        print("\n[HARDWARE] === TEST DE DÉBIT STABLE (SANS CHANGEMENT) ===")
        
        # Test avec moyennage 1 (acquisition rapide)
        print("[HARDWARE] Test débit stable - Moyennage 1")
        config_m1 = {"gain_dds": 5000, "freq_hz": 1000, "n_avg": 1}
        
        self.data_ready_event.clear()
        self.samples_received.clear()
        
        start_time = time.time()
        self.manager.start_acquisition(AcquisitionMode.EXPLORATION, config_m1)
        
        # Acquérir 50 samples pour mesurer le débit
        target_samples = 50
        while len(self.samples_received) < target_samples:
            if not self.wait_for_signal(self.data_ready_event, timeout=5000):
                break
            self.data_ready_event.clear()
        
        end_time = time.time()
        duration_m1 = end_time - start_time
        samples_m1 = len(self.samples_received)
        throughput_m1 = samples_m1 / duration_m1 if duration_m1 > 0 else 0
        
        print(f"[HARDWARE] Moyennage 1 stable: {samples_m1} samples en {duration_m1:.3f}s = {throughput_m1:.1f} Hz")
        
        self.manager.stop_acquisition()
        time.sleep(0.5)
        
        # Test avec moyennage 127 (acquisition lente)
        print("[HARDWARE] Test débit stable - Moyennage 127")
        config_m127 = {"gain_dds": 5000, "freq_hz": 1000, "n_avg": 127}
        
        self.data_ready_event.clear()
        self.samples_received.clear()
        
        start_time = time.time()
        self.manager.start_acquisition(AcquisitionMode.EXPLORATION, config_m127)
        
        # Acquérir 10 samples pour mesurer le débit (plus lent avec moyennage 127)
        target_samples = 10
        while len(self.samples_received) < target_samples:
            if not self.wait_for_signal(self.data_ready_event, timeout=10000):
                break
            self.data_ready_event.clear()
        
        end_time = time.time()
        duration_m127 = end_time - start_time
        samples_m127 = len(self.samples_received)
        throughput_m127 = samples_m127 / duration_m127 if duration_m127 > 0 else 0
        
        print(f"[HARDWARE] Moyennage 127 stable: {samples_m127} samples en {duration_m127:.3f}s = {throughput_m127:.1f} Hz")
        
        self.manager.stop_acquisition()
        
        # Résultats et validation
        print(f"\n[HARDWARE] === RÉSULTATS DÉBIT STABLE ===")
        print(f"[HARDWARE] Débit moyennage 1 stable: {throughput_m1:.1f} Hz")
        print(f"[HARDWARE] Débit moyennage 127 stable: {throughput_m127:.1f} Hz")
        print(f"[HARDWARE] Ratio de performance: {throughput_m1/throughput_m127:.1f}x plus rapide avec moyennage 1")
        
        # Validation des performances minimales
        self.assertGreater(throughput_m1, 10, f"Débit moyennage 1 stable trop faible: {throughput_m1:.1f} Hz")
        self.assertGreater(throughput_m127, 0.5, f"Débit moyennage 127 stable trop faible: {throughput_m127:.1f} Hz")
        self.assertGreater(throughput_m1, throughput_m127, "Le moyennage 1 devrait être plus rapide que 127")
        
        print("[HARDWARE] Test de débit stable réussi !")

    def test_acquisition_throughput_with_param_change(self):
        """Test de débit d'acquisition avec changement de paramètres"""
        print("\n[HARDWARE] === TEST DE DÉBIT AVEC CHANGEMENT DE PARAMÈTRES ===")
        
        # Test avec moyennage 1 + changement de fréquence
        print("[HARDWARE] Test débit avec changement - Moyennage 1")
        config_m1 = {"gain_dds": 5000, "freq_hz": 1000, "n_avg": 1}
        
        self.data_ready_event.clear()
        self.samples_received.clear()
        
        start_time = time.time()
        self.manager.start_acquisition(AcquisitionMode.EXPLORATION, config_m1)
        
        # Acquérir 25 samples avant changement
        target_samples_before = 25
        while len(self.samples_received) < target_samples_before:
            if not self.wait_for_signal(self.data_ready_event, timeout=5000):
                break
            self.data_ready_event.clear()
        
        # Changement de paramètre
        print("[HARDWARE] Changement de fréquence à 2000 Hz...")
        self.manager.update_configuration({"freq_hz": 2000})
        
        # Acquérir 25 samples après changement
        target_samples_after = 25
        while len(self.samples_received) < (target_samples_before + target_samples_after):
            if not self.wait_for_signal(self.data_ready_event, timeout=5000):
                break
            self.data_ready_event.clear()
        
        end_time = time.time()
        duration_m1 = end_time - start_time
        samples_m1 = len(self.samples_received)
        throughput_m1 = samples_m1 / duration_m1 if duration_m1 > 0 else 0
        
        print(f"[HARDWARE] Moyennage 1 avec changement: {samples_m1} samples en {duration_m1:.3f}s = {throughput_m1:.1f} Hz")
        
        self.manager.stop_acquisition()
        time.sleep(0.5)
        
        # Test avec moyennage 127 + changement de fréquence
        print("[HARDWARE] Test débit avec changement - Moyennage 127")
        config_m127 = {"gain_dds": 5000, "freq_hz": 1000, "n_avg": 127}
        
        self.data_ready_event.clear()
        self.samples_received.clear()
        
        start_time = time.time()
        self.manager.start_acquisition(AcquisitionMode.EXPLORATION, config_m127)
        
        # Acquérir 5 samples avant changement
        target_samples_before = 5
        while len(self.samples_received) < target_samples_before:
            if not self.wait_for_signal(self.data_ready_event, timeout=10000):
                break
            self.data_ready_event.clear()
        
        # Changement de paramètre
        print("[HARDWARE] Changement de fréquence à 2000 Hz...")
        self.manager.update_configuration({"freq_hz": 2000})
        
        # Acquérir 5 samples après changement
        target_samples_after = 5
        while len(self.samples_received) < (target_samples_before + target_samples_after):
            if not self.wait_for_signal(self.data_ready_event, timeout=10000):
                break
            self.data_ready_event.clear()
        
        end_time = time.time()
        duration_m127 = end_time - start_time
        samples_m127 = len(self.samples_received)
        throughput_m127 = samples_m127 / duration_m127 if duration_m127 > 0 else 0
        
        print(f"[HARDWARE] Moyennage 127 avec changement: {samples_m127} samples en {duration_m127:.3f}s = {throughput_m127:.1f} Hz")
        
        self.manager.stop_acquisition()
        
        # Résultats et validation
        print(f"\n[HARDWARE] === RÉSULTATS DÉBIT AVEC CHANGEMENT ===")
        print(f"[HARDWARE] Débit moyennage 1 avec changement: {throughput_m1:.1f} Hz")
        print(f"[HARDWARE] Débit moyennage 127 avec changement: {throughput_m127:.1f} Hz")
        print(f"[HARDWARE] Ratio de performance: {throughput_m1/throughput_m127:.1f}x plus rapide avec moyennage 1")
        
        # Validation des performances minimales
        self.assertGreater(throughput_m1, 8, f"Débit moyennage 1 avec changement trop faible: {throughput_m1:.1f} Hz")
        self.assertGreater(throughput_m127, 0.3, f"Débit moyennage 127 avec changement trop faible: {throughput_m127:.1f} Hz")
        self.assertGreater(throughput_m1, throughput_m127, "Le moyennage 1 devrait être plus rapide que 127")
        
        print("[HARDWARE] Test de débit avec changement réussi !")

    def test_acquisition_and_param_change(self):
        """Test acquisition réelle + changement de paramètres à chaud"""
        config = {"gain_dds": 5000, "freq_hz": 1000, "n_avg": 10}
        print("[HARDWARE] Démarrage acquisition...")
        self.manager.start_acquisition(AcquisitionMode.EXPLORATION, config)
        # Attendre quelques samples
        self.data_ready_event.clear()
        self.samples_received.clear()
        self.assertTrue(self.wait_for_signal(self.data_ready_event, timeout=2000))
        print(f"[HARDWARE] {len(self.samples_received)} sample(s) acquis avant changement paramètre.")
        # Changer la fréquence DDS à chaud
        new_freq = 2000
        print(f"[HARDWARE] Changement de fréquence DDS à {new_freq} Hz...")
        self.manager.update_configuration({"freq_hz": new_freq})
        # Attendre à nouveau des samples
        self.data_ready_event.clear()
        self.samples_received.clear()
        self.assertTrue(self.wait_for_signal(self.data_ready_event, timeout=2000))
        print(f"[HARDWARE] {len(self.samples_received)} sample(s) acquis après changement paramètre.")
        # Vérifier que l'acquisition continue
        self.assertTrue(self.manager.status == AcquisitionStatus.RUNNING)
        self.assertTrue(len(self.samples_received) > 0)

if __name__ == "__main__":
    unittest.main() 