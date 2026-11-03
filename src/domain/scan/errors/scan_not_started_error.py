"""Refused promise: no point is accepted before the scan starts."""


class ScanNotStartedError(ValueError):
    def __init__(self, scan_id, acquisition_id):
        super().__init__(f"Scan {scan_id} is not started, cannot accept acquisition {acquisition_id}")
        self.scan_id = scan_id
        self.acquisition_id = acquisition_id
