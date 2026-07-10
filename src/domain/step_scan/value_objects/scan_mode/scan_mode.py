"""
Compatibility shim for legacy code importing:

    from domain.step_scan.value_objects.scan_mode.scan_mode import ScanMode

In the refactored model, `ScanPattern` is the canonical enum for scan
patterns. We alias ScanMode to ScanPattern to preserve behaviour.
"""

from domain.step_scan.value_objects.scan_pattern.scan_pattern import ScanPattern as ScanMode

__all__ = ["ScanMode"]


