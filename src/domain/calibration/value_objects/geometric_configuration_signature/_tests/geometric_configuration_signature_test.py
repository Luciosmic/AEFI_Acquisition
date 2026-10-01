import unittest

from domain.calibration.value_objects.geometric_configuration_signature.geometric_configuration_signature import (
    GeometricConfigurationSignature,
)

_DIAMETERS = (0.0196, 0.0196, 0.0195, 0.0195)
_DISTANCES = (0.11142, 0.10908, 0.08436, 0.08352, 0.08230, 0.08450)


class TestGeometricConfigurationSignature(unittest.TestCase):
    def test_creates_with_valid_tuples(self):
        signature = GeometricConfigurationSignature(
            sphere_diameters_m=_DIAMETERS, pairwise_distances_ext_m=_DISTANCES
        )
        self.assertEqual(signature.sphere_diameters_m, _DIAMETERS)
        self.assertEqual(signature.pairwise_distances_ext_m, _DISTANCES)

    def test_is_immutable(self):
        signature = GeometricConfigurationSignature(
            sphere_diameters_m=_DIAMETERS, pairwise_distances_ext_m=_DISTANCES
        )
        with self.assertRaises(Exception):
            signature.sphere_diameters_m = (0.0, 0.0, 0.0, 0.0)

    def test_equal_snapshots_compare_equal(self):
        signature_a = GeometricConfigurationSignature(
            sphere_diameters_m=_DIAMETERS, pairwise_distances_ext_m=_DISTANCES
        )
        signature_b = GeometricConfigurationSignature(
            sphere_diameters_m=_DIAMETERS, pairwise_distances_ext_m=_DISTANCES
        )
        self.assertEqual(signature_a, signature_b)

    def test_different_geometry_compares_unequal(self):
        signature_a = GeometricConfigurationSignature(
            sphere_diameters_m=_DIAMETERS, pairwise_distances_ext_m=_DISTANCES
        )
        signature_b = GeometricConfigurationSignature(
            sphere_diameters_m=(0.02, 0.02, 0.02, 0.02), pairwise_distances_ext_m=_DISTANCES
        )
        self.assertNotEqual(signature_a, signature_b)

    def test_rejects_wrong_diameter_count(self):
        with self.assertRaises(ValueError):
            GeometricConfigurationSignature(
                sphere_diameters_m=(0.02, 0.02, 0.02), pairwise_distances_ext_m=_DISTANCES
            )

    def test_rejects_wrong_distance_count(self):
        with self.assertRaises(ValueError):
            GeometricConfigurationSignature(
                sphere_diameters_m=_DIAMETERS, pairwise_distances_ext_m=(0.1, 0.1)
            )


if __name__ == "__main__":
    unittest.main()
