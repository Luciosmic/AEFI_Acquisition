import unittest
import time
import csv
import os
from pathlib import Path
import sys
from PyQt5.QtCore import QCoreApplication, QTimer
from threading import Event

# Ajoute getE3D/ et getE3D/interface/ au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent))         # getE3D/
sys.path.insert(0, str(Path(__file__).parent.parent))                # getE3D/interface/

from instruments.AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator
from getE3D.interface.components.AD9106_ADS131A04_acquisition_manager import AcquisitionManager, AcquisitionStatus
from getE3D.interface.components.AD9106_ADS131A04_CSVexporter_Module import CSVExporter, ExportConfig
from getE3D.interface.components.AD9106_ADS131A04_DataBuffer_Module import AcquisitionSample
from getE3D.interface.components.AD9106_ADS131A04_ModeController_Module import AcquisitionMode

class TestHardwareCSVBenchmark(unittest.TestCase):
    """
    Test d'intégration hardware : benchmark export CSV et analyse du temps mort
    - Pour plusieurs valeurs de moyennage, mesure du débit effectif
    - Calcul du temps mort moyen entre deux acquisitions
    - Estimation du nombre d'opérations annexes réalisables
    """
    @classmethod
    def setUpClass(cls):
        # Force l'export dans le dossier du script de test
        cls.data_dir = Path(__file__).parent / "hardware_csv_benchmark_results"
        cls.data_dir.mkdir(exist_ok=True)
        cls.port = "COM10"  # Adapter si besoin
        cls.serial = SerialCommunicator(port=cls.port)
        success, msg = cls.serial.connect(cls.port)
        if not success:
            raise unittest.SkipTest(f"Connexion série impossible : {msg}")
        cls.manager = AcquisitionManager(
            serial_communicator=cls.serial,
            data_buffer=None,
            mode_controller=None
        )
        print(f"[BENCHMARK] Connecté à {cls.port}")
        
        # Initialiser QCoreApplication pour les signaux PyQt5
        if QCoreApplication.instance() is None:
            cls._app = QCoreApplication(sys.argv)
        else:
            cls._app = QCoreApplication.instance()

    @classmethod
    def tearDownClass(cls):
        cls.serial.disconnect()
        print("[BENCHMARK] Connexion série fermée")
        # Optionnel : suppression des fichiers générés
        # for f in cls.data_dir.glob("*.csv"):
        #     f.unlink()

    def measure_simple_operation_time(self, n_iter=1000):
        """Mesure le temps moyen d'une opération simple (addition)"""
        start = time.perf_counter()
        x = 0
        for _ in range(n_iter):
            x += 1  # Opération simple
        end = time.perf_counter()
        return (end - start) / n_iter
    
    def wait_for_signal(self, event, timeout=2000):
        """Attend un signal avec traitement des événements PyQt5"""
        timer = QTimer()
        timer.setSingleShot(True)
        timer.start(timeout)
        while not event.is_set() and timer.isActive():
            self._app.processEvents()
            time.sleep(0.01)
        return event.is_set()

    def test_benchmark_csv_export(self):
        moyennages = [1, 10, 50, 127]
        n_samples = 1000
        freq_hz = 1000
        gain_dds = 5000
        op_time = self.measure_simple_operation_time()
        print(f"[BENCHMARK] Temps moyen d'une opération simple : {op_time*1e6:.2f} us")

        for n_avg in moyennages:
            print(f"\n[TEST] Moyennage = {n_avg}")
            # 1. Configurer acquisition
            config = {"gain_dds": gain_dds, "freq_hz": freq_hz, "n_avg": n_avg}
            # 2. Démarrer CSVExporter
            filename_base = f"benchmark_navg{n_avg}"
            export_config = ExportConfig(
                output_dir=str(self.data_dir),
                filename_base=filename_base,
                duration_seconds=None,
                metadata={"gain_dds": gain_dds, "freq_hz": freq_hz, "n_avg": n_avg}
            )
            exporter = CSVExporter()
            started = exporter.start_export(export_config)
            self.assertTrue(started, "Échec démarrage CSVExporter")
            # 3. Connecter le signal AVANT de démarrer l'acquisition
            self.manager.set_mode(AcquisitionMode.EXPORT)
            samples_received = []
            data_ready_event = Event()
            def on_sample(sample):
                samples_received.append(sample)
                exporter.add_sample(sample)
                data_ready_event.set()
            self.manager.data_ready.connect(on_sample)
            # 4. Démarrer acquisition avec mesure du temps
            start_time = time.perf_counter()
            self.manager.start_acquisition(AcquisitionMode.EXPORT, config)
            # 5. Attendre N samples avec traitement des événements PyQt5
            timeout = 30  # secondes max
            t0 = time.time()
            while exporter.samples_written < n_samples and (time.time() - t0) < timeout:
                if not self.wait_for_signal(data_ready_event, timeout=1000):
                    break
                data_ready_event.clear()
            end_time = time.perf_counter()
            self.manager.stop_acquisition()
            time.sleep(0.5)
            exporter.stop_export()
            
            # Calcul du débit d'acquisition réel
            acquisition_duration = end_time - start_time
            acquisition_throughput = self.manager.samples_acquired / acquisition_duration if acquisition_duration > 0 else 0
            # 6. Lire CSV
            csv_files = sorted(self.data_dir.glob(f"*{filename_base}*.csv"), key=os.path.getmtime)
            self.assertTrue(len(csv_files) > 0, "Aucun fichier CSV généré")
            csv_path = csv_files[-1]
            print(f"[INFO] Fichier CSV généré : {csv_path.resolve()}")
            # Lecture des index et timestamps relatifs
            indexes = []
            timestamps = []
            with open(csv_path, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and not row[0].startswith('#') and row[0] and row[0] != 'index':
                        try:
                            idx = int(row[0])
                            t_rel = float(row[1])
                            indexes.append(idx)
                            timestamps.append(t_rel)
                        except Exception:
                            continue
            # Vérification de la continuité de l'index
            if len(indexes) > 1:
                missing = [i for i, (a, b) in enumerate(zip(indexes[:-1], indexes[1:])) if b != a+1]
                if missing:
                    print(f"[WARN] Index non continus à la/aux position(s) : {missing}")
            # 7. Calculer débit effectif
            if len(timestamps) < 2:
                print(f"[WARN] Moyennage {n_avg} : pas assez de samples pour calculer le débit")
                continue
            delta_ts = [t2 - t1 for t1, t2 in zip(timestamps[:-1], timestamps[1:])]
            mean_dt = sum(delta_ts) / len(delta_ts)
            throughput = 1.0 / mean_dt if mean_dt > 0 else 0
            # 8. Calculer temps mort moyen
            nb_op_possible = mean_dt / op_time if op_time > 0 else 0

            # 9. Assertions sur le débit minimal
            if n_avg == 1:
                self.assertGreater(acquisition_throughput, 10, f"Débit acquisition trop faible pour n_avg=1 : {acquisition_throughput:.2f} Hz")
            if n_avg == 127:
                self.assertGreater(acquisition_throughput, 0.5, f"Débit acquisition trop faible pour n_avg=127 : {acquisition_throughput:.2f} Hz")
            
            print(f"[BENCHMARK] Moyennage {n_avg} : acquisition={acquisition_throughput:.1f} Hz, export={throughput:.1f} Hz, {mean_dt*1e3:.1f} ms, {nb_op_possible:.0f} op")

if __name__ == '__main__':
    unittest.main() 