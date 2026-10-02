import unittest

from infrastructure.hardware.micro_controller.ads131a04.adapter_adc_oversampling_ads131a04 import (
    AdapterAdcOversamplingAds131a04,
)
from infrastructure.hardware.micro_controller.ads131a04.ads131_controller import ADS131Controller
from infrastructure.hardware.micro_controller.fake.fake_mcu_serial_communicator import FakeMCUSerialCommunicator


class TestAdapterAdcOversamplingAds131a04(unittest.TestCase):
    def setUp(self):
        communicator = FakeMCUSerialCommunicator()
        communicator.connect("COM_TEST")
        self.controller = ADS131Controller(communicator)
        self.adapter = AdapterAdcOversamplingAds131a04(self.controller)

    def test_written_osr_is_read_back_from_the_controller(self):
        self.assertTrue(self.adapter.set_oversampling_ratio(512).is_success)
        self.assertEqual(self.adapter.get_oversampling_ratio(), 512)
        self.assertEqual(self.controller.memory_state["ICLK_divider_ratio"], 2)  # divider kept

    def test_osr_refused_by_the_chip_is_a_failure(self):
        self.assertTrue(self.adapter.set_oversampling_ratio(1000).is_failure)

    def test_disconnected_mcu_is_a_failure(self):
        adapter = AdapterAdcOversamplingAds131a04(ADS131Controller(FakeMCUSerialCommunicator()))
        result = adapter.set_oversampling_ratio(512)
        self.assertTrue(result.is_failure)
        self.assertIn("Not connected", result.error)


if __name__ == "__main__":
    unittest.main()
