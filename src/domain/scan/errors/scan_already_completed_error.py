"""Refused promise: a completed scan accepts no new point."""


class ScanAlreadyCompletedError(ValueError):
    def __init__(self, scan_id, aefi_point_id):
        super().__init__(f"Scan {scan_id} is completed, cannot accept new point {aefi_point_id}")
        self.scan_id = scan_id
        self.aefi_point_id = aefi_point_id
