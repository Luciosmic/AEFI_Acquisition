"""Refused promise: a scan starts only once, from PENDING."""


class ScanAlreadyStartedError(ValueError):
    def __init__(self, scan_id, state):
        super().__init__(f"Scan {scan_id} cannot start from state {state.value}")
        self.scan_id = scan_id
