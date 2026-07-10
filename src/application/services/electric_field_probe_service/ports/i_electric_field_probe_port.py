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
