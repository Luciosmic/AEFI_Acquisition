import unittest

from domain.calibration.value_objects.hardware_signature.hardware_signature import HardwareSignature


class TestHardwareSignature(unittest.TestCase):
    def test_creates_with_all_fields(self):
        signature = HardwareSignature(
            excitation_board_version="v1.2",
            conditioning_board_version="v2.0",
            sensor_version="v3.1",
            sensor_serial_number="SN-001",
        )
        self.assertEqual(signature.excitation_board_version, "v1.2")
        self.assertEqual(signature.conditioning_board_version, "v2.0")
        self.assertEqual(signature.sensor_version, "v3.1")
        self.assertEqual(signature.sensor_serial_number, "SN-001")

    def test_sensor_serial_number_may_be_none(self):
        signature = HardwareSignature(
            excitation_board_version="v1.2",
            conditioning_board_version="v2.0",
            sensor_version="v3.1",
            sensor_serial_number=None,
        )
        self.assertIsNone(signature.sensor_serial_number)

    def test_is_immutable(self):
        signature = HardwareSignature(
            excitation_board_version="v1.2",
            conditioning_board_version="v2.0",
            sensor_version="v3.1",
            sensor_serial_number=None,
        )
        with self.assertRaises(Exception):
            signature.excitation_board_version = "v9.9"

    def test_rejects_empty_excitation_board_version(self):
        with self.assertRaises(ValueError):
            HardwareSignature(
                excitation_board_version="",
                conditioning_board_version="v2.0",
                sensor_version="v3.1",
                sensor_serial_number=None,
            )

    def test_rejects_empty_conditioning_board_version(self):
        with self.assertRaises(ValueError):
            HardwareSignature(
                excitation_board_version="v1.2",
                conditioning_board_version="",
                sensor_version="v3.1",
                sensor_serial_number=None,
            )

    def test_rejects_empty_sensor_version(self):
        with self.assertRaises(ValueError):
            HardwareSignature(
                excitation_board_version="v1.2",
                conditioning_board_version="v2.0",
                sensor_version="",
                sensor_serial_number=None,
            )

    def test_equal_signatures_compare_equal(self):
        signature_a = HardwareSignature(
            excitation_board_version="v1.2",
            conditioning_board_version="v2.0",
            sensor_version="v3.1",
            sensor_serial_number="SN-001",
        )
        signature_b = HardwareSignature(
            excitation_board_version="v1.2",
            conditioning_board_version="v2.0",
            sensor_version="v3.1",
            sensor_serial_number="SN-001",
        )
        self.assertEqual(signature_a, signature_b)


if __name__ == "__main__":
    unittest.main()
