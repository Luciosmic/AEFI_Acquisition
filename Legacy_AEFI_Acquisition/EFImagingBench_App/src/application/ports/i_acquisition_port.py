"""
Acquisition Port Interface

Responsibility:
- Define abstract interface for data acquisition operations
- Allow domain service to acquire data without knowing infrastructure details

Rationale:
- Hexagonal Architecture: Port pattern
- Domain service depends on abstraction, not concrete implementation
- Enables testing with mock implementations

Design:
- Abstract Base Class (ABC)
- Pure interface, no implementation
- Infrastructure layer provides concrete adapter (e.g., ADS131A04Adapter)
"""

from abc import ABC, abstractmethod
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from domain.value_objects.measurement_uncertainty import MeasurementUncertainty


class IAcquisitionPort(ABC):
    """
    Port interface for data acquisition.
    
    This is an abstraction that allows the domain service to acquire
    voltage measurements without depending on specific hardware (ADC, etc.).
    
    Implemented by infrastructure adapters (e.g., ADS131A04Adapter).
    """
    
    @abstractmethod
    def acquire_sample(self) -> VoltageMeasurement:
        """
        Acquire a single voltage measurement sample.
        
        The sample is already hardware-averaged (via ADC OSR).
        
        Returns:
            Single voltage measurement with all 6 components
        
        Raises:
            AcquisitionError: If acquisition fails
        """
        pass
    
    @abstractmethod
    def configure_for_uncertainty(self, uncertainty: MeasurementUncertainty) -> None:
        """
        Configure acquisition hardware to achieve target measurement uncertainty.
        
        The infrastructure adapter translates the domain concept (uncertainty)
        into hardware configuration (gain, OSR, sampling rate, etc.).
        
        Args:
            uncertainty: Target measurement uncertainty from domain
        
        Raises:
            ConfigurationError: If configuration fails or is invalid
        """
        pass
    
    @abstractmethod
    def is_ready(self) -> bool:
        """
        Check if acquisition system is ready to acquire data.
        
        Returns:
            True if ready, False otherwise
        """
        pass
