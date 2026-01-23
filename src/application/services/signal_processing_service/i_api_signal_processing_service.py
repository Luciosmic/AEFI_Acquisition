"""
Application: Signal Processing Service API Interface

Responsibility:
    Contrat abstrait définissant les opérations publiques exposées par la couche Application.
    Interface consommée par les Adapters primaires (UI, CLI, HTTP).

Rationale:
    - Interface API Application (inbound) - distincte des Ports Infrastructure (outbound)
    - Permet aux Adapters primaires d'interagir avec l'Application sans dépendre de l'implémentation
    - Convention `i_api_` pour éviter la confusion avec les ports infrastructure

Design:
    - Abstract Base Class (ABC)
    - Pure interface, no implementation
    - Application layer provides concrete implementation (SignalProcessingApiService)
"""
from abc import ABC, abstractmethod
from typing import Optional
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from domain.value_objects.acquisition.voltage_measurement_reference import VoltageMeasurementReference
from domain.value_objects.geometric.position_2d import Position2D
from domain.value_objects.excitation.excitation_parameters import ExcitationParameters


class IApiSignalProcessingService(ABC):
    """
    Interface API pour le signal processing.
    
    Contrat abstrait définissant les opérations publiques exposées par la couche Application.
    Cette interface est consommée par les Adapters primaires (UI/view_model, CLI, HTTP).
    
    Distinction:
    - Port Infrastructure (`i_repository.py`) : Interface Domain→Infrastructure (outbound)
    - Interface API (`i_api_*`) : Contrat Application→Adapters (inbound)
    """
    
    # ========================================================================
    # API Methods - Processing
    # ========================================================================
    
    @abstractmethod
    def process_measurement(self, measurement: VoltageMeasurement) -> VoltageMeasurement:
        """
        Process a measurement with current calibration.
        
        Args:
            measurement: Raw voltage measurement
        
        Returns:
            Processed voltage measurement
        """
        pass
    
    # ========================================================================
    # API Methods - Calibration
    # ========================================================================
    
    @abstractmethod
    def calibrate_noise(
        self,
        position: Optional[Position2D] = None,
        excitation: Optional[ExcitationParameters] = None,
        reference_measurement: Optional[VoltageMeasurement] = None
    ) -> None:
        """
        Calibrate noise offset.
        
        Args:
            position: Optional target position (used if reference_measurement not provided)
            excitation: Optional excitation parameters (default: off, used if reference_measurement not provided)
            reference_measurement: Optional measurement to use as noise offset. If None, orchestrates acquisition.
        """
        pass
    
    @abstractmethod
    def calibrate_phase(
        self,
        position: Optional[Position2D] = None,
        excitation: Optional[ExcitationParameters] = None,
        reference_measurement: Optional[VoltageMeasurement] = None
    ) -> None:
        """
        Calibrate phase angles.
        
        Args:
            position: Optional target position (used if reference_measurement not provided)
            excitation: Excitation parameters (required if reference_measurement not provided, should be on)
            reference_measurement: Optional measurement to use for phase calculation. If None, orchestrates acquisition.
        """
        pass
    
    @abstractmethod
    def calibrate_primary(
        self,
        position: Optional[Position2D] = None,
        excitation: Optional[ExcitationParameters] = None,
        reference_measurement: Optional[VoltageMeasurement] = None
    ) -> None:
        """
        Calibrate primary field offset.
        
        Args:
            position: Optional target position (used if reference_measurement not provided)
            excitation: Excitation parameters (required if reference_measurement not provided)
            reference_measurement: Optional measurement to use as primary offset. If None, orchestrates acquisition.
        """
        pass
    
    @abstractmethod
    def perform_automatic_calibration(
        self,
        target_position: Optional[Position2D],
        excitation_params: ExcitationParameters
    ) -> VoltageMeasurementReference:
        """
        Perform complete automatic calibration sequence.
        
        Args:
            target_position: Optional target position for calibration
            excitation_params: Excitation parameters for phase and primary calibration
        
        Returns:
            Complete VoltageMeasurementReference
        """
        pass
    
    # ========================================================================
    # API Methods - Reference Management
    # ========================================================================
    
    @abstractmethod
    def get_current_reference(self) -> Optional[VoltageMeasurementReference]:
        """
        Get current calibration reference.
        
        Returns:
            Current VoltageMeasurementReference or None
        """
        pass
    
    @abstractmethod
    def set_reference(self, reference: VoltageMeasurementReference) -> None:
        """
        Set calibration reference.
        
        Args:
            reference: VoltageMeasurementReference to use
        """
        pass
    
    @abstractmethod
    def reset_calibration(self) -> None:
        """Reset all calibration parameters."""
        pass
    
    # ========================================================================
    # API Methods - Persistence
    # ========================================================================
    
    @abstractmethod
    def save_reference(
        self,
        name: Optional[str] = None,
        reference: Optional[VoltageMeasurementReference] = None
    ) -> str:
        """
        Save calibration reference to repository.
        
        Args:
            name: Optional name/identifier. If None, generates from timestamp.
            reference: Optional reference to save. If None, uses current reference.
        
        Returns:
            Name/identifier of saved reference
        
        Raises:
            ValueError: If repository not configured or no reference to save
        """
        pass
    
    @abstractmethod
    def load_reference(self, name: str) -> Optional[VoltageMeasurementReference]:
        """
        Load calibration reference from repository.
        
        Args:
            name: Identifier/name of reference to load
        
        Returns:
            VoltageMeasurementReference if found, None otherwise
        
        Raises:
            ValueError: If repository not configured
        """
        pass
    
    @abstractmethod
    def load_latest_reference(self) -> Optional[VoltageMeasurementReference]:
        """
        Load most recent calibration reference from repository.
        
        Returns:
            Most recent VoltageMeasurementReference if any exist, None otherwise
        
        Raises:
            ValueError: If repository not configured
        """
        pass
    
    @abstractmethod
    def list_saved_references(self) -> list[str]:
        """
        List all saved reference names.
        
        Returns:
            List of reference names/identifiers
        
        Raises:
            ValueError: If repository not configured
        """
        pass
    
    @abstractmethod
    def delete_reference(self, name: str) -> bool:
        """
        Delete a saved reference.
        
        Args:
            name: Identifier/name of reference to delete
        
        Returns:
            True if deleted, False if not found
        
        Raises:
            ValueError: If repository not configured
        """
        pass
    
    # ========================================================================
    # API Methods - Status/Info
    # ========================================================================
    
    @abstractmethod
    def get_calibration_status(self) -> dict:
        """
        Get current calibration status.
        
        Returns:
            Dict with calibration status information
        """
        pass
