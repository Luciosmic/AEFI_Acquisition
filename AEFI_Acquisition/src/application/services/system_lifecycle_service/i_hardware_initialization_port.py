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
