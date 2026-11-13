import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from domain.measured_object_registry.entities.measured_object.measured_object import MeasuredObject
from infrastructure.persistence.measured_object_registry.real_measured_object_repository import RealMeasuredObjectRepository


def _measured_object(name: str) -> MeasuredObject:
    return MeasuredObject(measured_object_id=uuid4(), name=name, registered_at=datetime(2026, 10, 2, 9, 0, tzinfo=timezone.utc))


class TestRealMeasuredObjectRepository(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "measured_objects" / "measured_objects.json"
        self.repository = RealMeasuredObjectRepository(self.path)

    def test_no_file_means_no_measured_object_yet(self):
        self.assertEqual(self.repository.find_all().value, [])

    def test_added_measured_objects_survive_a_new_repository_instance(self):
        luis, marie = _measured_object("Luis Saluden"), _measured_object("Marie Curie")
        self.assertTrue(self.repository.add(luis).is_success)
        self.assertTrue(self.repository.add(marie).is_success)

        reloaded = RealMeasuredObjectRepository(self.path).find_all().value

        self.assertEqual(reloaded, [luis, marie])  # identity, name and date round-trip

    def test_unreadable_registry_is_a_failure_and_is_never_overwritten(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{not json", encoding="utf-8")

        self.assertTrue(self.repository.find_all().is_failure)
        self.assertTrue(self.repository.add(_measured_object("Luis")).is_failure)
        self.assertEqual(self.path.read_text(encoding="utf-8"), "{not json")

    def test_file_is_plain_json_with_iso_dates(self):
        self.repository.add(_measured_object("Luis Saluden"))
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(data["measured_objects"][0]["name"], "Luis Saluden")
        self.assertEqual(data["measured_objects"][0]["registered_at"], "2026-10-02T09:00:00+00:00")

    def test_save_all_replaces_the_registry(self):
        luis, marie = _measured_object("Luis Saluden"), _measured_object("Marie Curie")
        self.repository.add(luis)
        self.repository.add(marie)

        self.assertTrue(self.repository.save_all([marie]).is_success)

        self.assertEqual(RealMeasuredObjectRepository(self.path).find_all().value, [marie])

    def test_save_all_never_overwrites_an_unreadable_registry(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{not json", encoding="utf-8")
        self.assertTrue(self.repository.save_all([]).is_failure)
        self.assertEqual(self.path.read_text(encoding="utf-8"), "{not json")


if __name__ == "__main__":
    unittest.main()
