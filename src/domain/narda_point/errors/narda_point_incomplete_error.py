"""Refused promise: a field point holds exactly N samples (see narda_point_incomplete_error_intention.md)."""


class NardaPointIncompleteError(ValueError):
    def __init__(self, narda_point_id, expected: int, received: int, what: str = "samples"):
        super().__init__(f"NardaPoint {narda_point_id}: expected exactly {expected} {what}, got {received}")
        self.narda_point_id = narda_point_id
        self.expected = expected
        self.received = received
        self.what = what
