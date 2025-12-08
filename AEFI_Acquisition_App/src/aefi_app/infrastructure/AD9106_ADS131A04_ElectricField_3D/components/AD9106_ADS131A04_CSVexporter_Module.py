#!/usr/bin/env python3
"""
Exporteur CSV pour l'interface AD9106/ADS131A04

Gère l'export automatique streaming en mode Export :
- Écriture continue des données vers CSV
- Métadonnées complètes avec configuration figée
- Thread séparé pour performance
- Flush périodique vers disque

Complexité: 7/10 selon todo (écriture streaming 8/10)
"""

import csv
import os
import time
import hashlib
import json
import logging
from datetime import datetime
from threading import Thread, Lock, Event
from queue import Queue, Empty
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict, dataclass
from pathlib import Path

from .AD9106_ADS131A04_DataBuffer_Module import AcquisitionSample
# from .AD9106_ADS131A04_ModeController_Module import AcquisitionMode


@dataclass
class ExportConfig:
    """Configuration d'export CSV"""
    output_dir: str
    filename_base: str
    duration_seconds: Optional[int]  # None = continu
    metadata: Dict[str, Any]
    v_to_vm_factor: float = 63600.0
    dataFormat_Labview: bool = False  # Ajout du paramètre pour format rétrocompatible


