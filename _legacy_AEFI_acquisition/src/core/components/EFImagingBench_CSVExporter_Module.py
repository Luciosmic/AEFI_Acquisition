# Correction linter : Remplace // par #
# Nouveau fichier : src/core/EFImagingBench_CSVExporter_Module.py
# Inspiré de AD9106_ADS131A04_CSVexporter_Module.py et EFImagingBench_CSVexporter_Module.py

import csv
import os
import sys
import time
from datetime import datetime
from threading import Thread, Lock
from queue import Queue
from typing import List, Dict, Any
from dataclasses import dataclass
from pathlib import Path



# Assure l'import des types de données des buffers
# Remplace par les imports réels du metaManager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Correction des imports pour utiliser des chemins absolus
from core.AD9106_ADS131A04_ElectricField_3D.components.AD9106_ADS131A04_DataBuffer_Module import AcquisitionSample  # Pour capteur
from core.ArcusPerfomax4EXStage.components.ArcusPerfomax4EXStage_DataBuffer_Module import PositionSample  # Pour positions (assume nom)

@dataclass
class ExportConfig:
    output_dir: str  # Injecté par le MetaManager
    filename_base: str  # Injecté par le MetaManager (avec timestamp intégré)
    metadata: Dict[str, Any] = None
    filter_active_lines_only: bool = False  # Si True, n'exporte que les lignes de scan actives
    dataFormat_Labview: bool = False  # Si True, utilise le format rétrocompatible avec LabVIEW

