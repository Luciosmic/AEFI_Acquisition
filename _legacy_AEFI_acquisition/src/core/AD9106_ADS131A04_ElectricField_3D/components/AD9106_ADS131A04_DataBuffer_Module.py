#!/usr/bin/env python3
"""
Data Buffer - Système de buffers adaptatifs pour acquisition

Gère 3 types de buffers selon le mode d'acquisition :
- CircularBuffer : Mode EXPLORATION (100 échantillons max, overwrite)
- ProductionBuffer : Mode EXPORT (1000+ échantillons, flush callbacks)
- AdaptiveDataBuffer : Sélection automatique selon le mode
"""

# =========================
# Imports
# =========================
import time
import logging
from datetime import datetime
from threading import Lock, RLock
from collections import deque
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field



# =========================
# CLASSE ADAPTIVE_DATA_BUFFER --> API PUBLIQUE DU MODULE
# =========================
class AdaptiveDataBuffer:
    """
    Buffer adaptatif qui sélectionne automatiquement le bon buffer selon le mode
    """
    def __init__(self, max_size: int = 100, flush_threshold: int = 500, logger=None):
        from threading import RLock
        self._lock = RLock()
        self._circular_buffer = CircularBuffer(max_size)
        self._production_buffer = ProductionBuffer(flush_threshold)
        self._current_mode = 'exploration'
        self.logger = logger if logger is not None else self._default_logger()
    def _default_logger(self):
        import logging
        return logging.getLogger(__name__)

    # === API PUBLIQUE DU MODULE ===

    def add_sample(self, sample):
        self.append_sample(sample)

    def append_sample(self, sample):
        with self._lock:
            if self._current_mode == 'exploration':
                self._circular_buffer.append_sample(sample)
            else:  # Mode export
                self._production_buffer.append_sample(sample)

    def get_latest_samples(self, count: int) -> list:
        with self._lock:
            if self._current_mode == 'exploration':
                return self._circular_buffer.get_latest(count)
            else:
                buffer_samples = self._production_buffer.get_buffer()
                return buffer_samples[-count:] if len(buffer_samples) >= count else buffer_samples

    def get_all_samples(self) -> list:
        """Retourne tous les échantillons disponibles"""
        with self._lock:
            if self._current_mode == 'exploration':
                return self._circular_buffer.get_latest(self._circular_buffer.size())
            else:
                return self._production_buffer.get_buffer()

    def clear_buffer(self):
        """Vide le buffer actuel"""
        with self._lock:
            if self._current_mode == 'exploration':
                self._circular_buffer.clear()
            else:
                self._production_buffer.force_flush()

    def flush_for_export(self):
        """Flush les échantillons pour export CSV (mode export uniquement)"""
        with self._lock:
            if self._current_mode == 'export':
                return self._production_buffer.force_flush()
            else:
                self.logger.warning("Flush demandé en mode non-Export")
                return []

    def get_buffer_status(self) -> dict:
        """Alias pour get_buffer_info() pour compatibilité"""
        return self.get_buffer_info()

    def get_buffer_info(self) -> dict:
        """Retourne des informations sur l'état des buffers"""
        with self._lock:
            if self._current_mode == 'exploration':
                return {
                    "mode": "exploration",
                    "buffer_type": "circular",
                    "current_size": self._circular_buffer.size(),
                    "max_size": self._circular_buffer.max_size,
                    "total_samples": self._circular_buffer.total_samples
                }
            else:
                return {
                    "mode": "export", 
                    "buffer_type": "production",
                    "pending_size": self._production_buffer.size(),
                    "flush_threshold": self._production_buffer.flush_threshold,
                    "total_samples": self._production_buffer.total_samples
                }

    def add_production_callback(self, callback):
        """Ajoute un callback pour le flush en mode production"""
        self._production_buffer.add_flush_callback(callback)

    def set_mode(self, mode: str):
        """Change le mode du buffer ('exploration'/'export')"""
        with self._lock:
            if self._current_mode != mode:
                old_mode = self._current_mode
                self._current_mode = mode
                self.logger.info(f"Buffer mode changé: {old_mode} → {mode}")

# add_sample = append_sample
    def is_buffer_fully_updated(self) -> bool:
        """Vérifie la régénération complète du buffer après clear"""
        with self._lock:
            if self._current_mode == 'exploration':
                return self._circular_buffer.size() <= self._circular_buffer.max_size
            else:
                return self._production_buffer.size() <= self._production_buffer.flush_threshold
            
# =========================
# CLASSES INTERNES
# =========================

