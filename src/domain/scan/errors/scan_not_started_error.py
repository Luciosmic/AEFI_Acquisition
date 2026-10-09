"""Refused promise: no point is accepted before the scan starts."""


class ScanNotStartedError(ValueError):
    def __init__(self, scan_id, aefi_point_id):
        super().__init__(f"Scan {scan_id} is not started, cannot accept point {aefi_point_id}")
        self.scan_id = scan_id
        self.aefi_point_id = aefi_point_id
