"""
Source Geometry Inconsistent Error

Responsibility:
- Name the refused promise "these caliper measurements describe a physically
  possible 4-sphere source geometry".

Rationale:
- Raised both by `SourceGeometryCalibrationEntry` (overlapping spheres) and by
  `SourceFrameSolver` (distances that no planar placement satisfies). One
  name for one business condition, so the application layer translates a
  single domain error into a visible use-case outcome instead of catching a
  generic `ValueError`.

Design:
- Subclass of `ValueError`: callers that predate this type keep working.
"""


class SourceGeometryInconsistentError(ValueError):
    """The measured diameters/distances describe no physically possible geometry."""
