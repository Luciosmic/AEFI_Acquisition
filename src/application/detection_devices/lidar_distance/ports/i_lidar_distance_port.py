"""
LIDAR Distance Port Interface

Responsibility:
- Open the LIDAR distance stream for the calibration, read distances
  timestamped at their reception, close it.
- Say whether someone else (the inertial probe panel) streams it already.

Rationale:
- The calibration starts and stops the LIDAR stream itself (decision
  2026-10-15) and must refuse when the panel already streams it: the serial
  link has one owner.

Design:
- open(): LidarStreamBusyError if streamed elsewhere, LidarUnavailableError if
  the link cannot be opened. Connects the link if needed (and close() then
  disconnects it again).
- read_distance(): next reading in reception order, or None on timeout.
  Readings are timestamped when they arrive, not when they are read: a reader
  that waits (settling) can still tell which readings came after the wait.
- Each reading carries a domain LidarDistance: a valid distance (> 0) or "no
  return" (the LIDAR sends 0 when it measures nothing: floor out of range,
  dropout). Only valid distances or explicit "no return" samples: never a
  distance of 0, and never a "no return" dropped silently (off the bar, it is
  the floor's signature). The 0 rule itself lives in LidarDistance.
- close(): idempotent, always stops the stream (the board keeps streaming
  until told to stop).
- Timestamps share the service clock (time.perf_counter on the bench).
"""

from abc import ABC, abstractmethod
from typing import Optional

from application.detection_devices.lidar_distance.dtos.lidar_distance_dtos import (
    LidarDistanceReading,
)


class ILidarDistancePort(ABC):
    """
    Responsibility:
        - Ouvrir le flux LIDAR (refus `LidarStreamBusyError` si le panneau le diffuse déjà),
          lire les distances horodatées à leur réception, fermer le flux dans tous les cas.
        - Ne livrer que des distances valides ou des « pas de retour » explicites : chaque
          lecture porte un `LidarDistance` du noyau partagé (le LIDAR renvoie 0 quand il
          ne mesure rien ; premier essai au banc, 2026-10-15 : le sol hors de portée ne
          renvoie que des 0, la barre a des décrochages). Un 0 n'est jamais une
          distance ; il n'est pas non plus supprimé, car hors barre il est la seule trace
          du sol. La règle du 0 vit dans `LidarDistance`, pas dans le port ni
          l'adaptateur.

    Rationale:
        Le LIDAR est un canal du flux de la carte inertielle (`IInertialProbeStreamPort`),
        piloté par le panneau du capteur. Si la calibration utilisait ce port directement,
        elle hériterait de tout le flux inertiel et de son exécuteur ; et deux lecteurs sur
        le même port série se voleraient les lignes. Il faut un port étroit, du point de vue
        de la calibration : « une distance, quand elle est arrivée », et un propriétaire
        unique du flux.

    Design:
        - Port sortant placé dans un dossier neutre `application/detection_devices/lidar_distance/ports/`
          (même chemin que le pilote autonome LIDAR-VL53L0C-ESP32) : son premier consommateur,
          la calibration par barre, a été abandonné le 2026-10-30 ; le port reste pour tout
          lecteur du LIDAR, quel que soit le capteur derrière.
        - Horodatage à la réception (pas à la lecture) : le service attend la stabilisation
          sans lire, puis ne garde que les distances arrivées après.
        - Erreurs déclarées : `LidarStreamBusyError`, `LidarUnavailableError`
          (`lidar_stream_error.py`).
        - Qualité de service : ≈ 5,1 Hz (185 à 208 ms) mesuré sur l'ESP32 le 2026-10-30
          (25 Hz pour le LIDAR de la carte inertielle, journal AEFI 2026-10-12) ; le service
          ne suppose pas de cadence, il attend des échantillons avec un délai de silence.
    """
    @abstractmethod
    def is_streamed_elsewhere(self) -> bool:
        """True while another owner (the sensor panel) streams the board."""

    @abstractmethod
    def open(self) -> None:
        """Start the LIDAR stream for this caller."""

    @abstractmethod
    def read_distance(self, timeout_s: float) -> Optional[LidarDistanceReading]:
        """Next reading in reception order (its LidarDistance may be "no return");
        None on timeout; LidarUnavailableError on link failure."""

    @abstractmethod
    def close(self) -> None:
        """Stop the stream (and disconnect if open() connected). Idempotent."""
