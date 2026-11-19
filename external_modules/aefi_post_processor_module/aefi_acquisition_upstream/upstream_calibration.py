"""
upstream_calibration - The calibration concept borrowed from the acquisition application, without Qt.
See upstream_objects_intention.md.

Kept apart from `upstream_objects`: that module pulls Qt widgets, and the readers of the parameters file must load
without Qt.
"""

from . import settle_sys_path

settle_sys_path()

from domain.test_bench_calibration.value_objects.rotation_convention.rotation_convention import RotationConvention  # noqa: E402

__all__ = ["RotationConvention"]
