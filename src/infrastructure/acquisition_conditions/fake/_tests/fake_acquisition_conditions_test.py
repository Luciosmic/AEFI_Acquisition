import unittest

from application.shared.acquisition_parameters.acquisition_conditions_dtos import (
    BenchPositionDTO,
)
from infrastructure.acquisition_conditions.fake.fake_acquisition_conditions_port import (
    FakeAcquisitionConditionsPort,
    make_bench_conditions,
)


class TestFakeAcquisitionConditionsPort(unittest.TestCase):
    def test_default_bench_mounts_every_kind(self):
        kinds = {c.kind for c in FakeAcquisitionConditionsPort().read_conditions().components}
        self.assertEqual(len(kinds), 7)

    def test_positions_are_returned_in_turn_and_the_last_repeats(self):
        start, end = BenchPositionDTO(1.0, 2.0), BenchPositionDTO(3.0, 4.0)
        port = FakeAcquisitionConditionsPort(positions=[start, end])
        self.assertEqual([port.read_bench_position().value for _ in range(3)], [start, end, end])

    def test_disconnected_motors_are_a_failure(self):
        port = FakeAcquisitionConditionsPort(position_failure="moteurs non connectés")
        self.assertTrue(port.read_bench_position().is_failure)

    def test_given_conditions_are_returned(self):
        conditions = make_bench_conditions()
        port = FakeAcquisitionConditionsPort(conditions=conditions)
        self.assertIs(port.read_conditions(), conditions)
        self.assertEqual(port.conditions_reads, 1)


if __name__ == "__main__":
    unittest.main()
