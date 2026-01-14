"""
AefiDevice Aggregate

Responsibility:
- Aggregate Root representing the 4-source AEFI device.
- Owns the probe geometry and the list of source–sensor interaction pairs.

Rationale:
- Provide a single domain object that encapsulates how the physical
  device is arranged, without depending on hardware drivers.
- Higher-level services (e.g. physics engine, test bench) can query
  this aggregate for configuration and interactions.
"""

from dataclasses import dataclass, field
from typing import List, NewType

from .value_objects import QuadSourceGeometry, AefiInteractionPair


DeviceId = NewType("DeviceId", str)


@dataclass
class AefiDevice:
    """
    Aggregate Root for the AEFI device.

    Notes:
    - `geometry` describes the relative arrangement of the four sources
      around the sensor in the device-local frame.
    - `interactions` can be used to store precomputed source–sensor
      interaction vectors (e.g. for physics calculations).
    - This aggregate intentionally does not contain any hardware-specific
      details (ports, drivers, etc.).
    """

    id: DeviceId
    geometry: QuadSourceGeometry
    interactions: List[AefiInteractionPair] = field(default_factory=list)

    def set_interactions(self, interactions: List[AefiInteractionPair]) -> None:
        """
        Replace the current list of interactions with a new one.

        Domain services are expected to compute these interactions
        from geometry and calibration data.
        """
        self.interactions = list(interactions)


