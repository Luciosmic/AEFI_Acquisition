"""
Module de gestion des buffers de position pour acquisition synchronisée
La communication en liaison série se fait de manière synchrone. Pour maximiser le débit d'acquisition,
on alimente le buffer en tâche de fond. Cela permet d'avoir un thread propre, et de pouvoir accéder 
aux données avec plusieurs points d'entrée (affichage, export, etc.)
Seule la classe AdaptivePositionBuffer doit être utilisée comme API publique.
Les classes CircularPositionBuffer et ProductionPositionBuffer sont internes.
"""
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock, RLock
from collections import deque
from typing import List, Callable

@dataclass
class PositionSample:
    """
    Échantillon de position synchronisée
    - timestamp : datetime de l'acquisition
    - x, y : positions (incréments ou unités physiques)
    """
    timestamp: datetime = field(default_factory=datetime.now)
    x: float = 0.0
    y: float = 0.0

# =========================
# CLASSE Position_AdaptiveBuffer --> API PUBLIQUE DU MODULE
# ========================= 
class Position_AdaptiveBuffer:
    """
    Buffer adaptatif pour positions, sélectionne le bon buffer selon le mode
    """

    def __init__(self):
        self._circular_buffer = Position_CircularBuffer(max_size=100)
        self._export_buffer = Position_ExportBuffer(flush_threshold=500)
        self._current_mode = 'exploration'  # 'exploration' ou 'export'
        self._lock = Lock()

    def set_mode(self, mode: str):
        """Change le mode du buffer ('exploration'/'export')"""
        with self._lock:
            self._current_mode = mode

    def append_sample(self, sample: PositionSample):
        """Ajoute un échantillon au buffer courant selon le mode"""
        with self._lock:
            if self._current_mode == 'exploration':
                self._circular_buffer.append_sample(sample)
            else:
                self._export_buffer.append_sample(sample)

    def get_latest_samples(self, count: int) -> List[PositionSample]:
        """Retourne les 'count' derniers échantillons"""
        with self._lock:
            if self._current_mode == 'exploration':
                return self._circular_buffer.get_latest(count)
            else:
                buffer_samples = self._export_buffer.get_buffer()
                return buffer_samples[-count:] if len(buffer_samples) >= count else buffer_samples

    def get_all_samples(self) -> List[PositionSample]:
        """Retourne tous les échantillons disponibles"""
        with self._lock:
            if self._current_mode == 'exploration':
                return self._circular_buffer.get_latest(self._circular_buffer.size())
            else:
                return self._export_buffer.get_buffer()

    def flush_for_export(self) -> List[PositionSample]:
        """Flush les échantillons pour export (mode export uniquement)"""
        with self._lock:
            if self._current_mode == 'export':
                return self._export_buffer.force_flush()
            else:
                return []

    def clear_buffer(self):
        """Vide le buffer actuel"""
        with self._lock:
            if self._current_mode == 'exploration':
                self._circular_buffer._buffer.clear()
            else:
                self._export_buffer.force_flush()

    def add_export_callback(self, callback: Callable[[List[PositionSample]], None]):
        """Ajoute un callback pour le flush en mode export"""
        self._export_buffer.add_flush_callback(callback)

    @property
    def current_mode(self) -> str:
        """Retourne le mode courant ('exploration' ou 'export')"""
        with self._lock:
            return self._current_mode

    @property
    def current_size(self) -> int:
        """Retourne la taille actuelle du buffer courant"""
        with self._lock:
            if self._current_mode == 'exploration':
                return self._circular_buffer.size()
            else:
                return self._export_buffer.size()



# =========================
# CLASSES INTERNES
# =========================

class Position_CircularBuffer:
    """
    Buffer circulaire pour positions (mode exploration)
    """
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._buffer = deque(maxlen=max_size)
        self._lock = RLock()
        self._total_samples = 0
    def append_sample(self, sample: PositionSample):
        with self._lock:
            self._buffer.append(sample)
            self._total_samples += 1
    def get_latest(self, count: int) -> List[PositionSample]:
        with self._lock:
            available = min(count, len(self._buffer))
            if available == 0:
                return []
            return list(reversed(list(self._buffer)[-available:]))
    def size(self) -> int:
        with self._lock:
            return len(self._buffer)
    @property
    def total_samples(self) -> int:
        with self._lock:
            return self._total_samples

class Position_ExportBuffer:
    """
    Buffer d'export pour positions (mode export)
    """
    def __init__(self, flush_threshold: int = 500):
        self.flush_threshold = flush_threshold
        self._buffer = []
        self._lock = RLock()
        self._flush_callbacks = []
    def add_flush_callback(self, callback: Callable[[List[PositionSample]], None]):
        with self._lock:
            self._flush_callbacks.append(callback)
    def append_sample(self, sample: PositionSample):
        with self._lock:
            self._buffer.append(sample)
            if len(self._buffer) >= self.flush_threshold:
                self._flush()
    def _flush(self):
        if not self._buffer:
            return
        samples_to_flush = self._buffer.copy()
        self._buffer.clear()
        for callback in self._flush_callbacks:
            try:
                callback(samples_to_flush)
            except Exception:
                pass
    def size(self) -> int:
        with self._lock:
            return len(self._buffer)
    def force_flush(self):
        with self._lock:
            if self._buffer:
                self._flush()
    def get_buffer(self) -> List[PositionSample]:
        with self._lock:
            return self._buffer.copy()
    @property
    def total_samples(self) -> int:
        return 0  # Stub
