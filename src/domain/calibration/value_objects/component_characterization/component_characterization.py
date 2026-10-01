"""
Component Characterization Value Object

Responsibility:
- Hold the values of every essential quantity of one hardware component
  kind, each one either measured or explicitly not characterized (None).
"""

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Tuple, Union

from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)

CurvePoints = Tuple[Tuple[float, float], ...]
QuantityValue = Optional[Union[float, CurvePoints]]


@dataclass(frozen=True)
class ComponentCharacterization:
    """
    `values` has exactly one entry per quantity of `kind`. A scalar is a
    float > 0, a curve a non-empty tuple of (x, y) points with x, y > 0;
    `None` means "not characterized yet" — an explicit, recorded debt.
    """

    kind: HardwareComponentKind
    values: Dict[str, QuantityValue]

    def __post_init__(self):
        expected = {q.key for q in self.kind.quantities}
        if set(self.values) != expected:
            raise ValueError(f"{self.kind.value}: expected quantities {sorted(expected)}, got {sorted(self.values)}")
        for spec in self.kind.quantities:
            value = self.values[spec.key]
            if value is None:
                continue
            if spec.is_curve:
                if not value or any(len(p) != 2 or p[0] <= 0 or p[1] <= 0 for p in value):
                    raise ValueError(f"{spec.key} must be non-empty (x, y) points with x, y > 0, got {value}")
            elif value <= 0:
                raise ValueError(f"{spec.key} must be > 0, got {value}")

    @staticmethod
    def of(kind: HardwareComponentKind, values: Mapping[str, QuantityValue]) -> "ComponentCharacterization":
        """Build from possibly partial `values`: a quantity left out is not
        characterized. Curves are normalized to tuples of (x, y) tuples."""
        normalized: Dict[str, QuantityValue] = {}
        for spec in kind.quantities:
            value = values.get(spec.key)
            if spec.is_curve and value is not None:
                value = tuple((float(x), float(y)) for x, y in value)
            normalized[spec.key] = value
        unknown = set(values) - set(normalized)
        if unknown:
            raise ValueError(f"{kind.value}: unknown quantities {sorted(unknown)}")
        return ComponentCharacterization(kind=kind, values=normalized)

    def uncharacterized(self) -> List[str]:
        """Keys of the quantities still not characterized, in declaration order."""
        return [q.key for q in self.kind.quantities if self.values[q.key] is None]
