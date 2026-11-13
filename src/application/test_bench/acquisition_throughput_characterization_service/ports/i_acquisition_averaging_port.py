from abc import ABC, abstractmethod
from typing import Tuple

from domain.shared_kernel.operation_result import OperationResult


class IAcquisitionAveragingPort(ABC):
    """
    Responsibility:
    - Read and set the MCU averaging n_avg (conversions averaged per returned
      sample), and read the ADC oversampling ratio it is measured under.

    Rationale:
    - The throughput characterization sweeps n_avg; without this port the
      service would write mcu_last_config.json itself (infrastructure detail).

    Design:
    - set_n_avg() takes effect on the next sample the acquisition starts
      (the ADC adapter re-reads n_avg before each sample).
    - set_n_avg() returns a failure (not raises) if the value cannot be
      applied (out of range, config not writable).
    """

    @abstractmethod
    def get_n_avg(self) -> int: ...

    @abstractmethod
    def set_n_avg(self, n_avg: int) -> OperationResult[None, str]: ...

    @abstractmethod
    def get_n_avg_range(self) -> Tuple[int, int]:
        """(min, max) accepted by the MCU."""

    @abstractmethod
    def get_oversampling_ratio(self) -> int: ...

    @abstractmethod
    def get_configuration_hardware_ids(self) -> Tuple[str, ...]:
        """Hardware Advanced Config ids of the settings this port reads or
        writes (n_avg, OSR): locked while a characterization runs."""
