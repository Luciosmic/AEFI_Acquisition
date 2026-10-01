import unittest

from domain.shared_kernel.excitation.value_objects.phase_angle import PhaseAngle


class TestPhaseAngle(unittest.TestCase):
    def test_normalizes_to_0_360(self):
        self.assertAlmostEqual(PhaseAngle(370.0).degrees, 10.0)
        self.assertAlmostEqual(PhaseAngle(-90.0).degrees, 270.0)

    def test_opposite_is_plus_180(self):
        self.assertAlmostEqual(PhaseAngle(0.0).opposite().degrees, 180.0)
        self.assertAlmostEqual(PhaseAngle(270.0).opposite().degrees, 90.0)

    def test_difference_from_shortest_path(self):
        self.assertAlmostEqual(PhaseAngle(180.0).difference_from(PhaseAngle(0.0)), 180.0)
        self.assertAlmostEqual(PhaseAngle(0.0).difference_from(PhaseAngle(90.0)), -90.0)
        self.assertAlmostEqual(PhaseAngle(10.0).difference_from(PhaseAngle(350.0)), 20.0)

    def test_register_roundtrip(self):
        self.assertAlmostEqual(PhaseAngle.from_register(32768).degrees, 180.0)
        self.assertAlmostEqual(PhaseAngle.from_register(16384).degrees, 90.0)
        self.assertEqual(PhaseAngle(180.0).to_register(), 32768)
        self.assertEqual(PhaseAngle(90.0).to_register(), 16384)


if __name__ == "__main__":
    unittest.main()