class CSVSensorExporter:
    def __init__(self):
        self._export_queue = Queue()
        self._export_thread = None
        self._is_exporting = False
        self._export_lock = Lock()
        self._current_file = None
        self._csv_writer = None
        self._samples_written = 0
        self._sample_index = 0
        self._t0 = None
        self._current_segment_id = ""
        self._is_active_line = False
        self._filter_active_only = False
        self._dataFormat_Labview = False
        
        # Système de double buffer pour l'export
        self._buffer_A = []
        self._buffer_B = []
        self._active_buffer = "A"
        self._writing_buffer = None
        self._buffer_lock = Lock()
        self._batch_size = 1000
        
        # Compteur pour le format LabVIEW
        self._labview_sample_count = 0
        self._labview_batch_size = 1000  # Nombre d'échantillons à accumuler avant écriture

    def set_current_segment(self, segment_id: str, is_active_line: bool):
        """Met à jour le segment actuel pour marquer les échantillons"""
        self._current_segment_id = segment_id
        self._is_active_line = is_active_line
        print(f"[CSVSensorExporter] Segment changé: {segment_id}, active: {is_active_line}")

    def start_export(self, config: ExportConfig) -> bool:
        with self._export_lock:
            if self._is_exporting:
                return False
            self._filter_active_only = config.filter_active_lines_only
            self._dataFormat_Labview = config.dataFormat_Labview
            filename = f"{config.filename_base}_E_all.csv"
            filepath = Path(config.output_dir) / filename
            try:
                filepath.parent.mkdir(parents=True, exist_ok=True)
                self._current_file = open(filepath, 'w', newline='', encoding='utf-8')
                self._csv_writer = csv.writer(self._current_file)
                
                # Pas de métadonnées ni d'en-têtes en mode LabVIEW
                if not self._dataFormat_Labview:
                    self._write_metadata(config.metadata)
                
                # Initialiser les structures pour le format LabVIEW
                if self._dataFormat_Labview:
                    self._labview_sample_count = 0
                    # Initialiser les colonnes pour le format LabVIEW
                    self._labview_temps_x = []
                    self._labview_temps_y = []
                    self._labview_temps_z = []
                    self._labview_ex_imag = []
                    self._labview_ex_real = []
                    self._labview_ey_imag = []
                    self._labview_ey_real = []
                    self._labview_ez_imag = []
                    self._labview_ez_real = []
                    self._labview_scan_state = []
                
                self._is_exporting = True
                self._export_thread = Thread(target=self._export_worker)
                self._export_thread.start()
                return True
            except:
                if self._current_file:
                    self._current_file.close()
                return False

    def add_sample(self, sample: AcquisitionSample):
        if self._is_exporting:
            # Si filtrage actif et pas sur une ligne active, ignorer
            if self._filter_active_only and not self._is_active_line:
                return
            
            if self._t0 is None:
                self._t0 = time.perf_counter()
            t_rel = time.perf_counter() - self._t0
            
            # Utilisation du double buffer
            should_exchange = False
            with self._buffer_lock:
                if self._active_buffer == "A":
                    self._buffer_A.append((self._sample_index, t_rel, sample, self._current_segment_id, self._is_active_line))
                    if len(self._buffer_A) >= self._batch_size:
                        should_exchange = True
                else:
                    self._buffer_B.append((self._sample_index, t_rel, sample, self._current_segment_id, self._is_active_line))
                    if len(self._buffer_B) >= self._batch_size:
                        should_exchange = True
            
            # Échange des buffers en dehors du verrou (évite le deadlock)
            if should_exchange:
                self._exchange_buffers()
            
            self._sample_index += 1

    def stop_export(self) -> bool:
        print("stop_export: début")
        with self._export_lock:
            print("stop_export: dans export_lock")
            if not self._is_exporting:
                return True
            self._is_exporting = False
            print("stop_export: is_exporting = False")
            
            # Vider les buffers restants
            print("stop_export: appel _flush_remaining_buffers")
            self._flush_remaining_buffers()
            print("stop_export: _flush_remaining_buffers terminé")
            
            # Attendre que tous les buffers soient traités (vérification directe)
            print("stop_export: début attente buffers")
            timeout = 10.0  # 10 secondes max
            start_time = time.time()
            while (len(self._buffer_A) > 0 or len(self._buffer_B) > 0) and (time.time() - start_time) < timeout:
                print(f"stop_export: attente... Buffer A ({len(self._buffer_A)}), Buffer B ({len(self._buffer_B)})")
                time.sleep(0.1)
            
            if len(self._buffer_A) > 0 or len(self._buffer_B) > 0:
                print(f"Warning: Buffer A ({len(self._buffer_A)}) et Buffer B ({len(self._buffer_B)}) non vides après timeout")
                # Forcer le traitement des buffers restants
                print("stop_export: traitement forcé des buffers restants")
                if len(self._buffer_A) > 0:
                    self._export_queue.put("A")
                if len(self._buffer_B) > 0:
                    self._export_queue.put("B")
                # Attendre encore un peu pour le traitement
                time.sleep(1.0)
            
            print("stop_export: mise en queue None")
            self._export_queue.put(None)
            print("stop_export: attente thread")
            if self._export_thread:
                self._export_thread.join(timeout=5.0)
            print("stop_export: fermeture fichier")
            if self._current_file:
                if not self._dataFormat_Labview:
                    self._write_footer()
                self._current_file.close()
                self._current_file = None
                self._csv_writer = None
            print("stop_export: fin")
            return True

    def _write_metadata(self, metadata):
        if self._csv_writer and metadata:
            self._csv_writer.writerow(['# Metadata'])
            for k, v in metadata.items():
                self._csv_writer.writerow([f'# {k}', v])
            self._csv_writer.writerow([])
            headers = ['index', 'timestamp_rel', 'segment_id', 'is_active_line',
                       'ADC1_Ch1 Ex_real', 'ADC1_Ch2 Ex_imag', 'ADC1_Ch3 Ey_real', 
                       'ADC1_Ch4 Ey_imag', 'ADC2_Ch1 Ez_real', 'ADC2_Ch2 Ez_imag']
            self._csv_writer.writerow(headers)

    def _write_footer(self):
        if self._csv_writer:
            self._csv_writer.writerow(['# End of export', self._samples_written])

    def _export_worker(self):
        while self._is_exporting:
            try:
                item = self._export_queue.get(timeout=1.0)
                if item is None:
                    # En mode LabVIEW, écrire les données accumulées avant de terminer
                    if self._dataFormat_Labview and self._labview_sample_count > 0:
                        self._write_labview_format()
                    break
                
                # Traitement du double buffer
                if item == "A" or item == "B":
                    buffer_to_write = None
                    with self._buffer_lock:
                        if item == "A":
                            buffer_to_write = self._buffer_A.copy()
                            self._buffer_A = []
                        else:
                            buffer_to_write = self._buffer_B.copy()
                            self._buffer_B = []
                        self._writing_buffer = None
                    
                    # Traiter le buffer complet
                    if buffer_to_write:
                        self._process_buffer(buffer_to_write)
                    continue
                
                # Traitement des anciens échantillons individuels (pour compatibilité)
                index, t_rel, sample, segment_id, is_active = item
                
                if self._dataFormat_Labview:
                    # Accumuler les données pour le format LabVIEW
                    self._labview_temps_x.append(t_rel)
                    self._labview_temps_y.append(t_rel)
                    self._labview_temps_z.append(t_rel)
                    self._labview_ex_imag.append(sample.adc1_ch2)
                    self._labview_ex_real.append(sample.adc1_ch1)
                    self._labview_ey_imag.append(sample.adc1_ch4)
                    self._labview_ey_real.append(sample.adc1_ch3)
                    self._labview_ez_imag.append(sample.adc2_ch2)
                    self._labview_ez_real.append(sample.adc2_ch1)
                    self._labview_scan_state.append(int(is_active))
                    
                    self._labview_sample_count += 1
                    
                    # Écrire périodiquement si on a accumulé assez d'échantillons
                    if self._labview_sample_count >= self._labview_batch_size:
                        self._write_labview_format()
                else:
                    # Format standard
                    row = [index, f"{t_rel:.6f}", segment_id, int(is_active),
                           sample.adc1_ch1, sample.adc1_ch2, sample.adc1_ch3, 
                           sample.adc1_ch4, sample.adc2_ch1, sample.adc2_ch2]
                    self._csv_writer.writerow(row)
                    self._samples_written += 1
                    if self._samples_written % 100 == 0:
                        self._current_file.flush()
            except:
                continue

    def _write_labview_format(self):
        """Écrit les données au format LabVIEW rétrocompatible"""
        if self._labview_sample_count == 0:
            return
        
        # Nombre de points à exporter
        n_points = self._labview_sample_count
        
        # Écrire les données au format LabVIEW
        # Ligne 1: Temps X
        self._csv_writer.writerow(self._labview_temps_x)
        # Ligne 2-3: Lignes vides ou valeurs non utilisées
        self._csv_writer.writerow([-3.41E-01] * n_points)
        self._csv_writer.writerow([-2.06E-04] * n_points)
        # Ligne 4-5: Ex (imag, real)
        self._csv_writer.writerow(self._labview_ex_imag)
        self._csv_writer.writerow(self._labview_ex_real)
        # Ligne 6: Temps Y
        self._csv_writer.writerow(self._labview_temps_y)
        # Ligne 7-8: Lignes vides ou valeurs non utilisées
        self._csv_writer.writerow([-3.41E-01] * n_points)
        self._csv_writer.writerow([-4.98E-04] * n_points)
        # Ligne 9-10: Ey (imag, real)
        self._csv_writer.writerow(self._labview_ey_imag)
        self._csv_writer.writerow(self._labview_ey_real)
        # Ligne 11: Temps Z
        self._csv_writer.writerow(self._labview_temps_z)
        # Ligne 12-13: Lignes vides ou valeurs non utilisées
        self._csv_writer.writerow([-3.41E-01] * n_points)
        self._csv_writer.writerow([2.48E-04] * n_points)
        # Ligne 14-15: Ez (imag, real)
        self._csv_writer.writerow(self._labview_ez_imag)
        self._csv_writer.writerow(self._labview_ez_real)
        # Ligne 16: État du scan
        self._csv_writer.writerow(self._labview_scan_state)
        
        # Réinitialiser les listes après écriture
        self._labview_temps_x = []
        self._labview_temps_y = []
        self._labview_temps_z = []
        self._labview_ex_imag = []
        self._labview_ex_real = []
        self._labview_ey_imag = []
        self._labview_ey_real = []
        self._labview_ez_imag = []
        self._labview_ez_real = []
        self._labview_scan_state = []
        
        self._current_file.flush()
        self._samples_written += self._labview_sample_count
        self._labview_sample_count = 0

    def _exchange_buffers(self):
        """Échange les buffers et déclenche l'écriture"""
        with self._buffer_lock:
            # Si un buffer est déjà en écriture, ne rien faire
            if self._writing_buffer is not None:
                return
                
            # Échanger les buffers
            if self._active_buffer == "A":
                self._writing_buffer = "A"
                self._active_buffer = "B"
            else:
                self._writing_buffer = "B"
                self._active_buffer = "A"
                
        # Déclencher l'écriture dans la queue
        self._export_queue.put(self._writing_buffer)

    def _process_buffer(self, buffer):
        """Traite un buffer complet d'échantillons"""
        for index, t_rel, sample, segment_id, is_active in buffer:
            if self._dataFormat_Labview:
                # Accumuler les données pour le format LabVIEW
                self._labview_temps_x.append(t_rel)
                self._labview_temps_y.append(t_rel)
                self._labview_temps_z.append(t_rel)
                self._labview_ex_imag.append(sample.adc1_ch2)
                self._labview_ex_real.append(sample.adc1_ch1)
                self._labview_ey_imag.append(sample.adc1_ch4)
                self._labview_ey_real.append(sample.adc1_ch3)
                self._labview_ez_imag.append(sample.adc2_ch2)
                self._labview_ez_real.append(sample.adc2_ch1)
                self._labview_scan_state.append(int(is_active))
                
                self._labview_sample_count += 1
                
                # Écrire périodiquement si on a accumulé assez d'échantillons
                if self._labview_sample_count >= self._labview_batch_size:
                    self._write_labview_format()
            else:
                # Format standard
                row = [index, f"{t_rel:.6f}", segment_id, int(is_active),
                       sample.adc1_ch1, sample.adc1_ch2, sample.adc1_ch3, 
                       sample.adc1_ch4, sample.adc2_ch1, sample.adc2_ch2]
                self._csv_writer.writerow(row)
                self._samples_written += 1
                if self._samples_written % 100 == 0:
                        self._current_file.flush()

    def _flush_remaining_buffers(self):
        """Force l'écriture des buffers restants"""
        with self._buffer_lock:
            if len(self._buffer_A) > 0:
                self._export_queue.put("A")
            if len(self._buffer_B) > 0:
                self._export_queue.put("B")

