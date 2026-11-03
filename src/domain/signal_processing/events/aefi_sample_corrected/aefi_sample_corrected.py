"""AefiSampleCorrected event (see aefi_sample_corrected_intention.md)."""

from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement


@dataclass(frozen=True)
class AefiSampleCorrected(DomainEvent):
    """Emitted when a raw sample has been corrected (noise/phase/primary, per the
    enabled stages), after AefiCorrectedSample validated its calibration invariant.
    Still expressed in the sensor frame (not yet transformed to the source frame).
    """

    acquisition_id: UUID
    sample_index: int
    sample: AefiVoltageMeasurement
