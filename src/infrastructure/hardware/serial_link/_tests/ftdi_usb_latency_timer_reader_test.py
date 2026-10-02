import unittest

from infrastructure.hardware.serial_link.ftdi_usb_latency_timer_reader import FtdiUsbLatencyTimerReader

DEVICES = [
    ("VID_0403+PID_6001+AL03IC37A", "COM10", 16),
    ("VID_0403+PID_6015+FT421G4IA", "COM5", 1),
    ("VID_0403+PID_6001+BROKEN", None, None),
]


def reader(devices=DEVICES, platform="win32"):
    return FtdiUsbLatencyTimerReader(enumerate_devices=lambda: iter(devices), platform=platform)


class TestFtdiUsbLatencyTimerReader(unittest.TestCase):
    def test_reads_the_latency_of_the_device_on_that_port(self):
        self.assertEqual(reader().read_latency_timer_ms("COM10").value, 16.0)
        self.assertEqual(reader().read_latency_timer_ms("COM5").value, 1.0)

    def test_unknown_port_is_a_failure(self):
        result = reader().read_latency_timer_ms("COM99")
        self.assertTrue(result.is_failure)
        self.assertIn("COM99", result.error)

    def test_missing_latency_value_is_a_failure(self):
        self.assertTrue(reader([("dev", "COM10", None)]).read_latency_timer_ms("COM10").is_failure)

    def test_other_os_is_a_failure_without_touching_the_registry(self):
        def explode():
            raise AssertionError("registry must not be read")

        result = FtdiUsbLatencyTimerReader(enumerate_devices=explode, platform="linux").read_latency_timer_ms("COM10")
        self.assertTrue(result.is_failure)

    def test_unreadable_registry_is_a_failure_not_an_exception(self):
        def denied():
            raise PermissionError("access denied")

        result = FtdiUsbLatencyTimerReader(enumerate_devices=denied, platform="win32").read_latency_timer_ms("COM10")
        self.assertTrue(result.is_failure)
        self.assertIn("PermissionError", result.error)


if __name__ == "__main__":
    unittest.main()
