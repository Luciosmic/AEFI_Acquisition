"""
Inertial sensor view model (pure, no Qt, no domain import).

Responsibility:
- Static descriptors of the displayed channels (explicit labels, "unverified"
  flags) and a frozen, ready-to-display reading built from primitives.

ponytail: the lidar is displayed as a channel of the inertial sensor panel only
because it travels in the same stream (same board, same serial link). Ceiling:
one panel and one reading carry both. Upgrade: a separate lidar panel and view
model once the lidar has its own concept and port.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

ABSENT = "—"


@dataclass(frozen=True)
class ChannelDescriptor:
    key: str
    label: str
    axis_labels: Tuple[str, ...]
    decimals: int
    signed: bool
    unverified_reason: str = ""
    note: str = ""

    @property
    def unverified(self) -> bool:
        return bool(self.unverified_reason)


CHANNELS: Tuple[ChannelDescriptor, ...] = (
    ChannelDescriptor(
        key="accelerometer",
        label="Accélération (g)",
        axis_labels=("X", "Y", "Z"),
        decimals=4,
        signed=True,
    ),
    ChannelDescriptor(
        key="gyroscope",
        label="Vitesse angulaire (°/s)",
        axis_labels=("X", "Y", "Z"),
        decimals=2,
        signed=True,
        unverified_reason="valeur non vérifiée : plage 490 °/s reprise d'un VI",
    ),
    ChannelDescriptor(
        key="magnetometer",
        label="Champ magnétique (µT)",
        axis_labels=("X", "Y", "Z"),
        decimals=2,
        signed=True,
        unverified_reason="valeur non vérifiée : facteur 2^15 contre 2^16 non tranché",
    ),
    ChannelDescriptor(
        key="lidar",
        label="Distance lidar (mm)",
        axis_labels=("d",),
        decimals=0,
        signed=False,
        unverified_reason="valeur non vérifiée : unité mm non mesurée",
        note="canal provisoire : concept distinct à venir",
    ),
)


@dataclass(frozen=True)
class ChannelReading:
    key: str
    label: str
    axis_labels: Tuple[str, ...]
    values: Tuple[str, ...]
    unverified_reason: str
    note: str

    @property
    def unverified(self) -> bool:
        return bool(self.unverified_reason)


@dataclass(frozen=True)
class InertialSensorReadingViewModel:
    channels: Tuple[ChannelReading, ...]
    measured_rate_hz: Optional[float]
    sample_count: int


def _format(descriptor: ChannelDescriptor, raw: Optional[Tuple[float, ...]]) -> Tuple[str, ...]:
    if raw is None:
        return tuple(ABSENT for _ in descriptor.axis_labels)
    sign = "+" if descriptor.signed else ""
    return tuple(f"{v:{sign}.{descriptor.decimals}f}" for v in raw)


def build_reading_view_model(
    acceleration_g: Optional[Tuple[float, float, float]],
    angular_rate_dps: Optional[Tuple[float, float, float]],
    magnetic_field_ut: Optional[Tuple[float, float, float]],
    lidar_distance_mm: Optional[float],
    measured_rate_hz: Optional[float],
    sample_count: int,
) -> InertialSensorReadingViewModel:
    raw_by_key = {
        "accelerometer": acceleration_g,
        "gyroscope": angular_rate_dps,
        "magnetometer": magnetic_field_ut,
        "lidar": None if lidar_distance_mm is None else (lidar_distance_mm,),
    }
    channels = tuple(
        ChannelReading(
            key=d.key,
            label=d.label,
            axis_labels=d.axis_labels,
            values=_format(d, raw_by_key[d.key]),
            unverified_reason=d.unverified_reason,
            note=d.note,
        )
        for d in CHANNELS
    )
    return InertialSensorReadingViewModel(
        channels=channels, measured_rate_hz=measured_rate_hz, sample_count=sample_count
    )
