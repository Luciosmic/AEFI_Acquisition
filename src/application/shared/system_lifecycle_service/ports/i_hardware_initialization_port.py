"""
Hardware Initialization Port Interface

Responsibility:
- Abstract interface for initializing, verifying, and closing hardware connections.
- Allows SystemLifecycleService to orchestrate hardware startup without knowing
  specific details (controller classes, DLLs, etc.).

Rationale:
- Decouples application lifecycle logic from infrastructure implementations.
- Supports different hardware setups (real, mock, legacy).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class IHardwareInitializationPort(ABC):
    """
    Port interface for hardware initialization and teardown.

    Responsibility:
        - Déclarer `initialize_all() → Dict[str, Any]` : initialise tous les périphériques, retourne les ressources créées.
        - Déclarer `verify_all() → bool` : vérifie optionnellement la connectivité de tous les périphériques.
        - Déclarer `close_all()` : ferme toutes les connexions de façon gracieuse.

    Rationale:
        Abstraire la séquence d'initialisation et de fermeture de tous les périphériques hardware (MCU, Arcus, AD9106, ADS131A04) derrière un port unique. Permet à `SystemStartupApplicationService` d'orchestrer le démarrage sans connaître les drivers concrets.

    Design:
        - **Port outbound** dans `system_lifecycle_service/`.
        - Implémenté typiquement par un `CompositeHardwareInitializationPort` qui agrège les initialiseurs individuels (MCU, Arcus).

        - `verify_all()` ne doit pas dépendre d'une calibration : l'adaptateur Arcus vérifie le contrôleur en impulsions brutes pour que l'absence de conversion mm/impulsion ne ferme pas l'application.
    """

    @abstractmethod
    def initialize_all(self) -> Dict[str, Any]:
        """
        Initialize all hardware components.

        Returns:
            Dict of initialized resources (controllers, ports, etc.),
            keyed by name/id.
        
        Raises:
            Exception: If initialization fails.
        """
        pass

    @abstractmethod
    def verify_all(self) -> bool:
        """
        Verify that all hardware components are connected and responsive.

        Returns:
            True if verification succeeds.
        
        Raises:
            Exception: If verification fails or is not supported.
        """
        pass

    @abstractmethod
    def close_all(self) -> None:
        """
        Close all hardware connections and release resources.

        Raises:
            Exception: If closure fails.
        """
        pass
