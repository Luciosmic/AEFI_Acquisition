import unittest

from infrastructure.execution.fake.fake_clock import FakeClock


class FakeClockTest(unittest.TestCase):
    def test_time_only_moves_on_sleep(self):
        clock = FakeClock(start_s=10.0)
        self.assertEqual(clock.now(), 10.0)
        clock.sleep(0.25)
        self.assertEqual(clock.now(), 10.25)

    def test_refuses_negative_sleep(self):
        with self.assertRaises(ValueError):
            FakeClock().sleep(-1.0)


if __name__ == "__main__":
    unittest.main()
