"""
Compatibility shim for legacy imports:

    from application.ports.i_scan_output_port import IScanOutputPort

The canonical definition now lives in
`application.services.scan_application_service.i_scan_output_port`.
"""

from application.services.scan_application_service.ports.i_scan_output_port import (
    IScanOutputPort,
)

__all__ = ["IScanOutputPort"]



