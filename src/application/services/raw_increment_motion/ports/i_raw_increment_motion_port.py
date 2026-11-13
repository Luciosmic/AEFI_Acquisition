"""
Raw Increment Motion Port Interface

Responsibility:
- Drive one axis of the bench in motor increments, without any mm/pulse
  conversion: home, move to an increment, run to the + hard limit switch,
  speed in increments/s, position, stop, wait for the stop.

Rationale:
- The bar calibration measures the conversion: it must move the bench before
  the conversion exists (IMotionPort refuses until then) and reason in the
  increments the controller counts — mm would make the measurement depend on
  the value it measures.

Design:
- Axis is "X" or "Y". Every failure of the controller or of the link is
  raised as RawIncrementMotionError (port-declared error), never as a driver
  exception.
- move_to and run_to_positive_limit return at once (the caller polls
  is_moving / get_position, e.g. during the fly scan); home and
  wait_until_stopped block.
- Concurrency: shares the controller with IMotionPort's adapter; the driver
  serializes every serial exchange, so polling here and the adapter's monitor
  can run side by side. Nothing here locks the bench against another caller.
"""

from abc import ABC, abstractmethod


class IRawIncrementMotionPort(ABC):
    """
    One bench axis in raw motor increments.

    Responsibility:
        - Piloter un axe en incréments moteur bruts : homing, aller à un incrément, courir
          jusqu'à la butée + (fin de course physique), vitesse en incréments/s, lire la
          position, arrêter, attendre l'arrêt.
        - Dire si le fin de course + est actif.

    Rationale:
        Avant calibration, `IMotionPort` refuse tout mouvement en millimètres : il n'a pas
        de conversion. Or la calibration par barre doit déplacer le banc précisément pour
        mesurer cette conversion. Si elle passait par les millimètres, la mesure dépendrait
        de la valeur mesurée ; si elle appelait le driver Arcus directement, le service
        applicatif dépendrait de l'infrastructure et ne serait testable qu'avec le banc.

    Design:
        - Port sortant placé dans un dossier neutre `application/services/raw_increment_motion/ports/`
          (même chemin que le pilote autonome Arcus-Performax-4EX) : son premier consommateur,
          la calibration par barre, a été abandonné le 2026-10-30 ; le port reste pour tout
          usage qui doit bouger le banc en incréments bruts. Depuis le 2026-11-10, `MotionControlService.move_to_increments`
          l'utilise pour les consignes en incréments du panneau de mouvement.
        - Échec de contrôleur ou de liaison : `RawIncrementMotionError`, erreur déclarée par
          le port ; l'adaptateur traduit les exceptions du driver.
        - `move_to` / `run_to_positive_limit` rendent la main tout de suite (le fly scan
          interroge la position pendant le mouvement) ; `home` / `wait_until_stopped`
          bloquent.
        - Concurrence : le contrôleur est partagé avec l'adaptateur mm (`ArcusAdapter`) ;
          le driver sérialise chaque échange série (RLock), donc ce port et le moniteur de
          position de l'adaptateur mm peuvent fonctionner en même temps. Le moniteur reste
          actif pendant la calibration pour afficher la position en incréments.
          `wait_until_stopped` interroge `is_moving` au lieu de bloquer le driver, pour ne
          pas geler ce moniteur.
        - Qualité de service : le fly scan apparie distances et positions par leur instant
          de réception ; la latence d'une lecture de position (requête série) ne touche que
          le repérage grossier, absorbé par la marge.
    """

    @abstractmethod
    def home(self, axis: str) -> None:
        """Blocking homing on the home switch; the position becomes 0 there."""

    @abstractmethod
    def set_speed(self, axis: str, increments_per_s: int) -> None:
        """Cruise speed of later moves on this axis."""

    @abstractmethod
    def move_to(self, axis: str, increment: int) -> None:
        """Start a move to an absolute increment. Non-blocking."""

    @abstractmethod
    def run_to_positive_limit(self, axis: str) -> None:
        """Start running toward + until the hard limit switch stops the axis. Non-blocking."""

    @abstractmethod
    def is_moving(self, axis: str) -> bool: ...

    @abstractmethod
    def get_position(self, axis: str) -> int:
        """Current position, in motor increments."""

    @abstractmethod
    def is_at_positive_limit(self, axis: str) -> bool:
        """True when the + hard limit switch is active."""

    @abstractmethod
    def stop(self, axis: str) -> None:
        """Decelerated stop of the axis."""

    @abstractmethod
    def wait_until_stopped(self, axis: str, timeout_s: float) -> None:
        """Block until the axis stops; RawIncrementMotionError after timeout_s."""
