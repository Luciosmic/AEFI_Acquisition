"""
Fake Software Provenance Port

See fake_software_provenance_port_intention.md.
"""

from application.shared.acquisition_parameters.acquisition_conditions_dtos import (
    SoftwareProvenanceDTO,
)
from application.shared.acquisition_parameters.i_software_provenance_port import (
    ISoftwareProvenancePort,
)

CLEAN = SoftwareProvenanceDTO(
    name="AEFI Acquisition", version="0.1.0", commit="0123456789abcdef0123456789abcdef01234567",
    branch="develop", dirty=False,
)
GIT_UNAVAILABLE = SoftwareProvenanceDTO(name="AEFI Acquisition", unknown_reason="git rev-parse HEAD : FileNotFoundError")


class FakeSoftwareProvenancePort(ISoftwareProvenancePort):
    """Returns the given provenance (default: a clean tree). Use
    GIT_UNAVAILABLE to reproduce the real reader's failure mode."""

    def __init__(self, provenance: SoftwareProvenanceDTO = CLEAN) -> None:
        self._provenance = provenance
        self.reads = 0

    def read(self) -> SoftwareProvenanceDTO:
        self.reads += 1
        return self._provenance
