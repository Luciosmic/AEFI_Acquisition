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

from LSM9D_DataBuffer_Module import AcquisitionSample
from LSM9D_ModeController_Module import AcquisitionMode


@dataclass
class ExportConfig:
    """Configuration d'export CSV"""
    output_dir: str
    filename_base: str
    duration_seconds: Optional[int]  # None = continu
    metadata: Dict[str, Any]
    v_to_vm_factor: float = 63600.0


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
            
            # Génération nom fichier avec timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            filename = f"{timestamp}_{config.filename_base}_vsTime.csv"
            filepath = Path(config.output_dir) / filename
            
            try:
                # Création répertoire si nécessaire
                filepath.parent.mkdir(parents=True, exist_ok=True)
                
                # Ouverture fichier
                self._current_file = open(filepath, 'w', newline='', encoding='utf-8')
                self._csv_writer = csv.writer(self._current_file)
                
                # Écriture métadonnées
                self._write_metadata()
                
                # Démarrage thread export
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
        if self._is_exporting:
            if self._t0 is None:
                self._t0 = time.perf_counter()
            t_rel = time.perf_counter() - self._t0
            # On emballe le sample avec index et t_rel
            self._export_queue.put((self._sample_index, t_rel, sample))
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
            
            # Signal d'arrêt
            self._export_queue.put(None)
            
            # Attente fin thread
            if self._export_thread:
                self._export_thread.join(timeout=5.0)
            
            # Finalisation fichier
            if self._current_file:
                try:
                    self._write_footer()
                    self._current_file.close()
                except Exception:
                    pass
                finally:
                    self._current_file = None
                    self._csv_writer = None
            
            return True
    
    def _write_metadata(self):
        """Écrit les métadonnées en header"""
        if not self._csv_writer or not self._export_config:
            return
        
        # Header de métadonnées
        self._csv_writer.writerow(['# Configuration Export'])
        self._csv_writer.writerow(['# Timestamp:', datetime.now().isoformat()])
        self._csv_writer.writerow(['# Mode:', 'EXPORT'])
        
        # Configuration
        metadata = self._export_config.metadata
        for key, value in metadata.items():
            self._csv_writer.writerow([f'# {key}:', str(value)])
        
        self._csv_writer.writerow(['# V_to_Vm_Factor:', self._export_config.v_to_vm_factor])
        
        # Ligne vide
        self._csv_writer.writerow([])
        
        # Nouveau header avec index et timestamp relatif
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
        while self._is_exporting:
            try:
                item = self._export_queue.get(timeout=1.0)
                if item is None:
                    break
                index, t_rel, sample = item
                if self._csv_writer:
                    row = [
                        index,
                        f"{t_rel:.6f}",
                        sample.adc1_ch1, sample.adc1_ch2, sample.adc1_ch3, sample.adc1_ch4,
                        sample.adc2_ch1, sample.adc2_ch2, sample.adc2_ch3, sample.adc2_ch4
                    ]
                    self._csv_writer.writerow(row)
                    self._samples_written += 1
                    # Flush périodique (toutes les 100 lignes)
                    if self._samples_written % 100 == 0:
                        self._current_file.flush()
            except Empty:
                # Timeout normal, continuer
                continue
            except Exception:
                # Erreur d'écriture, arrêter export
                break
        # Après le break (signal d'arrêt), vider la queue restante
        while True:
            try:
                item = self._export_queue.get_nowait()
                if item is None:
                    break
                index, t_rel, sample = item
                if self._csv_writer:
                    row = [
                        index,
                        f"{t_rel:.6f}",
                        sample.adc1_ch1, sample.adc1_ch2, sample.adc1_ch3, sample.adc1_ch4,
                        sample.adc2_ch1, sample.adc2_ch2, sample.adc2_ch3, sample.adc2_ch4
                    ]
                    self._csv_writer.writerow(row)
                    self._samples_written += 1
            except Empty:
                break
    
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