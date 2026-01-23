"""
Domain: Voltage Measurement Reference Repository Interface

Responsibility:
    Define abstract interface for persisting VoltageMeasurementReference.
    Follows DDD Repository pattern.

Rationale:
    - Hexagonal Architecture: Port pattern
    - Domain depends on abstraction, not infrastructure details
    - Enables testing with mock implementations

Design:
    - Abstract Base Class (ABC)
    - Pure interface, no implementation
    - Infrastructure layer provides concrete implementation
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from domain.value_objects.acquisition.voltage_measurement_reference import VoltageMeasurementReference


class IVoltageMeasurementReferenceRepository(ABC):
    """
    Port interface for persisting voltage measurement references.
    
    This abstraction allows the domain to save/load calibration references
    without depending on specific storage implementation (JSON, database, etc.).
    
    Implemented by infrastructure adapters (e.g., JsonVoltageMeasurementReferenceRepository).
    """
    
    @abstractmethod
    def save(self, reference: VoltageMeasurementReference, name: Optional[str] = None) -> str:
        """
        Persist a voltage measurement reference.
        
        Args:
            reference: VoltageMeasurementReference to save
            name: Optional name/identifier for the reference. If None, generates a name from timestamp.
        
        Returns:
            Identifier/name of the saved reference
        """
        pass
    
    @abstractmethod
    def load(self, name: str) -> Optional[VoltageMeasurementReference]:
        """
        Load a voltage measurement reference by name.
        
        Args:
            name: Identifier/name of the reference to load
        
        Returns:
            VoltageMeasurementReference if found, None otherwise
        """
        pass
    
    @abstractmethod
    def load_latest(self) -> Optional[VoltageMeasurementReference]:
        """
        Load the most recent voltage measurement reference.
        
        Returns:
            Most recent VoltageMeasurementReference if any exist, None otherwise
        """
        pass
    
    @abstractmethod
    def list_all(self) -> List[str]:
        """
        List all available reference names/identifiers.
        
        Returns:
            List of reference names/identifiers
        """
        pass
    
    @abstractmethod
    def delete(self, name: str) -> bool:
        """
        Delete a voltage measurement reference by name.
        
        Args:
            name: Identifier/name of the reference to delete
        
        Returns:
            True if deleted, False if not found
        """
        pass
