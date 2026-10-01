import unittest

from domain.calibration.value_objects.hardware_signature.hardware_signature import HardwareSignature


class TestHardwareSignature(unittest.TestCase):
    def test_creates_with_all_fields(self):
        signature = HardwareSignature(
            excitation_electronics_board_name="v1.2",
            conditioning_electronics_board_name="v2.0",
            sensor_name="v3.1_SN-001",
        )
        self.assertEqual(signature.excitation_electronics_board_name, "v1.2")
        self.assertEqual(signature.conditioning_electronics_board_name, "v2.0")
        self.assertEqual(signature.sensor_name, "v3.1_SN-001")

    def test_is_immutable(self):
        signature = HardwareSignature(
            excitation_electronics_board_name="v1.2",
            conditioning_electronics_board_name="v2.0",
            sensor_name="v3.1",
        )
        with self.assertRaises(Exception):
            signature.excitation_electronics_board_name = "v9.9"

    def test_rejects_empty_excitation_board_name(self):
        with self.assertRaises(ValueError):
            HardwareSignature(
                excitation_electronics_board_name="",
                conditioning_electronics_board_name="v2.0",
                sensor_name="v3.1",
            )

    def test_rejects_empty_conditioning_board_name(self):
        with self.assertRaises(ValueError):
            HardwareSignature(
                excitation_electronics_board_name="v1.2",
                conditioning_electronics_board_name="",
                sensor_name="v3.1",
            )

    def test_rejects_empty_sensor_name(self):
        with self.assertRaises(ValueError):
            HardwareSignature(
                excitation_electronics_board_name="v1.2",
                conditioning_electronics_board_name="v2.0",
                sensor_name="",
            )

    def test_equal_signatures_compare_equal(self):
        signature_a = HardwareSignature(
            excitation_electronics_board_name="v1.2",
            conditioning_electronics_board_name="v2.0",
            sensor_name="v3.1_SN-001",
        )
        signature_b = HardwareSignature(
            excitation_electronics_board_name="v1.2",
            conditioning_electronics_board_name="v2.0",
            sensor_name="v3.1_SN-001",
        )
        self.assertEqual(signature_a, signature_b)


if __name__ == "__main__":
    unittest.main()
