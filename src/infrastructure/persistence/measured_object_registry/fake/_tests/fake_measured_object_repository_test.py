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

    def test_save_all_replaces_and_fails_like_the_real_one(self):
        repository = FakeMeasuredObjectRepository([LUIS])
        self.assertTrue(repository.save_all([]).is_success)
        self.assertEqual(repository.find_all().value, [])
        self.assertTrue(FakeMeasuredObjectRepository([LUIS], read_failure="illisible").save_all([]).is_failure)
        not_writable = FakeMeasuredObjectRepository([LUIS], write_failure="disque plein")
        self.assertTrue(not_writable.save_all([]).is_failure)
        self.assertEqual(not_writable.measured_objects, [LUIS])


if __name__ == "__main__":
    unittest.main()
