"""FrequencyPointAcquired event (see frequency_point_acquired_intention.md)."""

from dataclasses import dataclass
from typing import Optional

from domain.frequency_sweep.value_objects.frequency_sweep_id.frequency_sweep_id import FrequencySweepId
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement

VOLT_UNIT_URI = "http://qudt.org/vocab/unit/V"
HERTZ_UNIT_URI = "http://qudt.org/vocab/unit/HZ"
MILLIMETRE_UNIT_URI = "http://qudt.org/vocab/unit/MilliM"


@dataclass(frozen=True)
class FrequencyPointAcquired(DomainEvent):
    frequency_sweep_id: FrequencySweepId
    role: str
    frequency_index: int
    frequency_hz: float
    measurement: AefiVoltageMeasurement
    samples_count: int
    table_height_mm: float
    measured_object_id: Optional[str] = None
    frequency_unit: str = HERTZ_UNIT_URI
    measurement_unit: str = VOLT_UNIT_URI
    table_height_unit: str = MILLIMETRE_UNIT_URI
