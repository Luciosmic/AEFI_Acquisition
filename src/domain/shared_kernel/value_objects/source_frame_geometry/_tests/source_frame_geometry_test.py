"""Smoke test for SourceFrameGeometry value object (pure data holder)."""
import pytest

from domain.shared_kernel.value_objects.source_frame_geometry.source_frame_geometry import (
    SourceFrameGeometry,
)


def test_immutable():
    result = SourceFrameGeometry(
        positions=((0, 0, 0), (0.1, 0, 0), (0.03, 0.06, 0), (0.03, 0.02, 0)),
        centroid=(0.0325, 0.02, 0.0),
        x_axis=(1, 0, 0), y_axis=(0, 1, 0), z_axis=(0, 0, 1),
        rotation_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
        is_orthogonal=True,
    )

    with pytest.raises(AttributeError):
        result.is_orthogonal = False
