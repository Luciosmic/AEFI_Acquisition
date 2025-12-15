#!/usr/bin/env python3
"""
Script de test simple pour le module d'export CSV avec double buffer
"""

import os
import sys
import random
from datetime import datetime

# Ajout des chemins d'import
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
sys.path.insert(0, project_root)

# Import des modules à tester
from EFImagingBench_App.src.core.AD9106_ADS131A04_ElectricField_3D.components.AD9106_ADS131A04_CSVexporter_Module import CSVExporter, ExportConfig
from EFImagingBench_App.src.core.AD9106_ADS131A04_ElectricField_3D.components.AD9106_ADS131A04_DataBuffer_Module import AcquisitionSample

def test_double_buffer():
    """Test simple du double buffer"""
    print("Test du double buffer...")
    
    # Créer l'exporteur
    exporter = CSVExporter()
    
    # Configurer l'export
    config = ExportConfig(
        output_dir=os.path.join(current_dir, "test_output"),
        filename_base="test",
        duration_seconds=None,
        metadata={"test": "double_buffer"},
        dataFormat_Labview=True
    )
    
    # Démarrer l'export
    exporter.start_export(config)
    print("Export démarré")
    
    # Envoyer quelques échantillons
    for i in range(1500):
        sample = AcquisitionSample(
            timestamp=datetime.now(),
            adc1_ch1=random.randint(-1000, 1000),
            adc1_ch2=random.randint(-1000, 1000),
            adc1_ch3=random.randint(-1000, 1000),
            adc1_ch4=random.randint(-1000, 1000),
            adc2_ch1=random.randint(-1000, 1000),
            adc2_ch2=random.randint(-1000, 1000),
            adc2_ch3=random.randint(-1000, 1000),
            adc2_ch4=random.randint(-1000, 1000)
        )
        exporter.add_sample(sample)
        if i % 100 == 0:
            print(f"Échantillon {i} envoyé")
    
    print("1500 échantillons envoyés")
    
    # Arrêter l'export
    exporter.stop_export()
    print("Export arrêté")
    print(f"Échantillons écrits: {exporter.samples_written}")

if __name__ == "__main__":
    test_double_buffer()
