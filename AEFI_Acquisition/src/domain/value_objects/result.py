"""
OperationResult type for explicit error handling.

Responsibility:
- Encapsulate success/failure states without exceptions
- Force explicit error handling at call sites
- Prevent UI crashes from unhandled exceptions

Rationale:
- Exceptions are control flow, not data
- UI should display errors, not catch exceptions
- Makes error handling explicit and type-safe

Design:
- Generic OperationResult[T, E] where T is success type, E is error type
- Immutable value object
- Pattern matching friendly
- Ubiquitous language: represents the outcome of any domain operation
"""

from dataclasses import dataclass
from typing import Generic, TypeVar, Optional

T = TypeVar('T')  # Success type
E = TypeVar('E')  # Error type


@dataclass(frozen=True)
class OperationResult(Generic[T, E]):
    """
    Ubiquitous type that represents the outcome of any domain operation.
    Either success (Ok) or failure (Err).
    
    Usage:
        result = some_operation()
        if result.is_success:
            data = result.value  # Safe access
        else:
            error = result.error  # Safe access
    """
    
    _is_success: bool
    _value: Optional[T] = None
    _error: Optional[E] = None
    
    @classmethod
    def ok(cls, value: T) -> 'OperationResult[T, E]':
        """Create a successful operation result."""
        return cls(_is_success=True, _value=value, _error=None)
    
    @classmethod
    def fail(cls, error: E) -> 'OperationResult[T, E]':
        """Create a failed operation result."""
        return cls(_is_success=False, _value=None, _error=error)
    
    @property
    def is_success(self) -> bool:
        """Check if operation was successful."""
        return self._is_success
    
    @property
    def is_failure(self) -> bool:
        """Check if operation failed."""
        return not self._is_success
    
    @property
    def value(self) -> T:
        """Get the success value. Raises if not successful."""
        if not self._is_success:
            raise ValueError("Cannot get value from failed OperationResult. Check is_success first.")
        return self._value
    
    @property
    def error(self) -> E:
        """Get the error value. Raises if successful."""
        if self._is_success:
            raise ValueError("Cannot get error from successful OperationResult. Check is_failure first.")
        return self._error
    
    def get_value_or(self, default: T) -> T:
        """Get value if successful, otherwise return default."""
        return self._value if self._is_success else default
    
    def get_error_or(self, default: E) -> E:
        """Get error if failed, otherwise return default."""
        return self._error if not self._is_success else default

