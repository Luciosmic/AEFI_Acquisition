"""SpectralAnalysisResultUpdated event (see spectral_analysis_result_updated_intention.md)."""

from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.signal_processing.value_objects.spectral_analysis_result.spectral_analysis_result import (
    SpectralAnalysisResult,
)


@dataclass(frozen=True)
class SpectralAnalysisResultUpdated(DomainEvent):
    """Emitted when a new spectral analysis result has been computed for the
    current window of an acquisition."""

    acquisition_id: UUID
    result: SpectralAnalysisResult
