"""ADS131A04Adapter reads n_avg before each sample and sends 'm<n_avg>'."""

import json
import os
import tempfile
import unittest

from infrastructure.hardware.micro_controller.ads131a04.adapter_i_acquistion_port_ads131a04 import ADS131A04Adapter

ADC_CONFIG = {
    "channels": {str(ch): {"gain": 1, "enabled": True} for ch in range(1, 9)},
    "oversampling_ratio": 4096,
    "reference_voltage": 2.442,
}
CONFIG_PATH = os.path.join(".aefi_acquisition", "configs", "mcu_last_config.json")


class RecordingCommunicator:
    def __init__(self):
        self.commands = []

    def send_command(self, command):
        self.commands.append(command)
        return True, "\t".join(["0"] * 6)


class TestAdapterNAvgReading(unittest.TestCase):
    """Runs in a temporary cwd: the default reader uses the relative config path."""

    def setUp(self):
        self._previous_cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)
        os.makedirs(os.path.dirname(CONFIG_PATH))
        self.communicator = RecordingCommunicator()
        self.adapter = ADS131A04Adapter(self.communicator)
        self.adapter.load_config(ADC_CONFIG)

    def tearDown(self):
        os.chdir(self._previous_cwd)
        self._tmp.cleanup()

    def _write(self, text):
        with open(CONFIG_PATH, "w") as f:
            f.write(text)

    def test_sends_the_n_avg_of_the_config_file(self):
        self._write(json.dumps({"n_avg": 32}))
        self.adapter.acquire_sample()
        self.assertEqual(self.communicator.commands, ["m32"])

    def test_file_caught_mid_write_keeps_the_last_n_avg(self):
        """The configurator truncates then writes: an empty read must not
        silently fall back to n_avg=1."""
        self._write(json.dumps({"n_avg": 32}))
        self.adapter.acquire_sample()
        self._write("")

        self.adapter.acquire_sample()

        self.assertEqual(self.communicator.commands, ["m32", "m32"])

    def test_injected_reader_replaces_the_file(self):
        adapter = ADS131A04Adapter(self.communicator, n_avg_reader=lambda: 7)
        adapter.load_config(ADC_CONFIG)
        adapter.acquire_sample()
        self.assertEqual(self.communicator.commands, ["m7"])


if __name__ == "__main__":
    unittest.main()
