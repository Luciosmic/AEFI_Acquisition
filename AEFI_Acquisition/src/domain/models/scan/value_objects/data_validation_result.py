"""
Domain: Validation Result

Responsibility:
    Represents the result of a validation operation.

Rationale:
    Standard value object for validation results across the domain.
    Provides structured error and warning information.

Design:
    - Frozen dataclass (immutable)
    - Separates errors (blocking) from warnings (non-blocking)
"""
from dataclasses import dataclass, field
from typing import List

@dataclass(frozen=True)
class DataValidationResult:
    """Result of a data validation operation.
    
    Provides structured information about validation:
    - is_valid: Overall validation status
    - errors: Blocking issues that prevent operation
    - warnings: Non-blocking issues to be aware of
    """
    
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @classmethod
    def success(cls, warnings: List[str] = None) -> 'DataValidationResult':
        """Create a successful validation result."""
        return cls(is_valid=True, errors=[], warnings=warnings or [])
    
    @classmethod
    def failure(cls, errors: List[str], warnings: List[str] = None) -> 'DataValidationResult':
        """Create a failed validation result."""
        if not errors:
            raise ValueError("Failure must have at least one error")
        return cls(is_valid=False, errors=errors, warnings=warnings or [])
    
    def __bool__(self) -> bool:
        """Allow using DataValidationResult in boolean context."""
        return self.is_valid