@dataclass
class AcquisitionSample:
    """
    Échantillon d'acquisition avec validation 4+4 canaux
    
    Structure données pour un échantillon complet :
    - ADC1 : 4 canaux (adc1_ch1 à adc1_ch4)
    - ADC2 : 4 canaux (adc2_ch1 à adc2_ch4)
    """
    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)
    
    # ADC1 - 4 canaux
    adc1_ch1: int = 0
    adc1_ch2: int = 0
    adc1_ch3: int = 0
    adc1_ch4: int = 0
    
    # ADC2 - 4 canaux
    adc2_ch1: int = 0
    adc2_ch2: int = 0
    adc2_ch3: int = 0
    adc2_ch4: int = 0
    
    def __post_init__(self):
        """Validation des valeurs ADC"""
        for field_name, field_value in self.__dict__.items():
            # Skip timestamp validation
            if field_name == 'timestamp':
                continue
            if not isinstance(field_value, int):
                raise ValueError(f"{field_name} doit être un entier, reçu : {type(field_value)}")
    
    def to_list(self) -> List[int]:
        """Convertit l'échantillon en liste [ADC1_ch1, ADC1_ch2, ..., ADC2_ch4]"""
        return [
            self.adc1_ch1, self.adc1_ch2, self.adc1_ch3, self.adc1_ch4,
            self.adc2_ch1, self.adc2_ch2, self.adc2_ch3, self.adc2_ch4
        ]


class CircularBuffer:
    """
    Buffer circulaire pour mode EXPLORATION
    
    Caractéristiques :
    - Taille max : 100 échantillons
    - Overwrite automatique des anciens
    - Thread-safe avec RLock
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialisation du buffer circulaire
        
        Args:
            max_size: Taille maximale du buffer
        """
        self.max_size = max_size
        self._buffer = deque(maxlen=max_size)
        self._lock = RLock()
        self._total_samples = 0
    
    def append_sample(self, sample: AcquisitionSample):
        with self._lock:
            self._buffer.append(sample)
            self._total_samples += 1
    
    def get_latest(self, count: int) -> List[AcquisitionSample]:
        with self._lock:
            available = min(count, len(self._buffer))
            if available == 0:
                return []
            
            # Retourne les 'available' derniers échantillons en ordre inverse
            result = list(reversed(list(self._buffer)[-available:]))
            return result
    
    def size(self) -> int:
        """Retourne la taille actuelle du buffer"""
        with self._lock:
            return len(self._buffer)
    
    def clear(self):
        """Vide le buffer circulaire"""
        with self._lock:
            self._buffer.clear()
            # Note: total_samples n'est pas remis à zéro pour garder la trace historique
    
    @property
    def total_samples(self) -> int:
        """Retourne le nombre total d'échantillons ajoutés"""
        with self._lock:
            return self._total_samples


class ProductionBuffer:
    """
    Buffer de production pour mode EXPORT
    
    Caractéristiques :
    - Flush automatique au seuil (défaut : 500)
    - Callbacks multiples supportés
    - Gestion exceptions dans callbacks
    """
    
    def __init__(self, flush_threshold: int = 500):
        """
        Initialisation du buffer de production
        
        Args:
            flush_threshold: Seuil de déclenchement du flush
        """
        self.flush_threshold = flush_threshold
        self._buffer = []
        self._lock = RLock()
        self._flush_callbacks = []
    
    def add_flush_callback(self, callback: Callable[[List[AcquisitionSample]], None]):
        """
        Ajoute un callback appelé lors du flush
        
        Args:
            callback: Fonction appelée avec la liste des échantillons
        """
        with self._lock:
            self._flush_callbacks.append(callback)
    
    def append_sample(self, sample: AcquisitionSample):
        with self._lock:
            self._buffer.append(sample)
            
            # Vérification seuil de flush
            if len(self._buffer) >= self.flush_threshold:
                self._flush()
    
    def _flush(self):
        """Flush le buffer vers les callbacks"""
        if not self._buffer:
            return
        
        # Copie des données pour callbacks
        samples_to_flush = self._buffer.copy()
        
        # Vidage du buffer
        self._buffer.clear()
        
        # Appel des callbacks (avec gestion d'exception)
        for callback in self._flush_callbacks:
            try:
                callback(samples_to_flush)
            except Exception:
                # Ignore les exceptions dans les callbacks
                pass
    
    def size(self) -> int:
        """Retourne la taille actuelle du buffer"""
        with self._lock:
            return len(self._buffer)
    
    def force_flush(self):
        """Force un flush immédiat"""
        with self._lock:
            if self._buffer:
                self._flush()
    
    def get_buffer(self) -> List[AcquisitionSample]:
        with self._lock:
            return self._buffer.copy()
    
    @property
    def total_samples(self) -> int:
        """Nombre total d'échantillons traités"""
        return 0  # Stub pour l'instant

