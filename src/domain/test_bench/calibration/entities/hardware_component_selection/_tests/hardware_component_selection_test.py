import unittest

from domain.test_bench.calibration.entities.hardware_component_selection.hardware_component_selection import (
    HardwareComponentSelection,
)
from domain.test_bench.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)


class TestHardwareComponentSelection(unittest.TestCase):
    def test_now_stamps_selection(self):
        selection = HardwareComponentSelection.now(HardwareComponentKind.MOTORS, "Arcus_4EX")
        self.assertEqual(selection.component_name, "Arcus_4EX")
        self.assertIsNotNone(selection.selected_at.tzinfo)

    def test_rejects_blank_name(self):
        with self.assertRaises(ValueError):
            HardwareComponentSelection.now(HardwareComponentKind.MOTORS, "")


if __name__ == "__main__":
    unittest.main()
