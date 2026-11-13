"""
Hardware Configuration Provider Port

Responsibility:
- Define an abstract interface for discovering hardware configuration parameters
- Allow application services to query available hardware and its actionable parameters
  without depending on concrete infrastructure implementations

Rationale:
- Hexagonal Architecture: application depends on ports, infrastructure on adapters
- Centralizes how hardware declares its configurable parameters
- Enables testing with mock hardware providers

Design:
- Protocol-like interface (duck-typing friendly)
- Implemented by infrastructure hardware adapters
- Exposes ActionableHardwareParametersSpec list for each hardware
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from domain.shared_kernel.value_objects.hardware_configuration.hardware_advanced_parameter_schema import HardwareAdvancedParameterSchema


class IHardwareAdvancedConfigurator(ABC):
    """
    Port interface for Advanced Hardware Configuration.

    Responsibility:
    - Allow users to access and modify "Advanced" hardware parameters.
    - These are typically low-level settings (PID gains, register values)
      that the Domain layer usually abstracts away.
    - This interface allows a generic UI to expose these settings without
      hard-coupling to specific hardware.

    Responsibility:
        - Déclarer les propriétés `hardware_id: str` et `display_name: str` pour l'identification.
        - Déclarer `get_parameter_specs() → List[HardwareAdvancedParameterSchema]` (méthode de classe).
        - Déclarer `apply_config(config: Dict[str, Any])`, `save_config_as_default(config: Dict[str, Any])`
          et `reset_to_default()` — ce dernier est le pendant de `save_config_as_default` : celui-ci
          capture une baseline, `reset_to_default()` y revient (doit réappliquer au hardware réel, pas
          seulement réécrire le fichier "last").

    Rationale:
        Définir le contrat que chaque périphérique hardware avancé (Arcus, MCU, AD9106, ADS131A04) doit respecter pour être configurable depuis le `HardwareConfigurationService`. Permet au service d'agréger des configurateurs hétérogènes via un type commun.

    Design:
        - **ABC** avec `@abstractmethod` exclusivement.
        - `hardware_id` sert de clé dans le dictionnaire du `HardwareConfigurationService`.
        - `get_parameter_specs()` est une méthode de classe statique : le service l'appelle via `type(provider).get_parameter_specs()` pour obtenir le schéma indépendamment de l'état de l'instance.
    """

    @property
    @abstractmethod
    def hardware_id(self) -> str:
        """
        Stable identifier for the hardware.

        Responsibility:
        - Unique key used by application services to reference this hardware

        Example:
        - "arcus_performax_4ex"
        - "ad9106_dds"
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def display_name(self) -> str:
        """
        Human-readable name for the hardware.

        Used by UI when listing available hardware.
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def get_parameter_specs() -> List[HardwareAdvancedParameterSchema]:
        """
        Return actionable parameter specifications for this hardware.

        Returns:
            List of HardwareAdvancedParameterSchema
        """
        raise NotImplementedError

    @abstractmethod
    def apply_config(self, config: Dict[str, Any]) -> None:
        """
        Apply configuration values to the underlying hardware.

        Responsibility:
        - Bridge high-level config dictionaries to concrete hardware APIs

        Args:
            config: Dictionary of parameter values keyed by spec.name
        """
        raise NotImplementedError

    @abstractmethod
    def save_config_as_default(self, config: Dict[str, Any]) -> None:
        """
        Save the provided configuration as the new default configuration.

        Responsibility:
        - Persist the configuration to a storage (e.g., JSON file) so it is loaded on next startup.

        Args:
            config: Dictionary of parameter values keyed by spec.name
        """
        raise NotImplementedError

    @abstractmethod
    def reset_to_default(self) -> None:
        """
        Discard the current applied/last state and re-apply the saved default
        configuration — the counterpart to save_config_as_default(): that
        captures a baseline, this reverts to it. Must apply to the real
        hardware (not just update the on-disk "last" state) and behave
        exactly as if apply_config() had been called with the default values.
        """
        raise NotImplementedError
