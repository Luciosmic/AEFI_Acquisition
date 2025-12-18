"""
Scan Interactive Port

Compatibility shim for legacy imports:

    from interface.interactive.scan_interactive_port import IScanOutputPort

The canonical definition now lives in
`application.services.scan_application_service.ports.i_scan_output_port`.
"""

from src.application.services.scan_application_service.ports.i_scan_output_port import (
    IScanOutputPort,
)

__all__ = ["IScanOutputPort"]



