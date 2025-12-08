"""
Application Layer: Custom Scan Service

Responsibility:
    Manages user-defined custom scan sequences.
    Allows arbitrary point sequences for specialized measurements.

Rationale:
    Some experiments require non-standard scan patterns.
    Service provides flexibility while maintaining scan lifecycle management.

Design:
    - Builder pattern for sequence construction
    - Validates custom sequences before execution
    - Reuses standard acquisition infrastructure
"""
from typing import Any
from uuid import UUID


class CustomScanService:
    """Service for custom scan operations."""
    
    def __init__(self):
        """Initialize custom scan service with required dependencies."""
        pass
    
    def define_custom_sequence(self, name: str) -> Any:
        """
        Create new custom scan sequence.
        
        Responsibility:
            Initialize builder for custom point sequence.
        
        Rationale:
            User needs to define sequence before adding points.
        
        Design:
            - Create sequence builder
            - Return builder for fluent API
        
        Args:
            name: Human-readable sequence name
            
        Returns:
            CustomSequenceBuilder for adding points
        """
        pass
    
    def add_scan_point(self, sequence: Any, point: tuple[float, float]) -> None:
        """
        Add point to custom sequence.
        
        Responsibility:
            Append position to sequence in order.
        
        Rationale:
            Build sequence incrementally, point by point.
        
        Design:
            - Validate point is within workspace
            - Append to sequence
            - No return (builder pattern)
        
        Args:
            sequence: CustomSequenceBuilder instance
            point: (x, y) position in mm
        """
        pass
    
    def execute_custom_scan(self, sequence: Any) -> UUID:
        """
        Execute custom scan sequence.
        
        Responsibility:
            Run scan following user-defined point order.
        
        Rationale:
            Execute arbitrary sequences while maintaining
            standard scan lifecycle and data structure.
        
        Design:
            - Validate sequence is complete
            - Execute point-by-point acquisition
            - Return scan ID for tracking
        
        Args:
            sequence: Completed custom sequence
            
        Returns:
            UUID of created scan
        """
        pass
