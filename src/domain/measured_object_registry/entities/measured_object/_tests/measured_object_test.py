import unittest
from datetime import datetime, timezone
from uuid import uuid4

from domain.measured_object_registry.entities.measured_object.measured_object import MeasuredObject


class TestMeasuredObject(unittest.TestCase):
    def test_measured_object_carries_its_identity_name_and_registration_date(self) -> None:
        measured_object_id, at = uuid4(), datetime(2026, 10, 2, tzinfo=timezone.utc)
        measured_object = MeasuredObject(measured_object_id=measured_object_id, name="Luis Saluden", registered_at=at)
        self.assertEqual((measured_object.measured_object_id, measured_object.name, measured_object.registered_at), (measured_object_id, "Luis Saluden", at))

    def test_measured_object_is_immutable(self) -> None:
        measured_object = MeasuredObject(measured_object_id=uuid4(), name="Luis", registered_at=datetime.now(timezone.utc))
        with self.assertRaises(Exception):
            measured_object.name = "Autre"


if __name__ == "__main__":
    unittest.main()
