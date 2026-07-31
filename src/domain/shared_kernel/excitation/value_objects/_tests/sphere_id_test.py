import unittest

from domain.shared_kernel.excitation.value_objects.sphere_id import SphereId


class TestSphereId(unittest.TestCase):
    def test_quadrants_match_motion_control_convention(self):
        self.assertEqual((SphereId.S1.x_sign, SphereId.S1.y_sign), ("neg", "pos"))
        self.assertEqual((SphereId.S3.x_sign, SphereId.S3.y_sign), ("pos", "pos"))
        self.assertEqual((SphereId.S4.x_sign, SphereId.S4.y_sign), ("neg", "neg"))
        self.assertEqual((SphereId.S2.x_sign, SphereId.S2.y_sign), ("pos", "neg"))

    def test_electronic_pair_s1_s2(self):
        self.assertEqual(SphereId.S1.electronic_pair, SphereId.S2)
        self.assertEqual(SphereId.S2.electronic_pair, SphereId.S1)

    def test_electronic_pair_s3_s4(self):
        self.assertEqual(SphereId.S3.electronic_pair, SphereId.S4)
        self.assertEqual(SphereId.S4.electronic_pair, SphereId.S3)

    def test_dds_channel_confirmed_on_oscilloscope(self):
        # Counter-intuitive: channel 1 (DDS1) drives S3/S4, channel 2 (DDS2) drives S1/S2.
        self.assertEqual(SphereId.S1.dds_channel, 2)
        self.assertEqual(SphereId.S2.dds_channel, 2)
        self.assertEqual(SphereId.S3.dds_channel, 1)
        self.assertEqual(SphereId.S4.dds_channel, 1)

    def test_is_direct_output(self):
        self.assertFalse(SphereId.S1.is_direct_output)
        self.assertTrue(SphereId.S2.is_direct_output)
        self.assertFalse(SphereId.S3.is_direct_output)
        self.assertTrue(SphereId.S4.is_direct_output)


if __name__ == "__main__":
    unittest.main()
