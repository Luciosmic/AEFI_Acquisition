import struct
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from infrastructure.hardware.narda_ep600.driver_narda_ep601 import NardaEP601, NardaProbeTimeout


class TestNardaEP601(unittest.TestCase):
    def setUp(self):
        patcher = patch("infrastructure.hardware.narda_ep600.driver_narda_ep601.serial.Serial")
        self.mock_serial_cls = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_serial = MagicMock()
        self.mock_serial.is_open = True
        self.mock_serial_cls.return_value = self.mock_serial

        self.probe = NardaEP601("COM8")
        self.probe.connect()

    def test_connect_opens_serial_with_configured_params(self):
        self.mock_serial_cls.assert_called_once_with("COM8", 9600, timeout=1.0)

    def test_disconnect_closes_serial(self):
        self.probe.disconnect()
        self.mock_serial.close.assert_called_once()
        self.assertIsNone(self.probe._serial)

    def test_context_manager_connects_and_disconnects(self):
        with NardaEP601("COM8") as probe:
            self.assertIsNotNone(probe._serial)
        self.mock_serial.close.assert_called()

    def test_query_raises_timeout_on_empty_response(self):
        self.mock_serial.read.return_value = b""
        with self.assertRaises(NardaProbeTimeout):
            self.probe.get_version()

    def test_get_version_strips_padding(self):
        self.mock_serial.read.return_value = b"vEP600:1.32 07/20;\x00\x00\x00"
        self.assertEqual(self.probe.get_version(), "vEP600:1.32 07/20;")

    def test_get_battery_voltage_conversion(self):
        nn = 700
        self.mock_serial.read.return_value = b"b" + struct.pack(">H", nn)
        expected = 3 * (nn / 1024 * 1.6)
        self.assertAlmostEqual(self.probe.get_battery_voltage(), expected)

    def test_get_total_field_takes_square_root_of_reported_value(self):
        squared = 25.0
        self.mock_serial.read.return_value = b"T" + struct.pack("<f", squared)
        self.assertAlmostEqual(self.probe.get_total_field(), 5.0, places=4)

    def test_get_field_components_unpacks_three_axes(self):
        self.mock_serial.read.return_value = b"A" + struct.pack("<3f", 1.0, 2.0, 3.0)
        x, y, z = self.probe.get_field_components()
        self.assertAlmostEqual(x, 1.0, places=5)
        self.assertAlmostEqual(y, 2.0, places=5)
        self.assertAlmostEqual(z, 3.0, places=5)

    def test_get_total_field_averaged_computes_arithmetic_mean(self):
        squares = [4.0, 9.0, 16.0]
        self.mock_serial.read.side_effect = [b"T" + struct.pack("<f", s) for s in squares]
        avg = self.probe.get_total_field_averaged(n=len(squares))
        expected = sum(s**0.5 for s in squares) / len(squares)
        self.assertAlmostEqual(avg, expected)

    def test_get_field_components_averaged_computes_per_axis_mean(self):
        readings = [(1.0, 2.0, 3.0), (3.0, 4.0, 5.0)]
        self.mock_serial.read.side_effect = [
            b"A" + struct.pack("<3f", *r) for r in readings
        ]
        avg_x, avg_y, avg_z = self.probe.get_field_components_averaged(n=len(readings))
        self.assertAlmostEqual(avg_x, 2.0, places=4)
        self.assertAlmostEqual(avg_y, 3.0, places=4)
        self.assertAlmostEqual(avg_z, 4.0, places=4)


if __name__ == "__main__":
    unittest.main()
