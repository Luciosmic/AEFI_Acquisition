"""
Test Bench Aggregate

Responsibility:
- Aggregate Root for the physical test bench used in electric field imaging experiments.
- Owns the arrangement of sources and sensor (columns, sources, sensor frame).
- Provides a high-level API to configure geometry and query source–sensor interactions.

Rationale:
- Centralise bench state in the Domain layer, independent of concrete hardware drivers.
- Offer a single entry point for application services that orchestrate scans on the bench.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from domain.value_objects.test_bench.column import Column
from domain.value_objects.test_bench.electric_field_sensor import CubicSensor3D
from domain.value_objects.test_bench.source_sensor_association import SourceSensorAssociation
from domain.value_objects.aefi_device.aefi_interaction_pair import AefiInteractionPair


@dataclass
class TestBench:
    """
    Aggregate Root representing the experimental test bench.

    Notes:
    - This aggregate captures the *logical* bench configuration (geometry,
      sensor/source associations), not the low-level hardware drivers.
    - Application services can use it to reason about which source interacts
      with the sensor at a given position.
    """

    columns: List[Column] = field(default_factory=list)
    sensor: Optional[CubicSensor3D] = None
    associations: List[SourceSensorAssociation] = field(default_factory=list)
    _interactions: List[AefiInteractionPair] = field(default_factory=list)

    def configure_geometry(
        self,
        columns: List[Column],
        sensor: CubicSensor3D,
        associations: List[SourceSensorAssociation],
    ) -> None:
        """
        Configure the bench geometry (columns, sensor, and source–sensor associations).

        This method is purely domain-level: it does not talk to hardware,
        only updates the aggregate state.
        """
        self.columns = columns
        self.sensor = sensor
        self.associations = associations
        # Interactions can be (re)computed from associations when needed.
        self._interactions = []

    def recompute_interactions(self) -> None:
        """
        Recompute the list of interaction pairs from the current associations.

        Placeholder:
        - In the future, this will derive `AefiInteractionPair` instances
          from the geometry (sources, sensor frame, etc.).
        """
        # TODO: Implement proper computation based on geometry and associations.
        self._interactions = []

    @property
    def interactions(self) -> List[AefiInteractionPair]:
        """
        Expose current interaction pairs as an immutable view (copy).
        """
        return list(self._interactions)


