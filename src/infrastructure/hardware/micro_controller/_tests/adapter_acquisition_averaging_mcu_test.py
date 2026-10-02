import os
import tempfile
import unittest
from types import SimpleNamespace

from infrastructure.hardware.micro_controller.adapter_acquisition_averaging_mcu import AdapterAcquisitionAveragingMcu
from infrastructure.hardware.micro_controller.fake.fake_mcu_serial_communicator import FakeMCUSerialCommunicator
from infrastructure.hardware.micro_controller.mcu_advanced_configurator import MCUAdvancedConfigurator


class TestAdapterAcquisitionAveragingMcu(unittest.TestCase):
    """Runs in a temporary working directory: MCUAdvancedConfigurator writes
    .aefi_acquisition/configs/mcu_last_config.json relative to the cwd."""

    def setUp(self):
        self._previous_cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)
        os.makedirs(os.path.join(".aefi_acquisition", "configs"))
        controller = SimpleNamespace(memory_state={"Oversampling_ratio": 2048})
        self.adapter = AdapterAcquisitionAveragingMcu(MCUAdvancedConfigurator(FakeMCUSerialCommunicator()), controller)

    def tearDown(self):
        os.chdir(self._previous_cwd)
        self._tmp.cleanup()

    def test_set_n_avg_is_read_back(self):
        self.assertTrue(self.adapter.set_n_avg(16).is_success)
        self.assertEqual(self.adapter.get_n_avg(), 16)

    def test_out_of_range_is_a_failure_not_an_exception(self):
        self.adapter.set_n_avg(16)
        result = self.adapter.set_n_avg(500)
        self.assertTrue(result.is_failure)
        self.assertEqual(self.adapter.get_n_avg(), 16)

    def test_range_and_oversampling_ratio(self):
        self.assertEqual(self.adapter.get_n_avg_range(), (1, 127))
        self.assertEqual(self.adapter.get_oversampling_ratio(), 2048)

    def test_locks_the_mcu_and_adc_configurations(self):
        self.assertEqual(self.adapter.get_configuration_hardware_ids(), ("mcu", "ads131a04"))


if __name__ == "__main__":
    unittest.main()
