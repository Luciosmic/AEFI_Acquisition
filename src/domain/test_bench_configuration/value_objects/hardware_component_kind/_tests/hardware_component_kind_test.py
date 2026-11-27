import unittest

from domain.test_bench_configuration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareAssembly,
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

    def test_dds_adc_and_microcontroller_form_the_digital_analog_signals_processing_unit(self):
        unit = HardwareAssembly.DIGITAL_ANALOG_SIGNALS_PROCESSING_UNIT
        members = {kind for kind in HardwareComponentKind if kind.assembly is unit}

        self.assertEqual(
            members,
            {
                HardwareComponentKind.SIGNAL_GENERATION_CHIP,
                HardwareComponentKind.ADC,
                HardwareComponentKind.MICROCONTROLLER,
            },
        )
        self.assertEqual(unit.value, "digital_analog_signals_processing_unit")
        self.assertEqual(unit.label, "Unité de conversion entre signaux numériques et analogiques")

    def test_conditioning_board_and_excitation_stay_outside_the_unit(self):
        self.assertIsNone(HardwareComponentKind.CONDITIONING_ELECTRONICS_BOARD.assembly)
        self.assertIsNone(HardwareComponentKind.EXCITATION_ELECTRONICS_BOARD.assembly)

    def test_conditioning_board_declares_the_sign_of_its_quadrature_output(self):
        spec = {q.key: q for q in HardwareComponentKind.CONDITIONING_ELECTRONICS_BOARD.quantities}[
            "quadrature_output_sign"
        ]
        self.assertEqual(spec.allowed_values, (-1.0, 1.0))


if __name__ == "__main__":
    unittest.main()
