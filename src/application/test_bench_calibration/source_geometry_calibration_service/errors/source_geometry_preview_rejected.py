"""
Source Geometry Preview Rejected

Responsibility:
- The one failure outcome of `preview_source_frame` its caller must handle:
  the edited measurements describe no geometry the 4 spheres can take.

Rationale:
- The rule itself (overlap, triangle that cannot close) is the domain's
  (`SourceGeometryInconsistentError`). This type is the use-case outcome the
  application translates it into, so the presenter shows a reason instead of
  catching a domain exception.

Design:
- Frozen dataclass, `reason` is the domain error's message (names the
  offending reading, e.g. D_S1_S2).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceGeometryPreviewRejected:
    reason: str
