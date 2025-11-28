from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import uuid

@dataclass(frozen=True)
class ObjectId:
    """Unique identifier for an Experiment Object."""
    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __str__(self):
        return self.value

@dataclass
class ExperimentObject:
    """Represents the physical object being studied.
    
    This entity is linked to the external Object Management Context.
    The Acquisition App treats it mostly as read-only metadata.
    """
    id: ObjectId
    name: str
    description: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    
    # Physical dimensions (optional, but useful for scan planning)
    width_mm: Optional[float] = None
    length_mm: Optional[float] = None
    depth_mm: Optional[float] = None # Depth if buried

    def update_properties(self, new_properties: Dict[str, Any]) -> None:
        """Update object properties (if allowed in this context)."""
        self.properties.update(new_properties)
