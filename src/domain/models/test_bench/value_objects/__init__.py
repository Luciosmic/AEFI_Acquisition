"""
Value Objects specific to the TestBench bounded context.

This module re-exports the existing implementations from
`domain.value_objects.test_bench` to provide a model-level
import path:

    from domain.model.test_bench.value_objects import Column, SphericalSource, ...
"""

from domain.models.test_bench.value_objects.column import Column, Dimensions2D, ColumnId
from domain.models.test_bench.value_objects.electric_field_source import (
    SphericalSource,
    SourceId,
    Quadrant,
)
from domain.models.test_bench.value_objects.electric_field_sensor import (
    CubicSensor3D,
    Dimensions3D,
    SensorId,
)
from domain.models.test_bench.value_objects.source_sensor_association import (
    SourceSensorAssociation,
)
from domain.models.test_bench.value_objects.sensor_frame import SensorFrame

__all__ = [
    "Column",
    "Dimensions2D",
    "ColumnId",
    "SphericalSource",
    "SourceId",
    "Quadrant",
    "CubicSensor3D",
    "Dimensions3D",
    "SensorId",
    "SourceSensorAssociation",
    "SensorFrame",
]



