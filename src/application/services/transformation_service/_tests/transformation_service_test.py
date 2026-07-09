import unittest
from application.services.transformation_service.transformation_service import TransformationService
from tool.diagram_friendly_test import DiagramFriendlyTest


class TestTransformationService(DiagramFriendlyTest):

    def setUp(self):
        super().setUp()
        self.service = TransformationService()

    def test_identity_when_disabled(self):
        self.service.set_enabled(False)
        vector = (1.0, 0.0, 0.0)
        result = self.service.transform_sensor_to_source(vector)
        self.assertEqual(result, vector)

    def test_enabled_applies_rotation(self):
        self.service.set_rotation_angles(0.0, 0.0, 90.0)
        self.service.set_enabled(True)
        x, y, z = self.service.transform_sensor_to_source((1.0, 0.0, 0.0))
        self.assertAlmostEqual(x, 0.0, places=5)
        self.assertAlmostEqual(y, 1.0, places=5)
        self.assertAlmostEqual(z, 0.0, places=5)


if __name__ == "__main__":
    unittest.main()