class CSVExporter:
    """
    Exporteur CSV avec écriture streaming thread-safe
    Responsabilités:
    - Génération nom fichier avec timestamp
    - Écriture métadonnées et headers
    - Thread d'écriture séparé pour performance
    - Flush périodique vers disque
    - Finalisation propre du fichier
    """

    # === API PUBLIQUE DU MODULE ===

    def __init__(self):
        """Initialisation de l'exporteur"""
        self.logger = logging.getLogger(__name__)
        self._export_queue = Queue()
        self._export_thread = None
        self._is_exporting = False
        self._export_lock = Lock()
        self._current_file = None
        self._csv_writer = None
        self._export_config = None
        self._samples_written = 0
        self._sample_index = 0
        self._t0 = None  # temps de référence perf_counter
        
        # Système de double buffer
        self._buffer_A = []
        self._buffer_B = []
        self._active_buffer = "A"
        self._writing_buffer = None
        self._buffer_lock = Lock()
        self._batch_size = 1000
        
        # Format LabVIEW
        self._dataFormat_Labview = False
        self._labview_sample_count = 0
        
        self.logger.info("CSVExporter initialisé")

    def start_export(self, config: ExportConfig) -> bool:
        """
        Démarre un export CSV
        Args:
            config: Configuration d'export
        Returns:
            True si démarrage réussi
        """
        with self._export_lock:
            if self._is_exporting:
                return False
            self._export_config = config
            self._samples_written = 0
            self._sample_index = 0
            self._t0 = time.perf_counter()
            self._dataFormat_Labview = config.dataFormat_Labview
            
            # Initialisation des buffers
            self._init_double_buffer_system()
            
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            filename = f"{timestamp}_{config.filename_base}_vsTime.csv"
            filepath = Path(config.output_dir) / filename
            try:
                filepath.parent.mkdir(parents=True, exist_ok=True)
                self._current_file = open(filepath, 'w', newline='', encoding='utf-8')
                self._csv_writer = csv.writer(self._current_file)
                
                # Pas de métadonnées en mode LabVIEW
                if not self._dataFormat_Labview:
                    self._write_metadata()
                
                # Initialiser structures LabVIEW si nécessaire
                if self._dataFormat_Labview:
                    self._init_labview_format()
                
                self._is_exporting = True
                self._export_thread = Thread(target=self._export_worker)
                self._export_thread.start()
                return True
            except Exception as e:
                if self._current_file:
                    self._current_file.close()
                    self._current_file = None
                return False

    def add_sample(self, sample: AcquisitionSample):
        """
        Ajoute un échantillon à la queue d'export, en ajoutant index et timestamp relatif
        """
        if not self._is_exporting:
            return
            
        if self._t0 is None:
            self._t0 = time.perf_counter()
        t_rel = time.perf_counter() - self._t0
        
        # Utilisation du double buffer
        should_exchange = False
        with self._buffer_lock:
            if self._active_buffer == "A":
                self._buffer_A.append((self._sample_index, t_rel, sample))
                print(f"Buffer A: {len(self._buffer_A)}/{self._batch_size}")
                # Si buffer A plein, signaler l'échange
                if len(self._buffer_A) >= self._batch_size:
                    should_exchange = True
            else:
                self._buffer_B.append((self._sample_index, t_rel, sample))
                print(f"Buffer B: {len(self._buffer_B)}/{self._batch_size}")
                # Si buffer B plein, signaler l'échange
                if len(self._buffer_B) >= self._batch_size:
                    should_exchange = True
        
        # Échange des buffers en dehors du verrou
        if should_exchange:
            print(f"ÉCHANGE BUFFER {self._active_buffer} -> {'B' if self._active_buffer == 'A' else 'A'} (échantillon {self._sample_index})")
            self._exchange_buffers()
        
        self._sample_index += 1

    def add_samples(self, samples: List[AcquisitionSample]):
        """
        Ajoute plusieurs échantillons à la queue d'export
        Args:
            samples: Liste d'échantillons à exporter
        """
        for sample in samples:
            self.add_sample(sample)

    def stop_export(self) -> bool:
        """
        Arrête l'export et finalise le fichier
        Returns:
            True si arrêt réussi
        """
        with self._export_lock:
            if not self._is_exporting:
                return True
            self._is_exporting = False
            
            # Vider les buffers restants
            self._flush_remaining_buffers()
            
            self._export_queue.put(None)
            if self._export_thread:
                self._export_thread.join(timeout=5.0)
            if self._current_file:
                try:
                    if not self._dataFormat_Labview:
                        self._write_footer()
                    self._current_file.close()
                except Exception:
                    pass
                finally:
                    self._current_file = None
                    self._csv_writer = None
            return True

    @property
    def is_exporting(self) -> bool:
        """État d'export actuel"""
        return self._is_exporting

    @property
    def samples_written(self) -> int:
        """Nombre d'échantillons écrits"""
        return self._samples_written

    def get_export_status(self) -> Dict[str, Any]:
        """Retourne le statut d'export"""
        return {
            'is_exporting': self._is_exporting,
            'samples_written': self._samples_written,
            'queue_size': self._export_queue.qsize(),
            'config': asdict(self._export_config) if self._export_config else None
        }

    # === MÉTHODES INTERNES ===
    
    def _init_double_buffer_system(self):
        """Initialise le système de double buffer"""
        self._buffer_A = []
        self._buffer_B = []
        self._active_buffer = "A"
        self._writing_buffer = None
    
    def _init_labview_format(self):
        """Initialise les structures pour le format LabVIEW"""
        self._labview_sample_count = 0
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
    
    def _exchange_buffers(self):
        """Échange les buffers et déclenche l'écriture"""
        print(f"  _exchange_buffers: début")
        print(f"  _exchange_buffers: avant verrou buffer_lock")
        with self._buffer_lock:
            print(f"  _exchange_buffers: dans verrou buffer_lock")
            # Si un buffer est déjà en écriture, ne rien faire
            if self._writing_buffer is not None:
                print(f"  _exchange_buffers: buffer déjà en écriture ({self._writing_buffer})")
                return
                
            # Échanger les buffers
            if self._active_buffer == "A":
                self._writing_buffer = "A"
                self._active_buffer = "B"
                print(f"  _exchange_buffers: A -> B, writing=A")
            else:
                self._writing_buffer = "B"
                self._active_buffer = "A"
                print(f"  _exchange_buffers: B -> A, writing=B")
            print(f"  _exchange_buffers: sortie verrou buffer_lock")
                
        # Déclencher l'écriture dans la queue
        print(f"  _exchange_buffers: mise en queue {self._writing_buffer}")
        self._export_queue.put(self._writing_buffer)
        print(f"  _exchange_buffers: fin")

    def _flush_remaining_buffers(self):
        """Force l'écriture des buffers restants"""
        with self._buffer_lock:
            if len(self._buffer_A) > 0:
                self._export_queue.put("A")
            if len(self._buffer_B) > 0:
                self._export_queue.put("B")

    def _write_metadata(self):
        """Écrit les métadonnées en header"""
        if not self._csv_writer or not self._export_config:
            return
        self._csv_writer.writerow(['# Configuration Export'])
        self._csv_writer.writerow(['# Timestamp:', datetime.now().isoformat()])
        self._csv_writer.writerow(['# Mode:', 'EXPORT'])
        metadata = self._export_config.metadata
        for key, value in metadata.items():
            self._csv_writer.writerow([f'# {key}:', str(value)])
        self._csv_writer.writerow(['# V_to_Vm_Factor:', self._export_config.v_to_vm_factor])
        self._csv_writer.writerow([])
        headers = [
            'index', 'timestamp',
            'ADC1_Ch1', 'ADC1_Ch2', 'ADC1_Ch3', 'ADC1_Ch4',
            'ADC2_Ch1', 'ADC2_Ch2', 'ADC2_Ch3', 'ADC2_Ch4'
        ]
        self._csv_writer.writerow(headers)

    def _write_footer(self):
        """Écrit les métadonnées de fin"""
        if not self._csv_writer:
            return
        self._csv_writer.writerow([])
        self._csv_writer.writerow(['# Export finalisé'])
        self._csv_writer.writerow(['# Échantillons écrits:', self._samples_written])
        self._csv_writer.writerow(['# Fin timestamp:', datetime.now().isoformat()])

    def _export_worker(self):
        """Worker thread pour écriture CSV"""
        print("  _export_worker: démarrage")
        while self._is_exporting or not self._export_queue.empty():
            try:
                print(f"  _export_worker: attente queue...")
                item = self._export_queue.get(timeout=1.0)
                print(f"  _export_worker: reçu {item}")
                if item is None:
                    print("  _export_worker: signal d'arrêt")
                    break
                    
                if item == "A" or item == "B":
                    print(f"  _export_worker: traitement buffer {item}")
                    # Traitement d'un buffer complet
                    buffer_to_write = None
                    with self._buffer_lock:
                        if item == "A":
                            buffer_to_write = self._buffer_A.copy()
                            self._buffer_A = []
                            print(f"  _export_worker: buffer A copié ({len(buffer_to_write)} échantillons)")
                        else:
                            buffer_to_write = self._buffer_B.copy()
                            self._buffer_B = []
                            print(f"  _export_worker: buffer B copié ({len(buffer_to_write)} échantillons)")
                        self._writing_buffer = None
                        print(f"  _export_worker: writing_buffer remis à None")
                    
                    # Écrire le buffer
                    if buffer_to_write:
                        if self._dataFormat_Labview:
                            self._process_buffer_labview(buffer_to_write)
                        else:
                            self._process_buffer_standard(buffer_to_write)
                
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Erreur dans export_worker: {e}")
                continue
    
    def _process_buffer_standard(self, buffer):
        """Traite un buffer complet au format standard"""
        if not self._csv_writer:
            return
            
        for index, t_rel, sample in buffer:
            row = [
                index,
                f"{t_rel:.6f}",
                sample.adc1_ch1, sample.adc1_ch2, sample.adc1_ch3, sample.adc1_ch4,
                sample.adc2_ch1, sample.adc2_ch2, sample.adc2_ch3, sample.adc2_ch4
            ]
            self._csv_writer.writerow(row)
            self._samples_written += 1
        
        self._current_file.flush()
    
    def _process_buffer_labview(self, buffer):
        """Traite un buffer complet au format LabVIEW"""
        if not buffer:
            return
        
        # Extraire les données du buffer
        for index, t_rel, sample in buffer:
            self._labview_temps_x.append(t_rel)
            self._labview_temps_y.append(t_rel)
            self._labview_temps_z.append(t_rel)
            self._labview_ex_imag.append(sample.adc1_ch2)
            self._labview_ex_real.append(sample.adc1_ch1)
            self._labview_ey_imag.append(sample.adc1_ch4)
            self._labview_ey_real.append(sample.adc1_ch3)
            self._labview_ez_imag.append(sample.adc2_ch2)
            self._labview_ez_real.append(sample.adc2_ch1)
            self._labview_scan_state.append(1)  # Toujours actif par défaut
            
            self._labview_sample_count += 1
        
        # Écrire si on a assez d'échantillons
        if self._labview_sample_count >= self._batch_size:
            self._write_labview_format()
    
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