"""Refused promise: an acquired point is immutable (see aefi_point_already_acquired_error_intention.md)."""


class AefiPointAlreadyAcquiredError(ValueError):
    def __init__(self, aefi_point_id):
        super().__init__(f"AefiPoint {aefi_point_id} is already acquired")
        self.aefi_point_id = aefi_point_id
