import unittest

from application.shared.exclusive_control.exclusive_control import ExclusiveControl, take_all


class TestExclusiveControl(unittest.TestCase):
    def setUp(self):
        self.changes = []
        self.control = ExclusiveControl("flux d'acquisition", self.changes.append)

    def test_free_resource_refuses_nobody(self):
        self.assertIsNone(self.control.controller)
        self.assertIsNone(self.control.refusal(None, "stop"))

    def test_owner_is_the_only_one_allowed(self):
        self.assertTrue(self.control.take("scan").is_success)
        self.assertIsNone(self.control.refusal("scan", "stop"))
        self.assertIn("scan", self.control.refusal(None, "stop"))
        self.assertIn("scan", self.control.refusal("calibration", "stop"))

    def test_second_controller_is_refused(self):
        self.control.take("scan")
        result = self.control.take("calibration")
        self.assertTrue(result.is_failure)
        self.assertIn("flux d'acquisition", result.error)
        self.assertEqual(self.control.controller, "scan")

    def test_changes_are_reported_once(self):
        self.control.take("scan")
        self.control.take("scan")
        self.control.release("calibration")  # not the owner: ignored
        self.control.release("scan")
        self.control.release("scan")
        self.assertEqual(self.changes, ["scan", None])


class TestTakeAll(unittest.TestCase):
    def setUp(self):
        self.a = ExclusiveControl("a", lambda c: None)
        self.b = ExclusiveControl("b", lambda c: None)

    def _takes(self, who):
        return [
            (lambda: self.a.take(who), lambda: self.a.release(who)),
            (lambda: self.b.take(who), lambda: self.b.release(who)),
        ]

    def test_takes_everything_then_releases_everything(self):
        result = take_all(self._takes("calibration"))
        self.assertTrue(result.is_success)
        self.assertEqual((self.a.controller, self.b.controller), ("calibration", "calibration"))
        for release in result.value:
            release()
        self.assertEqual((self.a.controller, self.b.controller), (None, None))

    def test_one_refusal_gives_back_what_was_taken(self):
        self.b.take("scan")

        result = take_all(self._takes("calibration"))

        self.assertTrue(result.is_failure)
        self.assertIn("scan", result.error)
        self.assertIsNone(self.a.controller)
        self.assertEqual(self.b.controller, "scan")


if __name__ == "__main__":
    unittest.main()
