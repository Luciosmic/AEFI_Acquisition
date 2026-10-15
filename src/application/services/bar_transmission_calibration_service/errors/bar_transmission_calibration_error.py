"""
Bar Transmission Calibration Use-Case Error Union

See bar_transmission_calibration_error_intention.md.
"""

from __future__ import annotations

from dataclasses import dataclass


class BarTransmissionCalibrationError:
    """Sealed union tag: every failure of the bar calibration the caller must tell apart."""

    @property
    def message(self) -> str:  # pragma: no cover - overridden by every variant
        raise NotImplementedError

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True)
class MeasurementAlreadyRunning(BarTransmissionCalibrationError):
    axis: str

    @property
    def message(self) -> str:
        return f"une mesure de l'axe {self.axis} est déjà en cours"


@dataclass(frozen=True)
class BenchResourceControlled(BarTransmissionCalibrationError):
    """A resource the measurement needs (motors, LIDAR stream) is held by another
    owner, e.g. a running scan: the ExclusiveControl refusal, as is."""

    refusal: str

    @property
    def message(self) -> str:
        return f"calibration refusée — {self.refusal}"


@dataclass(frozen=True)
class LidarStreamBusy(BarTransmissionCalibrationError):
    owner: str

    @property
    def message(self) -> str:
        return (
            f"le flux LIDAR est déjà diffusé par {self.owner} : arrêter l'acquisition du panneau "
            "avant la calibration (un seul propriétaire du port série)"
        )


@dataclass(frozen=True)
class LidarUnavailable(BarTransmissionCalibrationError):
    detail: str

    @property
    def message(self) -> str:
        return f"LIDAR indisponible : {self.detail}"


@dataclass(frozen=True)
class MotionChainIncomplete(BarTransmissionCalibrationError):
    missing: str

    @property
    def message(self) -> str:
        return f"chaîne de mouvement incomplète : {self.missing}"


@dataclass(frozen=True)
class InvalidMeasurementRequest(BarTransmissionCalibrationError):
    detail: str

    @property
    def message(self) -> str:
        return f"demande invalide : {self.detail}"


@dataclass(frozen=True)
class BenchMotionFailed(BarTransmissionCalibrationError):
    axis: str
    detail: str

    @property
    def message(self) -> str:
        return f"axe {self.axis} : mouvement en échec — {self.detail}"


@dataclass(frozen=True)
class PositiveLimitNotReached(BarTransmissionCalibrationError):
    axis: str
    stopped_at_increment: int

    @property
    def message(self) -> str:
        return (
            f"axe {self.axis} : arrêté à {self.stopped_at_increment} incréments sans fin de course + actif "
            "(butée opposée non atteinte, vérifier le fin de course)"
        )


@dataclass(frozen=True)
class BarNotFound(BarTransmissionCalibrationError):
    axis: str
    reason: str

    @property
    def message(self) -> str:
        return f"axe {self.axis} : barre non trouvée dans le fly scan — {self.reason}"


@dataclass(frozen=True)
class EdgeNotBracketed(BarTransmissionCalibrationError):
    axis: str
    front: str
    detail: str

    @property
    def message(self) -> str:
        return f"axe {self.axis}, {self.front} : encadrement non vérifié à l'arrêt — {self.detail}"


@dataclass(frozen=True)
class MeasurementCancelled(BarTransmissionCalibrationError):
    axis: str

    @property
    def message(self) -> str:
        return f"mesure de l'axe {self.axis} annulée par l'opérateur"


@dataclass(frozen=True)
class MeasurementsNotComparable(BarTransmissionCalibrationError):
    detail: str

    @property
    def message(self) -> str:
        return f"mesures X/Y non combinables : {self.detail}"


@dataclass(frozen=True)
class InternalCalibrationError(BarTransmissionCalibrationError):
    detail: str

    @property
    def message(self) -> str:
        return f"erreur interne de la calibration : {self.detail}"
