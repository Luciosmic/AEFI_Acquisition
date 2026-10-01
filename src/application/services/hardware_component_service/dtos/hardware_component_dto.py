from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class QuantitySpecDTO:
    """One quantity to characterize. `curve_x_label` set = the value is a
    curve: a tuple of (x, y) points."""

    key: str
    label: str
    unit: str
    curve_x_label: Optional[str]


@dataclass(frozen=True)
class HardwareComponentKindDTO:
    """A component kind and the quantities that characterize it — enough for
    the UI to build its tab without importing the domain."""

    key: str
    label: str
    quantities: Tuple[QuantitySpecDTO, ...]


@dataclass(frozen=True)
class HardwareComponentDTO:
    """Current characterization of one component (its latest entry).
    `values[key]` is a float, a tuple of (x, y) points, or None = not
    characterized; `uncharacterized` lists those keys."""

    kind_key: str
    component_name: str
    values: Dict[str, Any]
    uncharacterized: Tuple[str, ...]
    recorded_at: datetime
