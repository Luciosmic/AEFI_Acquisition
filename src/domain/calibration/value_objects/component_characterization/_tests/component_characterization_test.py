import unittest

from domain.calibration.value_objects.component_characterization.component_characterization import (
    ComponentCharacterization,
)
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)

MCU = HardwareComponentKind.MICROCONTROLLER
BOARD = HardwareComponentKind.EXCITATION_ELECTRONICS_BOARD


class TestComponentCharacterization(unittest.TestCase):
    def test_left_out_quantities_are_not_characterized(self):
        characterization = ComponentCharacterization.of(BOARD, {"bandwidth_hz": 1e6})

        self.assertEqual(characterization.values, {"gain": None, "bandwidth_hz": 1e6})
        self.assertEqual(characterization.uncharacterized(), ["gain"])

    def test_everything_may_be_uncharacterized(self):
        self.assertEqual(ComponentCharacterization.of(BOARD, {}).uncharacterized(), ["gain", "bandwidth_hz"])

    def test_curve_is_normalized_to_tuples(self):
        characterization = ComponentCharacterization.of(MCU, {"optimal_acquisition_rate_per_s": [[1, 1000], [10, 800]]})

        self.assertEqual(characterization.values["optimal_acquisition_rate_per_s"], ((1.0, 1000.0), (10.0, 800.0)))

    def test_rejects_non_positive_scalar_and_bad_curve_and_unknown_key(self):
        with self.assertRaises(ValueError):
            ComponentCharacterization.of(BOARD, {"gain": 0.0})
        with self.assertRaises(ValueError):
            ComponentCharacterization.of(MCU, {"optimal_acquisition_rate_per_s": [(0, 5)]})
        with self.assertRaises(ValueError):
            ComponentCharacterization.of(BOARD, {"gian": 2.0})


if __name__ == "__main__":
    unittest.main()
