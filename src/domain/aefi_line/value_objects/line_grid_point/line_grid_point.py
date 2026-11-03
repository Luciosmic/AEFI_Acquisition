"""LineGridPoint value object (see line_grid_point_intention.md)."""

from dataclasses import dataclass

from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D


@dataclass(frozen=True)
class LineGridPoint:
    index_in_line: int
    position: Position2D
    measurement: AefiVoltageMeasurement

    def __post_init__(self):
        if self.index_in_line < 0:
            raise ValueError("index_in_line must be >= 0")
