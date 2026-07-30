"""Tests for SourceGeometry value object."""
import pytest

from domain.shared_kernel.value_objects.source_geometry.source_geometry import SourceGeometry

RAW_FIELDS = ("D_12", "D_13", "D_14", "D_23", "D_24", "D_34", "phi_1", "phi_2", "phi_3", "phi_4")


def make_geometry(**overrides):
    # ideal symmetric cross, uniform diameter, chosen so all d_ij are comfortably positive
    r = 0.01
    defaults = dict(
        D_12=0.1 + 2 * r, D_34=0.1 + 2 * r,
        D_13=0.1 / 1.41421356 + 2 * r, D_14=0.1 / 1.41421356 + 2 * r,
        D_23=0.1 / 1.41421356 + 2 * r, D_24=0.1 / 1.41421356 + 2 * r,
        phi_1=2 * r, phi_2=2 * r, phi_3=2 * r, phi_4=2 * r,
    )
    defaults.update(overrides)
    return SourceGeometry(**defaults)


def test_valid_geometry_constructs():
    geometry = make_geometry()
    assert geometry.D_12 == pytest.approx(0.12)
    assert geometry.phi_1 == 0.02


def test_derives_radius_from_diameter():
    geometry = make_geometry(phi_1=0.0196, phi_2=0.0196, phi_3=0.0195, phi_4=0.0195)
    assert geometry.r_1 == pytest.approx(0.0098)
    assert geometry.r_3 == pytest.approx(0.00975)


def test_derives_center_to_center_from_extremity_to_extremity():
    # real device measurement, 2026-07-24
    geometry = SourceGeometry(
        D_12=0.11142, D_13=0.08436, D_14=0.08352, D_23=0.08230, D_24=0.08450, D_34=0.10908,
        phi_1=0.0196, phi_2=0.0196, phi_3=0.0195, phi_4=0.0195,
    )
    assert geometry.d_12 == pytest.approx(0.09182)
    assert geometry.d_34 == pytest.approx(0.08958)


def test_immutable():
    geometry = make_geometry()
    with pytest.raises(AttributeError):
        geometry.D_12 = 0.2


@pytest.mark.parametrize("field", RAW_FIELDS)
def test_rejects_non_positive_raw_value(field):
    with pytest.raises(ValueError, match="must be positive"):
        make_geometry(**{field: 0.0})


@pytest.mark.parametrize("field", RAW_FIELDS)
def test_rejects_negative_raw_value(field):
    with pytest.raises(ValueError, match="must be positive"):
        make_geometry(**{field: -0.05})


def test_rejects_non_finite_raw_value():
    with pytest.raises(ValueError, match="must be finite"):
        make_geometry(D_12=float("nan"))


def test_rejects_overlapping_spheres():
    # D_12 smaller than r_1 + r_2 => negative center-to-center distance
    with pytest.raises(ValueError, match="Derived center-to-center d_12 is not positive"):
        make_geometry(D_12=0.01, phi_1=0.02, phi_2=0.02)
