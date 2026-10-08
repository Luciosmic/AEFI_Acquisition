import unittest

from infrastructure.hardware.serial_link.fake.fake_usb_latency_timer_port import FakeUsbLatencyTimerPort


class TestFakeUsbLatencyTimerPort(unittest.TestCase):
    def test_returns_the_latency_of_its_port(self):
        self.assertEqual(FakeUsbLatencyTimerPort(latency_ms=1.0).read_latency_timer_ms("COM10").value, 1.0)

    def test_other_port_fails_like_the_real_reader(self):
        self.assertTrue(FakeUsbLatencyTimerPort().read_latency_timer_ms("COM3").is_failure)

    def test_imposed_failure(self):
        port = FakeUsbLatencyTimerPort(failure="registre illisible")
        self.assertEqual(port.read_latency_timer_ms("COM10").error, "registre illisible")
        self.assertEqual(port.requested_ports, ["COM10"])


if __name__ == "__main__":
    unittest.main()
