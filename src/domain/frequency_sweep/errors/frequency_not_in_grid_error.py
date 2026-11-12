"""Refused promise: a sweep only holds frequencies of its grid (see frequency_not_in_grid_error_intention.md)."""


class FrequencyNotInGridError(ValueError):
    def __init__(self, frequency_sweep_id, frequency_hz: float):
        super().__init__(f"FrequencySweep {frequency_sweep_id}: {frequency_hz} Hz is not a frequency of its grid")
        self.frequency_sweep_id = frequency_sweep_id
        self.frequency_hz = frequency_hz
