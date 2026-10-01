import unittest

from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)


class TestHardwareComponentKind(unittest.TestCase):
    def test_every_kind_has_a_label_and_unique_quantity_keys(self):
        for kind in HardwareComponentKind:
            keys = [q.key for q in kind.quantities]
            self.assertTrue(kind.label)
            self.assertTrue(keys)
            self.assertEqual(len(keys), len(set(keys)), kind)

    def test_microcontroller_optimal_rate_is_a_curve_of_n_avg(self):
        spec = {q.key: q for q in HardwareComponentKind.MICROCONTROLLER.quantities}["optimal_acquisition_rate_per_s"]
        self.assertTrue(spec.is_curve)
        self.assertEqual(spec.curve_x_label, "n_avg")


if __name__ == "__main__":
    unittest.main()
