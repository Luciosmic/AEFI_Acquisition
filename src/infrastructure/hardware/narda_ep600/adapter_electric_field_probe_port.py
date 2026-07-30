"""
Narda EP-601 Electric Field Probe Adapter

Responsibility:
- Implement IElectricFieldProbePort by wrapping the NardaEP601 serial driver.
- The only Narda-brand-specific piece of the electric_field_probe chain.
"""

import dataclasses
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
    NardaEP601,
    RF_SENSING_RANGE_HZ,
    estimate_battery_percentage,
    estimate_battery_remaining_hours,
)

AXIS_LABELS = ("X", "Y", "Z")


class NardaEP601ProbeAdapter(IElectricFieldProbePort):
    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 1.0) -> None:
        self._driver = NardaEP601(port=port, baudrate=baudrate, timeout=timeout)
        self._probe: Optional[ElectricFieldProbe] = None

    def connect(self) -> None:
        self._driver.connect()
        try:
            serial_number = self._driver.get_serial_number()
            battery_voltage = self._driver.get_battery_voltage()
        except Exception:
            self._driver.disconnect()
            raise
        self._probe = ElectricFieldProbe(
            brand="Narda",
            model="EP-601",
            serial_number=serial_number,
            axis_labels=AXIS_LABELS,
            battery_voltage_v=battery_voltage,
            battery_percentage=estimate_battery_percentage(battery_voltage),
            battery_remaining_hours=estimate_battery_remaining_hours(battery_voltage),
        )

    def disconnect(self) -> None:
        self._driver.disconnect()
        self._probe = None

    def is_connected(self) -> bool:
        return self._probe is not None

    def get_probe(self) -> Optional[ElectricFieldProbe]:
        return self._probe

    def acquire_sample(self):
        if self._probe is None:
            raise RuntimeError("probe not connected")
        components = self._driver.get_field_components()
        return self._probe.record_measurement(components, timestamp=datetime.now())

    def is_ready(self) -> bool:
        return self._probe is not None

    def refresh_battery(self) -> None:
        if self._probe is None:
            return
        battery_voltage = self._driver.get_battery_voltage()
        self._probe = dataclasses.replace(
            self._probe,
            battery_voltage_v=battery_voltage,
            battery_percentage=estimate_battery_percentage(battery_voltage),
            battery_remaining_hours=estimate_battery_remaining_hours(battery_voltage),
        )

    def apply_frequency_correction(self, frequency_hz: float) -> FrequencyCorrectionResult:
        if frequency_hz < RF_SENSING_RANGE_HZ[0]:
            # Limite physique permanente de la sonde (diode/antenne non qualifiee sous
            # 10kHz), pas une panne — aucun round-trip serie, pas de clamp.
            return FrequencyCorrectionResult(
                requested_hz=frequency_hz, applied_hz=None, in_range=False
            )
        try:
            applied_hz = self._driver.set_frequency_correction(frequency_hz)
        except (ValueError, IOError) as e:
            return FrequencyCorrectionResult(
                requested_hz=frequency_hz, applied_hz=None, in_range=True, error=str(e)
            )
        return FrequencyCorrectionResult(
            requested_hz=frequency_hz, applied_hz=applied_hz, in_range=True
        )
