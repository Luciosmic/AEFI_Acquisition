"""
Electric Field Probe Aggregate

Responsibility:
- Represent the identity of a connected electric field probe (brand, model,
  serial number) and the axes it measures.
- Enforce that measurements match the probe's declared dimensionality.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

from domain.electric_field_probe.value_objects.field_measurement.field_measurement import (
    FieldMeasurement,
)


@dataclass(frozen=True)
class ElectricFieldProbe:
    """
    Identity of an electric field probe (mono/bi/tri-axial), speaking in V/m.
    """

    brand: str
    model: str
    serial_number: str
    axis_labels: Tuple[str, ...]
    battery_voltage_v: Optional[float] = None
    battery_percentage: Optional[float] = None
    battery_remaining_hours: Optional[float] = None

    def record_measurement(
        self,
        components: Tuple[float, ...],
        timestamp: datetime,
        uncertainty_estimate: Optional[float] = None,
    ) -> FieldMeasurement:
        """Build a FieldMeasurement, enforcing one component per declared axis."""
        if len(components) != len(self.axis_labels):
            raise ValueError(
                f"expected {len(self.axis_labels)} components for axes "
                f"{self.axis_labels}, got {len(components)}"
            )
        return FieldMeasurement(
            components=components,
            timestamp=timestamp,
            uncertainty_estimate=uncertainty_estimate,
        )
