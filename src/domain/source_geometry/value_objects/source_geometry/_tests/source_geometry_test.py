"""Tests for SourceGeometry value object."""
import pytest

from domain.source_geometry.value_objects.source_geometry.source_geometry import SourceGeometry


def make_geometry(**overrides):
    defaults = dict(d_12=0.1, d_13=0.07, d_14=0.07, d_23=0.07, d_24=0.07, d_34=0.1)
    defaults.update(overrides)
    return SourceGeometry(**defaults)


def test_valid_geometry_constructs():
    geometry = make_geometry()
    assert geometry.d_12 == 0.1
    assert geometry.d_34 == 0.1


def test_immutable():
    geometry = make_geometry()
    with pytest.raises(AttributeError):
        geometry.d_12 = 0.2


@pytest.mark.parametrize("field", ["d_12", "d_13", "d_14", "d_23", "d_24", "d_34"])
def test_rejects_non_positive_distance(field):
    with pytest.raises(ValueError, match="must be positive"):
        make_geometry(**{field: 0.0})


@pytest.mark.parametrize("field", ["d_12", "d_13", "d_14", "d_23", "d_24", "d_34"])
def test_rejects_negative_distance(field):
    with pytest.raises(ValueError, match="must be positive"):
        make_geometry(**{field: -0.05})


def test_rejects_non_finite_distance():
    with pytest.raises(ValueError, match="must be finite"):
        make_geometry(d_12=float("nan"))
