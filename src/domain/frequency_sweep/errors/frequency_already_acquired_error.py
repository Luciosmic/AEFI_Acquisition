"""Refused promise: each grid frequency is acquired once (see frequency_already_acquired_error_intention.md)."""


class FrequencyAlreadyAcquiredError(ValueError):
    def __init__(self, frequency_sweep_id, frequency_hz: float):
        super().__init__(f"FrequencySweep {frequency_sweep_id}: {frequency_hz} Hz is already acquired")
        self.frequency_sweep_id = frequency_sweep_id
        self.frequency_hz = frequency_hz
