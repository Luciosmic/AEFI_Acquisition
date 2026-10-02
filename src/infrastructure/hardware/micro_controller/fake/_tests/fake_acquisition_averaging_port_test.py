import unittest

from infrastructure.hardware.micro_controller.fake.fake_acquisition_averaging_port import FakeAcquisitionAveragingPort


class TestFakeAcquisitionAveragingPort(unittest.TestCase):
    def test_set_then_get(self):
        port = FakeAcquisitionAveragingPort(n_avg=127)
        self.assertTrue(port.set_n_avg(8).is_success)
        self.assertEqual(port.get_n_avg(), 8)
        self.assertEqual(port.history, [8])

    def test_out_of_range_is_refused_and_keeps_the_value(self):
        port = FakeAcquisitionAveragingPort(n_avg=16)
        self.assertTrue(port.set_n_avg(128).is_failure)
        self.assertTrue(port.set_n_avg(0).is_failure)
        self.assertEqual(port.get_n_avg(), 16)

    def test_unwritable_config_fails(self):
        port = FakeAcquisitionAveragingPort(n_avg=16, fail_on_set=True)
        self.assertTrue(port.set_n_avg(8).is_failure)
        self.assertEqual(port.get_n_avg(), 16)


if __name__ == "__main__":
    unittest.main()
