import unittest
from datetime import datetime, timezone
from uuid import uuid4

from domain.measured_object_registry.events.measured_object_registered.measured_object_registered import MeasuredObjectRegistered


class TestMeasuredObjectRegistered(unittest.TestCase):
    def test_carries_a_replayable_snapshot_of_the_new_measured_object(self):
        measured_object_id, at = uuid4(), datetime(2026, 10, 2, tzinfo=timezone.utc)
        event = MeasuredObjectRegistered(measured_object_id=measured_object_id, name="Luis Saluden", registered_at=at)
        self.assertEqual((event.measured_object_id, event.name, event.registered_at), (measured_object_id, "Luis Saluden", at))

    def test_is_frozen(self):
        event = MeasuredObjectRegistered(measured_object_id=uuid4(), name="Luis", registered_at=datetime.now(timezone.utc))
        with self.assertRaises(Exception):
            event.name = "Autre"


if __name__ == "__main__":
    unittest.main()
