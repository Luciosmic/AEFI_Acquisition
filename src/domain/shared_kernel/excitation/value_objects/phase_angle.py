from dataclasses import dataclass

DDS_REGISTER_RANGE = 65536  # AD9106 16-bit phase register, 0-65535 = 0-360°


@dataclass(frozen=True)
class PhaseAngle:
    """
    Immutable phase angle in degrees, normalized to [0, 360).
    """
    degrees: float

    def __post_init__(self):
        object.__setattr__(self, "degrees", self.degrees % 360.0)

    def opposite(self) -> "PhaseAngle":
        """The complementary phase (+180°) of a differential DDS output pair."""
        return PhaseAngle(self.degrees + 180.0)

    def difference_from(self, other: "PhaseAngle") -> float:
        """Signed shortest angular difference (self - other), in (-180, 180]."""
        diff = (self.degrees - other.degrees + 180.0) % 360.0 - 180.0
        return 180.0 if diff == -180.0 else diff

    @staticmethod
    def from_register(value: int) -> "PhaseAngle":
        """Convert an AD9106 16-bit phase register value (0-65535) to degrees."""
        return PhaseAngle(value / DDS_REGISTER_RANGE * 360.0)

    def to_register(self) -> int:
        """Convert to an AD9106 16-bit phase register value (0-65535)."""
        return int(round(self.degrees / 360.0 * DDS_REGISTER_RANGE)) % DDS_REGISTER_RANGE
