"""Refused promise: an acquired field point is immutable (see narda_point_already_acquired_error_intention.md)."""


class NardaPointAlreadyAcquiredError(ValueError):
    def __init__(self, narda_point_id):
        super().__init__(f"NardaPoint {narda_point_id} is already acquired")
        self.narda_point_id = narda_point_id
