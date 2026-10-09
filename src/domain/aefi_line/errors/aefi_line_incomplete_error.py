"""Refused promise: a line holds exactly its expected grid points (see aefi_line_incomplete_error_intention.md)."""


class AefiLineIncompleteError(ValueError):
    def __init__(self, aefi_line_id, expected: int, missing_indices, received: int):
        super().__init__(
            f"AefiLine {aefi_line_id}: expected grid points 0..{expected - 1} exactly once, "
            f"got {received} (missing {list(missing_indices)})"
        )
        self.aefi_line_id = aefi_line_id
        self.expected = expected
        self.missing_indices = tuple(missing_indices)
        self.received = received
