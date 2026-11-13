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
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement


class IAcquisitionPort(ABC):
    """
    Port interface for data acquisition.

    This is an abstraction that allows the domain service to acquire
    voltage measurements without depending on specific hardware (ADC, etc.).

    Implemented by infrastructure adapters (e.g., ADS131A04Adapter).

    Responsibility:
        - Déclarer `acquire_sample() → AefiVoltageMeasurement` (ou équivalent) comme méthode abstraite.
        - Servir de frontière entre la couche Application et l'infrastructure d'acquisition.

    Rationale:
        Définir le contrat outbound que `ScanApplicationService` utilise pour acquérir un échantillon de mesure. Ce port découple le service applicatif du chip ADC concret (ADS131A04) et rend les tests de scan possibles sans hardware.

    Design:
        - **Port outbound** (Application → Infrastructure) : placé dans le dossier du service consommateur (`scan_application_service/`).
        - **ABC avec `@abstractmethod`** : contrat pur, zéro logique d'implémentation.
        - Implémenté par `AdapterIAcquisitionPortADS131A04` (Real) et `AdapterMockIAcquisitionPort` (Fake/Mock).
    """
    
    @abstractmethod
    def acquire_sample(self) -> AefiVoltageMeasurement:
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
    def is_ready(self) -> bool:
        """
        Check if acquisition system is ready to acquire data.
        
        Returns:
            True if ready, False otherwise
        """
        pass