class CSVPositionExporter:
    def __init__(self):
        self._export_queue = Queue()
        self._export_thread = None
        self._is_exporting = False
        self._export_lock = Lock()
        self._current_file = None
        self._csv_writer = None
        self._samples_written = 0
        self._sample_index = 0
        self._t0 = None
        self._current_segment_id = ""
        self._is_active_line = False
        self._filter_active_only = False

    def set_current_segment(self, segment_id: str, is_active_line: bool):
        """Met à jour le segment actuel pour marquer les échantillons"""
        self._current_segment_id = segment_id
        self._is_active_line = is_active_line
        print(f"[CSVPositionExporter] Segment changé: {segment_id}, active: {is_active_line}")

    def start_export(self, config: ExportConfig) -> bool:
        with self._export_lock:
            if self._is_exporting:
                return False
            self._filter_active_only = config.filter_active_lines_only
            filename = f"{config.filename_base}_Position_all.csv"
            filepath = Path(config.output_dir) / filename
            try:
                filepath.parent.mkdir(parents=True, exist_ok=True)
                self._current_file = open(filepath, 'w', newline='', encoding='utf-8')
                self._csv_writer = csv.writer(self._current_file)
                self._write_metadata(config.metadata)
                self._is_exporting = True
                self._export_thread = Thread(target=self._export_worker)
                self._export_thread.start()
                return True
            except:
                if self._current_file:
                    self._current_file.close()
                return False

    def add_sample(self, sample: PositionSample):
        if self._is_exporting:
            # Si filtrage actif et pas sur une ligne active, ignorer
            if self._filter_active_only and not self._is_active_line:
                return
                
            if self._t0 is None:
                self._t0 = time.perf_counter()
            t_rel = time.perf_counter() - self._t0
            self._export_queue.put((self._sample_index, t_rel, sample, self._current_segment_id, self._is_active_line))
            self._sample_index += 1

    def stop_export(self) -> bool:
        with self._export_lock:
            if not self._is_exporting:
                return True
            self._is_exporting = False
            self._export_queue.put(None)
            if self._export_thread:
                self._export_thread.join(timeout=5.0)
            if self._current_file:
                self._write_footer()
                self._current_file.close()
                self._current_file = None
                self._csv_writer = None
            return True

    def _write_metadata(self, metadata):
        if self._csv_writer and metadata:
            self._csv_writer.writerow(['# Metadata'])
            for k, v in metadata.items():
                self._csv_writer.writerow([f'# {k}', v])
            self._csv_writer.writerow([])
            headers = ['index', 'timestamp_rel', 'segment_id', 'is_active_line', 'x', 'y']
            self._csv_writer.writerow(headers)

    def _write_footer(self):
        if self._csv_writer:
            self._csv_writer.writerow(['# End of export', self._samples_written])

    def _export_worker(self):
        while self._is_exporting:
            try:
                item = self._export_queue.get(timeout=1.0)
                if item is None:
                    break
                index, t_rel, sample, segment_id, is_active = item
                row = [index, f"{t_rel:.6f}", segment_id, int(is_active), sample.x, sample.y]
                self._csv_writer.writerow(row)
                self._samples_written += 1
                if self._samples_written % 100 == 0:
                    self._current_file.flush()
            except:
                continue

class EFImagingBenchCSVExporter:
    def __init__(self):
        self.sensor_exporter = CSVSensorExporter()
        self.position_exporter = CSVPositionExporter()

    def set_current_segment(self, segment_id: str, is_active_line: bool):
        """Propage l'info de segment aux deux exporteurs"""
        self.sensor_exporter.set_current_segment(segment_id, is_active_line)
        self.position_exporter.set_current_segment(segment_id, is_active_line)

    def start_export(self, config: ExportConfig) -> bool:
        sensor_success = self.sensor_exporter.start_export(config)
        position_success = self.position_exporter.start_export(config)
        return sensor_success and position_success

    def add_sensor_sample(self, sample: AcquisitionSample):
        self.sensor_exporter.add_sample(sample)

    def add_position_sample(self, sample: PositionSample):
        self.position_exporter.add_sample(sample)

    def stop_export(self) -> bool:
        sensor_success = self.sensor_exporter.stop_export()
        position_success = self.position_exporter.stop_export()
        return sensor_success and position_success

    @property
    def is_exporting(self) -> bool:
        return self.sensor_exporter._is_exporting and self.position_exporter._is_exporting 