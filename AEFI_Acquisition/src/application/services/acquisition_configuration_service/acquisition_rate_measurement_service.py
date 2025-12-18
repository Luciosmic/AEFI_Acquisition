"""
Acquisition Rate Measurement Service - Application Layer

Responsibility:
- Measure actual acquisition rate of hardware
- Produce AcquisitionRateCapability value object
- Cache measurements to avoid repeated benchmarks
"""

import time
import hashlib
import json
from typing import Optional
from datetime import datetime
from statistics import mean, stdev

from src.application.services.scan_application_service.ports.i_acquisition_port import IAcquisitionPort
from domain.models.scan.value_objects.acquisition_rate_capability import AcquisitionRateCapability


class AcquisitionRateMeasurementService:
    """Application service for measuring acquisition rate capabilities."""

    def __init__(self):
        self._cached_capability: Optional[AcquisitionRateCapability] = None

    def measure_acquisition_rate(
        self,
        acquisition_port: IAcquisitionPort,
        measurement_duration_s: float = 5.0,
        warmup_samples: int = 10
    ) -> AcquisitionRateCapability:
        """
        Measure actual acquisition rate by benchmarking the port.

        Args:
            acquisition_port: Port to measure
            measurement_duration_s: How long to measure
            warmup_samples: Samples to discard at start

        Returns:
            AcquisitionRateCapability with measured statistics
        """
        print(f"[AcquisitionRateMeasurement] Starting measurement (duration={measurement_duration_s}s)...")

        # Warm-up
        for _ in range(warmup_samples):
            acquisition_port.acquire_sample()

        # Measurement
        timestamps = []
        t_start = time.perf_counter()

        while (time.perf_counter() - t_start) < measurement_duration_s:
            acquisition_port.acquire_sample()
            timestamps.append(time.perf_counter())

        t_end = time.perf_counter()
        actual_duration = t_end - t_start
        sample_count = len(timestamps)

        if sample_count < 10:
            raise RuntimeError(f"Insufficient samples: {sample_count}")

        # Calculate intervals
        intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]

        # Statistics
        mean_interval = mean(intervals)
        std_interval = stdev(intervals) if len(intervals) > 1 else 0.0

        # Convert to rates
        measured_rate_hz = 1.0 / mean_interval if mean_interval > 0 else 0.0
        measured_std_dev_hz = (std_interval / (mean_interval ** 2)) if mean_interval > 0 else 0.0

        capability = AcquisitionRateCapability(
            measured_rate_hz=measured_rate_hz,
            measured_std_dev_hz=measured_std_dev_hz,
            measurement_timestamp=datetime.now(),
            measurement_duration_s=actual_duration,
            sample_count=sample_count,
            configuration_hash=self._get_configuration_hash()
        )

        print(f"[AcquisitionRateMeasurement] Complete: {capability}")
        self._cached_capability = capability
        return capability

    def get_cached_capability(self) -> Optional[AcquisitionRateCapability]:
        """Get cached capability if recent."""
        if self._cached_capability is None:
            return None
        if not self._cached_capability.is_measurement_recent(max_age_seconds=300):
            return None
        return self._cached_capability

    def measure_or_use_cached(
        self,
        acquisition_port: IAcquisitionPort,
        force_remeasure: bool = False
    ) -> AcquisitionRateCapability:
        """Get capability, measuring only if necessary."""
        if not force_remeasure:
            cached = self.get_cached_capability()
            if cached is not None:
                print(f"[AcquisitionRateMeasurement] Using cached: {cached}")
                return cached
        return self.measure_acquisition_rate(acquisition_port)

    def _get_configuration_hash(self) -> str:
        """Get hash of current hardware configuration."""
        config_repr = json.dumps({"timestamp": datetime.now().isoformat()}, sort_keys=True)
        return hashlib.md5(config_repr.encode()).hexdigest()[:8]
