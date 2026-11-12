"""
Driver jog / hard limit switch reading, over a stub pylablib stage (the real
Performax4EXStage reports the switches as 'sw_plus_lim' / 'sw_minus_lim' in
get_status, from the MST status bits 0x010 / 0x020).
"""

import unittest

from infrastructure.hardware.arcus_performax_4ex.driver_arcus_performax4ex import ArcusPerformax4EXController


class _StubStage:
    def __init__(self):
        self.jogs = []
        self.status = {"x": ["sw_plus_lim"], "y": ["moving"]}

    def jog(self, axis, direction):
        self.jogs.append((axis, direction))

    def get_status(self, axis):
        return self.status[axis]


class DriverLimitSwitchTest(unittest.TestCase):
    def setUp(self):
        self.driver = ArcusPerformax4EXController()
        self.stage = _StubStage()
        self.driver._stage = self.stage

    def test_jog_forwards_the_direction_once_homed(self):
        self.driver.set_homed("x")
        self.driver.jog("X", "+")
        self.assertEqual(self.stage.jogs, [("x", "+")])

    def test_jog_refused_before_homing(self):
        with self.assertRaises(RuntimeError):
            self.driver.jog("y", "+")

    def test_jog_refuses_an_unknown_direction(self):
        self.driver.set_homed("x")
        with self.assertRaises(ValueError):
            self.driver.jog("x", "up")

    def test_limit_read_from_status_flags(self):
        self.assertTrue(self.driver.is_at_limit("x", "+"))
        self.assertFalse(self.driver.is_at_limit("x", "-"))
        self.assertFalse(self.driver.is_at_limit("y", "+"))


if __name__ == "__main__":
    unittest.main()
