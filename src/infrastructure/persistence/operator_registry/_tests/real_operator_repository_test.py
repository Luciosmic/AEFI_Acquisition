import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from domain.operator_registry.entities.operator.operator import Operator
from infrastructure.persistence.operator_registry.real_operator_repository import RealOperatorRepository


def _operator(name: str) -> Operator:
    return Operator(operator_id=uuid4(), name=name, registered_at=datetime(2026, 10, 2, 9, 0, tzinfo=timezone.utc))


class TestRealOperatorRepository(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "operators" / "operators.json"
        self.repository = RealOperatorRepository(self.path)

    def test_no_file_means_no_operator_yet(self):
        self.assertEqual(self.repository.find_all().value, [])

    def test_added_operators_survive_a_new_repository_instance(self):
        luis, marie = _operator("Luis Saluden"), _operator("Marie Curie")
        self.assertTrue(self.repository.add(luis).is_success)
        self.assertTrue(self.repository.add(marie).is_success)

        reloaded = RealOperatorRepository(self.path).find_all().value

        self.assertEqual(reloaded, [luis, marie])  # identity, name and date round-trip

    def test_unreadable_registry_is_a_failure_and_is_never_overwritten(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{not json", encoding="utf-8")

        self.assertTrue(self.repository.find_all().is_failure)
        self.assertTrue(self.repository.add(_operator("Luis")).is_failure)
        self.assertEqual(self.path.read_text(encoding="utf-8"), "{not json")

    def test_file_is_plain_json_with_iso_dates(self):
        self.repository.add(_operator("Luis Saluden"))
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(data["operators"][0]["name"], "Luis Saluden")
        self.assertEqual(data["operators"][0]["registered_at"], "2026-10-02T09:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
