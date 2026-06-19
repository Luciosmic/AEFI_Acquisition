# Compatibility shim — canonical definition has moved to scan_export_service/ports/
from application.services.scan_export_service.ports.i_scan_export_port import IScanExportPort
__all__ = ["IScanExportPort"]
