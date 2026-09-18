import logging
from typing import List, Dict, Any
from application.services.system_lifecycle_service.ports.i_hardware_initialization_port import IHardwareInitializationPort

logger = logging.getLogger(__name__)


class CompositeHardwareInitializationPort(IHardwareInitializationPort):
    """
    Aggregates multiple hardware initialization ports into one.
    Useful for initializing multiple subsystems (Arcus, MCU, etc.) via a single service call.
    """

    def __init__(self, initializers: List[IHardwareInitializationPort]):
        self._initializers = initializers

    def initialize_all(self) -> Dict[str, Any]:
        """
        Initialize all subsystems and aggregate their resources.

        Returns:
            Combined dict of all initialized resources.
        """
        all_resources = {}
        for i, initializer in enumerate(self._initializers):
            resources = initializer.initialize_all()
            # Merge resources with prefix to avoid collisions
            prefix = f"subsystem_{i}"
            for key, value in resources.items():
                all_resources[f"{prefix}_{key}"] = value
        logger.info("Initialized %d hardware subsystem(s)", len(self._initializers))
        return all_resources

    def verify_all(self) -> bool:
        """
        Verify all subsystems.

        Returns:
            True if all verifications succeed.
        """
        for i, initializer in enumerate(self._initializers):
            if not initializer.verify_all():
                logger.error("Hardware subsystem %d failed verification", i)
                return False
        return True

    def close_all(self) -> None:
        # Closing in reverse order is often safer (LIFO), but standard iteration is fine if independent.
        # We'll stick to order for now, or could do reversed(self._initializers).
        logger.info("Closing %d hardware subsystem(s) in reverse order", len(self._initializers))
        for initializer in reversed(self._initializers):
            initializer.close_all()
