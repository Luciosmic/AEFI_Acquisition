"""Refused promise: a completed scan accepts no new acquisition."""


class ScanAlreadyCompletedError(ValueError):
    def __init__(self, scan_id, acquisition_id):
        super().__init__(f"Scan {scan_id} is completed, cannot accept new acquisition {acquisition_id}")
        self.scan_id = scan_id
        self.acquisition_id = acquisition_id
