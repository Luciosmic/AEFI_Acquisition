"""
Fake Electric Field Probe Adapter

Responsibility:
- In-memory double of IElectricFieldProbePort for tests and mock hardware mode.
"""

import dataclasses
import random
from datetime import datetime
from typing import Optional

from application.services.electric_field_probe_service.ports.i_electric_field_probe_port import (
    IElectricFieldProbePort,
)
from application.services.electric_field_probe_service.dtos.electric_field_probe_dtos import (
    FrequencyCorrectionResult,
)
from domain.electric_field_probe.electric_field_probe import ElectricFieldProbe
from infrastructure.hardware.narda_ep600.driver_narda_ep601 import (
    RF_SENSING_RANGE_HZ,
    estimate_battery_percentage,
    estimate_battery_remaining_hours,
)

_FAKE_BATTERY_VOLTAGE_V = 2.7  # ~valeur mi-decharge plausible pour la pile Panasonic ML621S 3V


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
            battery_voltage_v=_FAKE_BATTERY_VOLTAGE_V,
            battery_percentage=estimate_battery_percentage(_FAKE_BATTERY_VOLTAGE_V),
            battery_remaining_hours=estimate_battery_remaining_hours(_FAKE_BATTERY_VOLTAGE_V),
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

    def refresh_battery(self) -> None:
        if self._probe is None:
            return
        # ponytail: valeur fixe rejouee telle quelle (pas de simulation de decharge) — suffisant
        # pour exercer le cablage refresh sans hardware ; a enrichir si un test veut voir varier
        # la valeur affichee.
        self._probe = dataclasses.replace(
            self._probe,
            battery_voltage_v=_FAKE_BATTERY_VOLTAGE_V,
            battery_percentage=estimate_battery_percentage(_FAKE_BATTERY_VOLTAGE_V),
            battery_remaining_hours=estimate_battery_remaining_hours(_FAKE_BATTERY_VOLTAGE_V),
        )

    def apply_frequency_correction(self, frequency_hz: float) -> FrequencyCorrectionResult:
        if frequency_hz < RF_SENSING_RANGE_HZ[0]:
            return FrequencyCorrectionResult(
                requested_hz=frequency_hz, applied_hz=None, in_range=False
            )
        # Quantification 10kHz, comme la resolution reelle du driver (#00k, cf.
        # driver_narda_ep601.set_frequency_correction).
        applied_hz = round(frequency_hz / 10_000) * 10_000
        return FrequencyCorrectionResult(
            requested_hz=frequency_hz, applied_hz=applied_hz, in_range=True
        )
