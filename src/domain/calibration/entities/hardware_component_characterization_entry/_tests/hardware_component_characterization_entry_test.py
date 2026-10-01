import unittest

from domain.calibration.entities.hardware_component_characterization_entry.hardware_component_characterization_entry import (
    HardwareComponentCharacterizationEntry,
)
from domain.calibration.value_objects.component_characterization.component_characterization import (
    ComponentCharacterization,
)
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)


class TestHardwareComponentCharacterizationEntry(unittest.TestCase):
    def test_single_mints_distinct_entries_carrying_kind(self):
        characterization = ComponentCharacterization.of(HardwareComponentKind.ADC, {"full_scale_v": 2.442})
        a = HardwareComponentCharacterizationEntry.single("ADS131A04", characterization)
        b = HardwareComponentCharacterizationEntry.single("ADS131A04", characterization)

        self.assertEqual(a.kind, HardwareComponentKind.ADC)
        self.assertNotEqual(a.entry_id, b.entry_id)

    def test_rejects_blank_name(self):
        with self.assertRaises(ValueError):
            HardwareComponentCharacterizationEntry.single(" ", ComponentCharacterization.of(HardwareComponentKind.ADC, {}))


if __name__ == "__main__":
    unittest.main()
