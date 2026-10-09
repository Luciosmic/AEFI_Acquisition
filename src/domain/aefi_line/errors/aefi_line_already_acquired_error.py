"""Refused promise: an acquired line is immutable (see aefi_line_already_acquired_error_intention.md)."""


class AefiLineAlreadyAcquiredError(ValueError):
    def __init__(self, aefi_line_id):
        super().__init__(f"AefiLine {aefi_line_id} is already acquired")
        self.aefi_line_id = aefi_line_id
