import unittest
from datetime import datetime, timezone
from uuid import uuid4

from domain.measured_object_registry.entities.measured_object.measured_object import MeasuredObject
from infrastructure.persistence.measured_object_registry.fake.fake_measured_object_repository import FakeMeasuredObjectRepository

LUIS = MeasuredObject(measured_object_id=uuid4(), name="Luis Saluden", registered_at=datetime(2026, 10, 2, tzinfo=timezone.utc))


class TestFakeMeasuredObjectRepository(unittest.TestCase):
    def test_added_measured_objects_are_found(self):
        repository = FakeMeasuredObjectRepository()
        repository.add(LUIS)
        self.assertEqual(repository.find_all().value, [LUIS])

    def test_unreadable_registry_fails_reads_and_writes_like_the_real_one(self):
        repository = FakeMeasuredObjectRepository(read_failure="illisible")
        self.assertTrue(repository.find_all().is_failure)
        self.assertTrue(repository.add(LUIS).is_failure)
        self.assertEqual(repository.measured_objects, [])

    def test_not_writable_registry_fails_writes_only(self):
        repository = FakeMeasuredObjectRepository([LUIS], write_failure="disque plein")
        self.assertEqual(repository.find_all().value, [LUIS])
        self.assertTrue(repository.add(LUIS).is_failure)


if __name__ == "__main__":
    unittest.main()
