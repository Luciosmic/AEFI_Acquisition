import unittest
from unittest.mock import MagicMock, patch

from infrastructure.hardware.narda_ep600.adapter_electric_field_probe_port import (
    NardaEP601ProbeAdapter,
)


class TestNardaEP601ProbeAdapterFrequencyCorrection(unittest.TestCase):
    def setUp(self):
        patcher = patch(
            "infrastructure.hardware.narda_ep600.adapter_electric_field_probe_port.NardaEP601"
        )
        self.mock_driver_cls = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_driver = MagicMock()
        self.mock_driver_cls.return_value = self.mock_driver

        self.adapter = NardaEP601ProbeAdapter(port="COM8")

    def test_out_of_range_below_10khz_does_not_touch_serial_port(self):
        result = self.adapter.apply_frequency_correction(5_000.0)

        self.mock_driver.set_frequency_correction.assert_not_called()
        assert result.in_range is False
        assert result.applied_hz is None
        assert result.requested_hz == 5_000.0

    def test_in_range_returns_frequency_applied_by_driver(self):
        self.mock_driver.set_frequency_correction.return_value = 50_000.0

        result = self.adapter.apply_frequency_correction(50_000.0)

        self.mock_driver.set_frequency_correction.assert_called_once_with(50_000.0)
        assert result.in_range is True
        assert result.applied_hz == 50_000.0
        assert result.error is None

    def test_driver_mismatch_returns_error_instead_of_raising(self):
        self.mock_driver.set_frequency_correction.side_effect = ValueError(
            "correction non appliquee"
        )

        result = self.adapter.apply_frequency_correction(50_000.0)

        assert result.in_range is True
        assert result.applied_hz is None
        assert result.error == "correction non appliquee"


if __name__ == "__main__":
    unittest.main()
