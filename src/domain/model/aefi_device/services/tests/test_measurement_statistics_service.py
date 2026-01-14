import unittest
from datetime import datetime
import math

from domain.model.aefi_device.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from domain.model.aefi_device.services.measurement_statistics_service import MeasurementStatisticsService

class TestMeasurementStatisticsService(unittest.TestCase):
    def log(self, msg: str):
        # Trace TDD : préfixe pour identifier l'origine
        print(f"[TestMeasurementStatisticsService] {msg}")
    
    def create_measurement(self, val: float) -> VoltageMeasurement:
        return VoltageMeasurement(
            voltage_x_in_phase=val, voltage_x_quadrature=val,
            voltage_y_in_phase=val, voltage_y_quadrature=val,
            voltage_z_in_phase=val, voltage_z_quadrature=val,
            timestamp=datetime.now()
        )

    def test_empty_list_raises_error(self):
        self.log("test_empty_list_raises_error start | expect ValueError")
        with self.assertRaises(ValueError):
            MeasurementStatisticsService.calculate_statistics([])
        self.log("test_empty_list_raises_error passed | ValueError raised as expected")

    def test_single_measurement(self):
        expected_mean = 1.0
        expected_std = 0.0
        self.log(f"test_single_measurement start | expect mean={expected_mean} std={expected_std}")
        m = self.create_measurement(1.0)
        result = MeasurementStatisticsService.calculate_statistics([m])
        
        self.assertEqual(result.voltage_x_in_phase, 1.0)
        self.assertEqual(result.std_dev_x_in_phase, 0.0)
        self.log(f"test_single_measurement expect mean={expected_mean} std={expected_std} | got mean={result.voltage_x_in_phase} std={result.std_dev_x_in_phase}")

    def test_statistics_calculation(self):
        expected_mean = 2.0
        expected_std = 1.0
        self.log(f"test_statistics_calculation start | expect mean={expected_mean} std={expected_std}")
        # Values: 1.0, 2.0, 3.0
        # Mean: 2.0
        # Variance (Sample): ((1-2)^2 + (2-2)^2 + (3-2)^2) / (3-1) = (1 + 0 + 1) / 2 = 1.0
        # Std Dev: sqrt(1.0) = 1.0
        
        measurements = [
            self.create_measurement(1.0),
            self.create_measurement(2.0),
            self.create_measurement(3.0)
        ]
        
        result = MeasurementStatisticsService.calculate_statistics(measurements)
        
        # Check Mean
        self.assertAlmostEqual(result.voltage_x_in_phase, 2.0)
        self.assertAlmostEqual(result.voltage_x_quadrature, 2.0)
        
        # Check Std Dev
        self.assertAlmostEqual(result.std_dev_x_in_phase, 1.0)
        self.assertAlmostEqual(result.std_dev_x_quadrature, 1.0)
        self.log(f"test_statistics_calculation expect mean={expected_mean} std={expected_std} | got mean={result.voltage_x_in_phase} std={result.std_dev_x_in_phase}")

    def test_statistics_calculation_more_complex(self):
        expected_mean = 5.0
        expected_std = math.sqrt(32/7)
        self.log(f"test_statistics_calculation_more_complex start | expect mean={expected_mean} std={expected_std}")
        # Values: 2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0
        # Mean: 5.0
        # Sum: 40
        # Count: 8
        # Variance Sum: 9 + 1 + 1 + 1 + 0 + 0 + 4 + 16 = 32
        # Variance: 32 / 7 = 4.5714...
        # Std Dev: sqrt(4.5714) = 2.138
        
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        measurements = [self.create_measurement(v) for v in values]
        
        result = MeasurementStatisticsService.calculate_statistics(measurements)
        
        self.assertAlmostEqual(result.voltage_x_in_phase, 5.0)
        self.assertAlmostEqual(result.std_dev_x_in_phase, math.sqrt(32/7), places=4)
        self.log(f"test_statistics_calculation_more_complex expect mean={expected_mean} std={expected_std} | got mean={result.voltage_x_in_phase} std={result.std_dev_x_in_phase}")

if __name__ == '__main__':
    unittest.main()
