"""Refused promise: a scan accepts acquisitions only from the sources it declared."""


class ScanSourceNotDeclaredError(ValueError):
    def __init__(self, scan_id, source, acquisition_id):
        super().__init__(f"Scan {scan_id} did not declare source '{source}', cannot accept acquisition {acquisition_id}")
        self.scan_id = scan_id
        self.source = source
        self.acquisition_id = acquisition_id
