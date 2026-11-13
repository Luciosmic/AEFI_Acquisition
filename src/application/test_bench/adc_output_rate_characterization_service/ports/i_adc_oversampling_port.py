from abc import ABC, abstractmethod
from typing import Tuple

from domain.shared_kernel.operation_result import OperationResult


class IAdcOversamplingPort(ABC):
    """
    Responsibility:
    - Read and write the ADC oversampling ratio (OSR) in the chip's register,
      without persisting it as the operator's configuration.

    Rationale:
    - The ODR sweep changes the OSR temporarily and restores it; the
      operator's saved configuration must not follow.

    Design:
    - set_oversampling_ratio() returns a failure (not raises) for a value the
      chip does not accept or a write the MCU refuses.
    """

    @abstractmethod
    def get_oversampling_ratio(self) -> int: ...

    @abstractmethod
    def set_oversampling_ratio(self, oversampling_ratio: int) -> OperationResult[None, str]: ...

    @abstractmethod
    def get_allowed_oversampling_ratios(self) -> Tuple[int, ...]: ...

    @abstractmethod
    def get_configuration_hardware_id(self) -> str:
        """Hardware Advanced Config id of the ADC (locked while the OSR is changed)."""
