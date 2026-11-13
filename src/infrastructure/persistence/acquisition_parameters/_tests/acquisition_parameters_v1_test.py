"""Sections common to every acquisition-parameters 1.0 document."""

import unittest

from application.shared.acquisition_parameters.acquisition_conditions_dtos import BenchPositionDTO
from infrastructure.acquisition_conditions_reader.fake.fake_acquisition_conditions_reader import make_bench_conditions
from infrastructure.persistence.acquisition_parameters import acquisition_parameters_v1 as v1


def _units(node):
    """Every `unit` written anywhere in a section."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "unit" and isinstance(value, str):
                yield value
            else:
                yield from _units(value)
    elif isinstance(node, list):
        for item in node:
            yield from _units(item)


class TestAcquisitionParametersV1(unittest.TestCase):
    def setUp(self):
        self.warnings, self.warn = v1.new_warnings()
        self.conditions = make_bench_conditions()

    def test_common_sections_write_only_declared_ucum_units(self):
        sections = [
            v1.components(self.conditions, self.warn),
            v1.host_link(self.conditions, 1.0, None, self.warn),
            v1.deployment(self.conditions, applies_to_data=True, notes="", warn=self.warn),
            v1.synchronous_detection_state(self.conditions, self.warn),
        ]
        undeclared = {unit for section in sections for unit in _units(section)} - v1.UCUM_UNITS
        self.assertEqual(undeclared, set())

    def test_a_present_but_undescribed_object_is_a_warning(self):
        v1.feature_of_interest(present=True, description=None, notes=None, warn=self.warn, lift_off_mm=8.0)
        self.assertEqual([w["path"] for w in self.warnings], ["feature_of_interest.description"])

    def test_lift_off_is_written_under_its_explicit_name_with_its_unit_and_alias(self):
        section = v1.feature_of_interest(present=True, description="plaque", notes=None, warn=self.warn, lift_off_mm=8.5)
        self.assertEqual(section[v1.LIFT_OFF_KEY], {"value": 8.5, "unit": "mm", "alias": "lift_off"})
        self.assertEqual(v1.LIFT_OFF_KEY, "distance_between_lowest_point_of_sphere_and_highest_point_of_object_under_test")
        self.assertEqual(self.warnings, [])

    def test_a_present_object_without_lift_off_is_written_null_with_a_warning(self):
        section = v1.feature_of_interest(present=True, description="plaque", notes=None, warn=self.warn)
        self.assertIsNone(section[v1.LIFT_OFF_KEY])
        self.assertEqual([w["path"] for w in self.warnings], [f"feature_of_interest.{v1.LIFT_OFF_KEY}"])

    def test_no_object_by_construction_says_why(self):
        section = v1.feature_of_interest(present=False, description=None, notes=None, warn=self.warn, absent_because="excitation coupée")
        self.assertIn("(excitation coupée)", self.warnings[0]["message"])
        self.assertIsNone(section[v1.LIFT_OFF_KEY])  # no object, no distance to it: no second warning
        self.assertEqual(len(self.warnings), 1)

    def test_bench_moved_is_a_warning_only_when_motors_were_not_held(self):
        start, end = BenchPositionDTO(0.0, 0.0), BenchPositionDTO(5.0, 0.0)
        motors = self.conditions.motors
        v1.positioning_state(start, end, None, motors_held=True, warn=self.warn, motors=motors)
        self.assertEqual(self.warnings, [])
        v1.positioning_state(start, end, None, motors_held=False, warn=self.warn, motors=motors)
        self.assertEqual([w["path"] for w in self.warnings], ["measurement_chain.positioning.state"])

    def test_rotation_says_whether_it_applies_to_the_exported_values(self):
        deployment = v1.deployment(self.conditions, applies_to_data=True, notes="tournées", warn=self.warn)
        self.assertTrue(deployment["rotation_applied"]["applies_to_data"])


if __name__ == "__main__":
    unittest.main()
