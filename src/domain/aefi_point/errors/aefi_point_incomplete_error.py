"""Refused promise: a point holds exactly N valid samples (see aefi_point_incomplete_error_intention.md)."""


class AefiPointIncompleteError(ValueError):
    def __init__(self, aefi_point_id, expected: int, received: int):
        super().__init__(f"AefiPoint {aefi_point_id}: expected exactly {expected} valid samples, got {received}")
        self.aefi_point_id = aefi_point_id
        self.expected = expected
        self.received = received
