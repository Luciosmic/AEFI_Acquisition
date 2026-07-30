"""
Electric Field Probe Port Interface

Responsibility:
- Define abstract interface for connecting to and acquiring from an electric
  field probe (mono/bi/tri-axial), independent of brand.

Rationale:
- Application service depends on this abstraction, not a specific driver
  (e.g. NardaEP601). A different probe brand could implement this same port.

Design:
- Abstract Base Class (ABC), pure interface.
- connect()/disconnect() are separate from acquire_sample(): the probe may
  be present but not yet connected (manual, on-demand connection).
"""

from abc import ABC, abstractmethod
from typing import Optional

from domain.electric_field_probe.electric_field_probe import ElectricFieldProbe
from domain.electric_field_probe.value_objects.field_measurement.field_measurement import (
    FieldMeasurement,
)
from application.services.electric_field_probe_service.dtos.electric_field_probe_dtos import (
    FrequencyCorrectionResult,
)


class IElectricFieldProbePort(ABC):
    """Port interface for an electric field probe (connection + acquisition)."""

    @abstractmethod
    def connect(self) -> None:
        """
        Open the connection to the probe and resolve its identity.

        Raises whatever the underlying driver raises (e.g. timeout, port not
        found) — the caller (application service) is responsible for turning
        that into a domain event instead of propagating it further.
        """

    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection to the probe."""

    @abstractmethod
    def is_connected(self) -> bool:
        """True if the probe is currently connected."""

    @abstractmethod
    def get_probe(self) -> Optional[ElectricFieldProbe]:
        """Identity of the connected probe, or None if not connected."""

    @abstractmethod
    def acquire_sample(self) -> FieldMeasurement:
        """Acquire a single field measurement sample."""

    @abstractmethod
    def is_ready(self) -> bool:
        """True if the probe is connected and ready to acquire."""

    @abstractmethod
    def refresh_battery(self) -> None:
        """
        Re-query the battery level from hardware and update the held probe's
        battery fields (battery_voltage_v/battery_percentage/battery_remaining_hours).

        No-op if not connected. Caller (application service) is responsible
        for not invoking this while an acquisition is running — the query
        shares the same physical link as sample acquisition and could
        perturb it.
        """

    @abstractmethod
    def apply_frequency_correction(self, frequency_hz: float) -> FrequencyCorrectionResult:
        """
        Apply the probe's frequency-dependent factory calibration correction
        for frequency_hz.

        No concurrent call while an acquisition is running — the correction
        shares the same physical link as sample acquisition (route through
        the executor's request_frequency_correction instead). Never raises
        for a hardware failure: captured and returned as
        FrequencyCorrectionResult.error.
        """
