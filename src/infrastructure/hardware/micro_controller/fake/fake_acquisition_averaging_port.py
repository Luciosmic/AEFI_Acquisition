"""
Fake Acquisition Averaging Port

See fake_acquisition_averaging_port_intention.md.
"""

from typing import List, Tuple

from application.services.acquisition_throughput_characterization_service.ports.i_acquisition_averaging_port import (
    IAcquisitionAveragingPort,
)
from domain.shared_kernel.operation_result import OperationResult


class FakeAcquisitionAveragingPort(IAcquisitionAveragingPort):
    """In-memory n_avg. Pass `get_n_avg` as ADS131A04Adapter's n_avg_reader
    so the simulated MCU averages what this port was set to."""

    N_AVG_MIN = 1
    N_AVG_MAX = 127  # same bounds as MCUAdvancedConfigurator

    def __init__(self, n_avg: int = 127, oversampling_ratio: int = 4096, fail_on_set: bool = False) -> None:
        self._n_avg = n_avg
        self._oversampling_ratio = oversampling_ratio
        self._fail_on_set = fail_on_set
        self.history: List[int] = []  # every n_avg set, in order

    def get_n_avg(self) -> int:
        return self._n_avg

    def set_n_avg(self, n_avg: int) -> OperationResult[None, str]:
        # Same failure modes as the real adapter: out of range, config not writable.
        if not self.N_AVG_MIN <= n_avg <= self.N_AVG_MAX:
            return OperationResult.fail(f"n_avg doit être entre {self.N_AVG_MIN} et {self.N_AVG_MAX} (reçu {n_avg})")
        if self._fail_on_set:
            return OperationResult.fail("configuration MCU non inscriptible (simulé)")
        self._n_avg = n_avg
        self.history.append(n_avg)
        return OperationResult.ok(None)

    def get_n_avg_range(self) -> Tuple[int, int]:
        return self.N_AVG_MIN, self.N_AVG_MAX

    def get_oversampling_ratio(self) -> int:
        return self._oversampling_ratio

    def get_configuration_hardware_ids(self) -> Tuple[str, ...]:
        return "mcu", "ads131a04"  # same ids as the real adapter
