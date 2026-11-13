"""
Inertial Probe Stream Port Interface

Responsibility:
- Continuous (streamed) reception of inertial probe samples (accelerometer,
  gyroscope, magnetometer), timestamped on the PC at reception.

Rationale:
- The application service depends on this abstraction, not on a specific
  board or driver (today: LSM9DS1 behind a serial board).

Design:
- Abstract Base Class (ABC), pure interface.
- Blocking read_sample(): no thread, no callback. The caller (the acquisition
  executor) loops on it from a worker thread.
- start_stream() blocks for ~0.5 s on the real board: never call it from the
  Qt thread.
- disconnect() must send the stream stop to the board (the board keeps its
  stream active with the port closed) and be idempotent.
- No nominal rate presumed: the consumer measures it from timestamp_s.
- The lidar is a channel of this same stream (see the ponytail note below).
"""

from abc import ABC, abstractmethod
from typing import Optional, Sequence

from application.inertial_probe.inertial_probe_service.dtos.inertial_probe_dtos import (
    InertialProbeStreamSample,
)


# ponytail: the lidar (a distance, not an inertial quantity) is a channel of this
# same stream because it sits on the same board and serial link — an
# infrastructure fact. Ceiling: a single stream carries both. Upgrade: a separate
# lidar port; the shared board/link stays an infrastructure detail.
class IInertialProbeStreamPort(ABC):
    """
    Port interface for a streamed inertial probe (connection + stream).

    Responsibility:
        - `connect()` / `disconnect()` (idempotent, envoie l'arrêt du flux) /
          `is_connected()`.
        - `start_stream(channels)` : démarre le flux d'un sous-ensemble de canaux.
          Bloque ~0,5 s sur la vraie carte.
        - `stop_stream()`.
        - `read_sample(timeout_s)` : lecture bloquante, `None` sur timeout.

    Rationale:
        Sans port, le service applicatif importerait le driver série de la carte :
        changer de carte ou de firmware réécrirait le service, et aucun test
        applicatif ne tournerait sans port COM. Le flux continu est aussi incompatible
        avec un mode requête/réponse sur la même liaison (un flux actif renvoie une
        ligne de flux à la place de la réponse), donc le contrat du flux a son propre
        port.

    Design:
        - **Port outbound** (Application vers Infrastructure) dans
          `inertial_probe_service/ports/`.
        - Lecture bloquante, sans thread ni callback : le thread appartient à
          l'exécuteur d'acquisition.
        - **Dette non silencieuse** : le lidar est un canal de ce même flux parce qu'il
          est sur la même carte et la même liaison série (fait d'infrastructure). Ce
          n'est pas un capteur inertiel. Sortie : un port lidar séparé, la carte
          partagée restant un détail d'infrastructure.
    """

    @abstractmethod
    def connect(self) -> None:
        """Open the link. Raises whatever the driver raises."""

    @abstractmethod
    def disconnect(self) -> None:
        """Stop any stream and close the link. Idempotent."""

    @abstractmethod
    def is_connected(self) -> bool:
        """True if the link is open."""

    @abstractmethod
    def start_stream(self, channels: Sequence[str]) -> None:
        """
        Start streaming a subset of {"accelerometer", "gyroscope",
        "magnetometer", "lidar"}. Blocks ~0.5 s on the real board.
        """

    @abstractmethod
    def stop_stream(self) -> None:
        """Stop the stream (the board keeps streaming until told to stop)."""

    @abstractmethod
    def read_sample(self, timeout_s: float = 1.0) -> Optional[InertialProbeStreamSample]:
        """Next streamed sample, or None on timeout. RuntimeError if not streaming."""
