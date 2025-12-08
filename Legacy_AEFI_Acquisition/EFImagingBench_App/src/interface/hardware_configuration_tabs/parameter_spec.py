"""
Data-driven UI generation for hardware configuration.

Responsibility:
- Define parameter specifications for UI generation
- Enable adapters to expose their UI requirements
- Provide type-safe configuration

Rationale:
- DDD: Infrastructure (adapters) defines UI constraints
- Single source of truth for parameter metadata
- Automatic validation from specs

Design:
- Dataclass for type safety
- Immutable specs
- Supports multiple widget types
"""

from dataclasses import dataclass
from typing import Any, Optional, Tuple, List


@dataclass(frozen=True)
class ParameterSpec:
    """
    Specification for a configurable parameter.
    
    Used to generate UI widgets automatically from adapter requirements.
    
    Example:
        >>> spec = ParameterSpec(
        ...     name='freq_hz',
        ...     label='Frequency',
        ...     type='spinbox',
        ...     default=1000,
        ...     range=(100, 10000),
        ...     unit='Hz'
        ... )
    """
    
    # Identity
    name: str  # Internal parameter name
    label: str  # User-facing label
    
    # Widget type
    type: str  # 'spinbox', 'slider', 'combo', 'checkbox', 'lineedit'
    
    # Value constraints
    default: Any  # Default value
    range: Optional[Tuple[int, int]] = None  # (min, max) for spinbox/slider
    options: Optional[List[str]] = None  # Options for combo
    
    # Display
    unit: Optional[str] = None  # Unit for display (Hz, V, °, etc.)
    tooltip: Optional[str] = None  # Tooltip text
    
    # Validation
    required: bool = True  # Is this parameter required?
    
    def validate_value(self, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate a value against this spec.
        
        Args:
            value: Value to validate
        
        Returns:
            (is_valid, error_message)
        """
        # Required check
        if self.required and value is None:
            return False, f"{self.label} is required"
        
        # Range check for numeric types
        if self.range and self.type in ('spinbox', 'slider'):
            if not (self.range[0] <= value <= self.range[1]):
                return False, f"{self.label} must be between {self.range[0]} and {self.range[1]}"
        
        # Options check for combo
        if self.options and self.type == 'combo':
            if str(value) not in self.options:
                return False, f"{self.label} must be one of {self.options}"
        
        return True, None
