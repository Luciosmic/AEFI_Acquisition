import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtCore import QCoreApplication, QTimer

"""
Test d'intégration simulée backend (niveau 3)
Chaîne complète : AcquisitionManager + MockSerialCommunicator + DataBuffer
"""
import unittest
import time
from threading import Event

from getE3D.interface.components.AD9106_ADS131A04_acquisition_manager import AcquisitionManager, AcquisitionStatus
from getE3D.interface.components.AD9106_ADS131A04_DataBuffer_Module import AdaptiveDataBuffer, AcquisitionSample
from getE3D.interface.components.AD9106_ADS131A04_ModeController_Module import AcquisitionMode
from tests.mock_serial_communicator import MockSerialCommunicator

class TestIntegrationSimulated(unittest.TestCase):
    def setUp(self):
        if QCoreApplication.instance() is None:
            self._app = QCoreApplication(sys.argv)
        else:
            self._app = QCoreApplication.instance()
        self.mock_serial = MockSerialCommunicator()
        self.data_buffer = AdaptiveDataBuffer()
        self.mode = AcquisitionMode.EXPLORATION
        self.manager = AcquisitionManager(
            serial_communicator=self.mock_serial,
            data_buffer=self.data_buffer,
            mode_controller=None  # Pas de GUI pour ce test
        )
        self.manager.set_mode(self.mode)
        self.data_ready_event = Event()
        def on_data_ready(*_):
            print("[DEBUG TEST] Signal data_ready reçu (event set)")
            self.data_ready_event.set()
        self.manager.data_ready.connect(on_data_ready)

    def tearDown(self):
        self.manager.stop_acquisition()
        time.sleep(0.1)

    def wait_for_signal(self, event, timeout=1000):
        """Attend qu'un event soit set, en laissant Qt traiter les signaux."""
        timer = QTimer()
        timer.setSingleShot(True)
        timer.start(timeout)
        while not event.is_set() and timer.isActive():
            self._app.processEvents()
            time.sleep(0.01)
        return event.is_set()

    def test_acquisition_exploration(self):
        """Test acquisition en mode EXPLORATION avec mock"""
        config = {"gain_dds": 5000, "freq_hz": 500, "n_avg": 10}
        print(f"[DEBUG TEST] Status avant start: {self.manager.status}")
        self.manager.start_acquisition(self.mode, config)
        print(f"[DEBUG TEST] Status après start: {self.manager.status}")
        # Attendre qu'au moins un échantillon arrive (boucle Qt)
        self.assertTrue(self.wait_for_signal(self.data_ready_event, timeout=1000))
        # Vérifier que le buffer contient des données
        samples = self.data_buffer.get_latest_samples(1)
        print(f"[DEBUG TEST] Nb samples dans buffer: {len(samples)}")
        self.assertTrue(len(samples) > 0)
        self.assertIsInstance(samples[0], AcquisitionSample)
        self.assertEqual(self.data_buffer.current_mode, AcquisitionMode.EXPLORATION)
        self.assertEqual(self.manager.status, AcquisitionStatus.RUNNING)

if __name__ == "__main__":
    unittest.main() 