"""Refused promise: a frequency point holds exactly N samples (see frequency_point_incomplete_error_intention.md)."""


class FrequencyPointIncompleteError(ValueError):
    def __init__(self, frequency_sweep_id, frequency_hz: float, expected: int, received: int):
        super().__init__(
            f"FrequencySweep {frequency_sweep_id}: {frequency_hz} Hz expected exactly {expected} samples, got {received}"
        )
        self.frequency_sweep_id = frequency_sweep_id
        self.frequency_hz = frequency_hz
        self.expected = expected
        self.received = received
