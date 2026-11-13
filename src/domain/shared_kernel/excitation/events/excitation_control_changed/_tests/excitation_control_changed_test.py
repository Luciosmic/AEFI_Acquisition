import unittest

from domain.shared_kernel.excitation.events.excitation_control_changed.excitation_control_changed import (
    ExcitationControlChanged,
)


class TestExcitationControlChanged(unittest.TestCase):
    def test_carries_the_controller(self) -> None:
        self.assertEqual(ExcitationControlChanged(controller="scan").controller, "scan")

    def test_none_means_released(self) -> None:
        self.assertIsNone(ExcitationControlChanged(controller=None).controller)

    def test_is_frozen(self) -> None:
        event = ExcitationControlChanged(controller="scan")
        with self.assertRaises(Exception):
            event.controller = None


if __name__ == "__main__":
    unittest.main()
