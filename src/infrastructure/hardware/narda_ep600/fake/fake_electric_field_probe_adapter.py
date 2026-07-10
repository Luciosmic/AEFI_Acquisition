"""
Fake Electric Field Probe Adapter

Responsibility:
- In-memory double of IElectricFieldProbePort for tests and mock hardware mode.
"""

import random
from datetime import datetime
from typing import Optional

from application.services.electric_field_probe_service.ports.i_electric_field_probe_port import (
    IElectricFieldProbePort,
)
from domain.electric_field_probe.electric_field_probe import ElectricFieldProbe


class FakeElectricFieldProbeAdapter(IElectricFieldProbePort):
    def __init__(
        self, noise_std: float = 0.05, simulate_connection_failure: bool = False
    ) -> None:
        self._noise_std = noise_std
        self._simulate_connection_failure = simulate_connection_failure
        self._connected = False
        self._probe: Optional[ElectricFieldProbe] = None

    def connect(self) -> None:
        if self._simulate_connection_failure:
            raise TimeoutError("simulated probe timeout")
        self._probe = ElectricFieldProbe(
            brand="Fake",
            model="EP-000",
            serial_number="FAKE-0001",
            axis_labels=("X", "Y", "Z"),
        )
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False
        self._probe = None

    def is_connected(self) -> bool:
        return self._connected

    def get_probe(self) -> Optional[ElectricFieldProbe]:
        return self._probe

    def acquire_sample(self):
        if not self._connected or self._probe is None:
            raise RuntimeError("probe not connected")
        components = tuple(
            1.0 + random.gauss(0.0, self._noise_std) for _ in self._probe.axis_labels
        )
        return self._probe.record_measurement(components, timestamp=datetime.now())

    def is_ready(self) -> bool:
        return self._connected
