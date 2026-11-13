"""FrequencySweepRole (see frequency_sweep_role_intention.md)."""

from enum import Enum


class FrequencySweepRole(Enum):
    """What a frequency sweep characterizes. The value is the stable
    identifier written in exports."""

    # Table at its lowest position, no object: the instrument's own response.
    INSTRUMENT_REFERENCE = "instrument_reference"
    # Table at the working height, no object: what the bench adds at that height.
    BACKGROUND = "background"
    # Same table height as the background, object on the table.
    OBJECT_MEASUREMENT = "object_measurement"

    @property
    def measures_an_object(self) -> bool:
        return self is FrequencySweepRole.OBJECT_MEASUREMENT
