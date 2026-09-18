import unittest

from domain.calibration.events.synchronous_detection_compensation_enabled_changed.synchronous_detection_compensation_enabled_changed import (
    SynchronousDetectionCompensationEnabledChanged,
)


class TestSynchronousDetectionCompensationEnabledChanged(unittest.TestCase):
    def test_carries_enabled_flag(self):
        event = SynchronousDetectionCompensationEnabledChanged(enabled=True)
        self.assertTrue(event.enabled)

    def test_is_frozen(self):
        event = SynchronousDetectionCompensationEnabledChanged(enabled=False)
        with self.assertRaises(Exception):
            event.enabled = True


if __name__ == "__main__":
    unittest.main()
