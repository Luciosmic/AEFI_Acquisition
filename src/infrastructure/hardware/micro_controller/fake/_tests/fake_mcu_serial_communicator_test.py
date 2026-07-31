import time
import unittest

from infrastructure.hardware.micro_controller.fake.fake_mcu_serial_communicator import (
    FakeMCUSerialCommunicator,
)
from infrastructure.hardware.micro_controller.ad9106.ad9106_controller import AD9106Controller
from infrastructure.hardware.micro_controller.adapter_lifecycle_MCU import MCULifecycleAdapter


class TestFakeMCUSerialCommunicator(unittest.TestCase):
    def test_send_command_fails_when_not_connected(self):
        comm = FakeMCUSerialCommunicator()
        ok, response = comm.send_command("a100")
        self.assertFalse(ok)
        self.assertEqual(response, "Not connected")

    def test_send_command_succeeds_after_connect(self):
        comm = FakeMCUSerialCommunicator()
        comm.connect("COM10", 1500000)
        ok, response = comm.send_command("a100")
        self.assertTrue(ok)
        self.assertEqual(response, "OK")

    def test_acquisition_command_returns_six_valid_channels(self):
        comm = FakeMCUSerialCommunicator()
        comm.connect("COM10")
        ok, response = comm.send_command("m127")
        self.assertTrue(ok)
        codes = [int(x) for x in response.split("\t")]
        self.assertEqual(len(codes), 6)
        for code in codes:
            self.assertTrue(-8388608 <= code <= 8388607)

    def test_disconnect_fails_subsequent_commands(self):
        comm = FakeMCUSerialCommunicator()
        comm.connect("COM10")
        comm.disconnect()
        ok, _ = comm.send_command("a100")
        self.assertFalse(ok)

    def test_real_ad9106_controller_runs_unmodified_against_the_fake(self):
        """The whole point: real domain/adapter code, only the transport is faked."""
        comm = FakeMCUSerialCommunicator()
        comm.connect("COM10")
        controller = AD9106Controller(comm)

        result = controller.set_dds_frequency(2000.0)

        self.assertTrue(result.is_success)

    def test_acquisition_command_is_paced_to_avoid_flooding_continuous_loops(self):
        """AdapterAefiAcquisitionAds131a04's continuous loop has no pacing of
        its own (relies on real ADC round-trip) — without a delay here it
        floods the event bus / Qt main thread within seconds of starting
        continuous acquisition against the fake."""
        comm = FakeMCUSerialCommunicator(acquisition_delay_s=0.01)
        comm.connect("COM10")

        start = time.monotonic()
        comm.send_command("m127")
        elapsed = time.monotonic() - start

        self.assertGreaterEqual(elapsed, 0.01)

    def test_non_acquisition_commands_are_not_paced(self):
        comm = FakeMCUSerialCommunicator(acquisition_delay_s=0.5)
        comm.connect("COM10")

        start = time.monotonic()
        comm.send_command("a100")
        elapsed = time.monotonic() - start

        self.assertLess(elapsed, 0.1)

    def test_mcu_lifecycle_adapter_verify_all_works_against_the_fake(self):
        """MCULifecycleAdapter.verify_all() reaches into communicator.ser.is_open
        directly — the fake must expose a compatible stand-in."""
        comm = FakeMCUSerialCommunicator()
        lifecycle = MCULifecycleAdapter(port="COM10", baudrate=1500000, communicator=comm)

        lifecycle.initialize_all()

        self.assertTrue(lifecycle.verify_all())

        lifecycle.close_all()
        with self.assertRaises(RuntimeError):
            lifecycle.verify_all()


if __name__ == "__main__":
    unittest.main()
