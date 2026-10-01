import unittest

from domain.calibration.value_objects.rotation_convention.rotation_convention import RotationConvention


class TestRotationConvention(unittest.TestCase):
    def test_standard_is_extrinsic_zyx_sources_to_sensor(self):
        convention = RotationConvention.standard()
        self.assertEqual(
            (convention.type, convention.order, convention.direction),
            ("extrinsic", "ZYX", "sources_to_sensor"),
        )

    def test_explicit_standard_values_compare_equal_to_standard(self):
        self.assertEqual(RotationConvention("extrinsic", "ZYX", "sources_to_sensor"), RotationConvention.standard())

    def test_rejects_previous_xyz_convention(self):
        with self.assertRaises(ValueError):
            RotationConvention("extrinsic", "XYZ", "sources_to_sensor")

    def test_rejects_other_direction(self):
        with self.assertRaises(ValueError):
            RotationConvention("extrinsic", "ZYX", "sensor_to_sources")

    def test_rejects_intrinsic(self):
        with self.assertRaises(ValueError):
            RotationConvention("intrinsic", "ZYX", "sources_to_sensor")

    def test_is_immutable(self):
        with self.assertRaises(Exception):
            RotationConvention.standard().order = "XYZ"


if __name__ == "__main__":
    unittest.main()
