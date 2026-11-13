import unittest
from datetime import datetime, timezone
from uuid import uuid4

from domain.measured_object_registry.events.measured_object_deleted.measured_object_deleted import MeasuredObjectDeleted


class TestMeasuredObjectDeleted(unittest.TestCase):
    def test_carries_a_replayable_snapshot_of_the_removed_measured_object(self) -> None:
        measured_object_id, at = uuid4(), datetime(2026, 11, 13, tzinfo=timezone.utc)
        event = MeasuredObjectDeleted(measured_object_id=measured_object_id, name="plaque", deleted_at=at)
        self.assertEqual((event.measured_object_id, event.name, event.deleted_at), (measured_object_id, "plaque", at))

    def test_is_frozen(self) -> None:
        event = MeasuredObjectDeleted(measured_object_id=uuid4(), name="plaque", deleted_at=datetime.now(timezone.utc))
        with self.assertRaises(Exception):
            event.name = "autre"


if __name__ == "__main__":
    unittest.main()
