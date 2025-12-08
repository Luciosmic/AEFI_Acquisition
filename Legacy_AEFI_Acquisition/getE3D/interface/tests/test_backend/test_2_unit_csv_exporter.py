import unittest
import tempfile
import shutil
import csv
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Ajoute getE3D/ et getE3D/interface/ au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # getE3D/
sys.path.insert(0, str(Path(__file__).parent.parent))         # getE3D/interface/

from getE3D.interface.components.AD9106_ADS131A04_CSVexporter_Module import CSVExporter, ExportConfig
from getE3D.interface.components.AD9106_ADS131A04_DataBuffer_Module import AcquisitionSample

class TestCSVExporterMinimal(unittest.TestCase):
    def setUp(self):
        # Crée un dossier temporaire pour les exports
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        # Supprime le dossier temporaire
        shutil.rmtree(self.temp_dir)

    def test_export_and_readback(self):
        exporter = CSVExporter()
        config = ExportConfig(
            output_dir=str(self.temp_dir),
            filename_base="unittest",
            duration_seconds=None,
            metadata={"test": True}
        )
        started = exporter.start_export(config)
        self.assertTrue(started, "Échec démarrage CSVExporter")
        # Ajoute 3 samples synthétiques
        t0 = datetime.now()
        samples = [
            AcquisitionSample(
                timestamp=t0 + timedelta(seconds=i),
                adc1_ch1=100+i, adc1_ch2=200+i, adc1_ch3=300+i, adc1_ch4=400+i,
                adc2_ch1=500+i, adc2_ch2=600+i, adc2_ch3=700+i, adc2_ch4=800+i
            ) for i in range(3)
        ]
        for s in samples:
            exporter.add_sample(s)
        exporter.stop_export()
        # Cherche le fichier CSV généré
        csv_files = list(self.temp_dir.glob("*.csv"))
        self.assertTrue(len(csv_files) > 0, "Aucun fichier CSV généré")
        csv_path = csv_files[0]
        # Relit le CSV et vérifie les données
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            data_rows = [row for row in reader if row and not row[0].startswith('#') and row[0] and row[0] != 'index']
            print("[DEBUG] Contenu brut du CSV :")
            f.seek(0)
            for line in f:
                print(line.strip())
        self.assertEqual(len(data_rows), 3, f"Le CSV doit contenir 3 lignes de données, trouvé {len(data_rows)}")
        # Vérifie le contenu de la première ligne
        first_row = data_rows[0]
        self.assertEqual(int(first_row[2]), 100)  # ADC1_Ch1
        self.assertEqual(int(first_row[6]), 500)  # ADC2_Ch1
        print(f"[UNITTEST] CSVExporter a bien écrit {len(data_rows)} lignes de données.")

if __name__ == '__main__':
    unittest.main() 