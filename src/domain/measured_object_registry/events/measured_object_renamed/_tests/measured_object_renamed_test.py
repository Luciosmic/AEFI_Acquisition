import unittest
from datetime import datetime, timezone
from uuid import uuid4

from domain.measured_object_registry.events.measured_object_renamed.measured_object_renamed import MeasuredObjectRenamed


class TestMeasuredObjectRenamed(unittest.TestCase):
    def test_carries_both_names(self) -> None:
        measured_object_id, at = uuid4(), datetime(2026, 11, 13, tzinfo=timezone.utc)
        event = MeasuredObjectRenamed(measured_object_id=measured_object_id, previous_name="hexagone", name="cylindre", renamed_at=at)
        self.assertEqual((event.previous_name, event.name, event.renamed_at), ("hexagone", "cylindre", at))

    def test_is_frozen(self) -> None:
        event = MeasuredObjectRenamed(measured_object_id=uuid4(), previous_name="a", name="b", renamed_at=datetime.now(timezone.utc))
        with self.assertRaises(Exception):
            event.name = "c"


if __name__ == "__main__":
    unittest.main()
