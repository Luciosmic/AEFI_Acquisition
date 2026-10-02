"""
Fake DRDY Capture Port

See fake_drdy_capture_port_intention.md.
"""

import random
from typing import Callable, Optional

from application.services.adc_output_rate_characterization_service.dtos.adc_output_rate_dtos import (
    DrdyCaptureDTO,
    DrdyCaptureRequestDTO,
)
from application.services.adc_output_rate_characterization_service.ports.i_drdy_capture_port import IDrdyCapturePort
from domain.shared_kernel.operation_result import OperationResult

# Bench values measured 2026-10-02: DRDY 1000,000 us at OSR 4096; interval std
# 0.229 us with a 0.5 us sample interval (50 ms window, 100 000 points). The
# timing noise comes from the scope's sampling, so it scales with the window.
MODULATOR_FREQUENCY_HZ = 4.096e6
CAPTURE_POINTS = 100_000
INTERVAL_STD_PER_SAMPLE_INTERVAL = 0.229 / 0.5
EDGE_JITTER_PER_SAMPLE_INTERVAL = INTERVAL_STD_PER_SAMPLE_INTERVAL / 2 ** 0.5


class FakeDrdyCapturePort(IDrdyCapturePort):
    """DRDY edges at f_MOD / OSR, the OSR read from `oversampling_provider`
    (e.g. FakeAdcOversamplingPort.get_oversampling_ratio).

    `applied_oversampling_ratio`: simulate an ADC that ignores the OSR register
    (edges stay at that OSR); `fail_reason`: simulate no instrument."""

    INSTRUMENT = "FAKE,DSO-X 2014A (simulated),0,0"

    def __init__(
        self,
        oversampling_provider: Callable[[], int],
        modulator_frequency_hz: float = MODULATOR_FREQUENCY_HZ,
        applied_oversampling_ratio: Optional[int] = None,
        fail_reason: Optional[str] = None,
        rng: Optional[random.Random] = None,
    ) -> None:
        self._oversampling_provider = oversampling_provider
        self._f_mod = modulator_frequency_hz
        self._applied = applied_oversampling_ratio
        self._fail_reason = fail_reason
        self._rng = rng or random.Random(0)
        self.requests = []

    def capture_falling_edges(self, request: DrdyCaptureRequestDTO) -> OperationResult[DrdyCaptureDTO, str]:
        self.requests.append(request)
        if self._fail_reason:
            return OperationResult.fail(self._fail_reason)
        osr = self._applied or self._oversampling_provider()
        period = osr / self._f_mod
        count = max(2, int(request.window_s / period) + 1)
        sample_interval = request.window_s / CAPTURE_POINTS
        jitter = EDGE_JITTER_PER_SAMPLE_INTERVAL * sample_interval
        edges = tuple(k * period + self._rng.gauss(0.0, jitter) for k in range(count))
        return OperationResult.ok(DrdyCaptureDTO(falling_edge_times_s=edges, sample_interval_s=sample_interval,
                                                 instrument=self.INSTRUMENT))
