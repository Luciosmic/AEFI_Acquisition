"""
Shared Kernel for Domain layer.

Responsibility:
- Provide shared value objects (geometry, units, etc.) that are used
  across multiple bounded contexts (Scan, TestBench, AefiDevice, Physics).
- Provide ubiquitous types like OperationResult for consistent error handling.

Notes:
- Implementation for some types still lives in `value_objects` packages;
  this module re-exports them to stabilise a common import path.
"""

from .operation_result import OperationResult

__all__ = ['OperationResult']


