from enum import Enum


class SphereId(Enum):
    """
    Identity of one of the 4 excitation spheres, with its physical quadrant.

    Quadrant convention matches Motion Control's position_visualizer.py:
    S1=top-left (x_neg,y_pos), S3=top-right (x_pos,y_pos),
    S4=bottom-left (x_neg,y_neg), S2=bottom-right (x_pos,y_neg).
    """

    S1 = ("neg", "pos")
    S2 = ("pos", "neg")
    S3 = ("pos", "pos")
    S4 = ("neg", "neg")

    def __init__(self, x_sign: str, y_sign: str):
        self.x_sign = x_sign
        self.y_sign = y_sign

    @property
    def electronic_pair(self) -> "SphereId":
        """The other sphere driven by the same DDS differential output (S1<->S2, S3<->S4)."""
        return _ELECTRONIC_PAIRS[self]

    @property
    def dds_channel(self) -> int:
        """
        Physical DDS generator (1 or 2) driving this sphere.

        Confirmed on oscilloscope (2026-07-30): channel 1 (DDS1 generator)
        drives S3/S4, channel 2 (DDS2 generator) drives S1/S2 — the reverse
        of the naive "channel N -> sphere N" assumption.
        """
        return _DDS_CHANNEL[self]

    @property
    def is_direct_output(self) -> bool:
        """True if this sphere carries its DDS's direct (0°) output, False if
        it carries the complementary (+180°) differential output."""
        return _IS_DIRECT_OUTPUT[self]


_ELECTRONIC_PAIRS = {
    SphereId.S1: SphereId.S2,
    SphereId.S2: SphereId.S1,
    SphereId.S3: SphereId.S4,
    SphereId.S4: SphereId.S3,
}

_DDS_CHANNEL = {
    SphereId.S1: 2,
    SphereId.S2: 2,
    SphereId.S3: 1,
    SphereId.S4: 1,
}

_IS_DIRECT_OUTPUT = {
    SphereId.S1: False,  # complementary (DDS2-bar)
    SphereId.S2: True,   # direct (DDS2)
    SphereId.S3: False,  # complementary (DDS1-bar)
    SphereId.S4: True,   # direct (DDS1)
}
