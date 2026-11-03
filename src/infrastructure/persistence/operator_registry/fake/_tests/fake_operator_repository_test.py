import unittest
from datetime import datetime, timezone
from uuid import uuid4

from domain.operator_registry.entities.operator.operator import Operator
from infrastructure.persistence.operator_registry.fake.fake_operator_repository import FakeOperatorRepository

LUIS = Operator(operator_id=uuid4(), name="Luis Saluden", registered_at=datetime(2026, 10, 2, tzinfo=timezone.utc))


class TestFakeOperatorRepository(unittest.TestCase):
    def test_added_operators_are_found(self):
        repository = FakeOperatorRepository()
        repository.add(LUIS)
        self.assertEqual(repository.find_all().value, [LUIS])

    def test_unreadable_registry_fails_reads_and_writes_like_the_real_one(self):
        repository = FakeOperatorRepository(read_failure="illisible")
        self.assertTrue(repository.find_all().is_failure)
        self.assertTrue(repository.add(LUIS).is_failure)
        self.assertEqual(repository.operators, [])

    def test_not_writable_registry_fails_writes_only(self):
        repository = FakeOperatorRepository([LUIS], write_failure="disque plein")
        self.assertEqual(repository.find_all().value, [LUIS])
        self.assertTrue(repository.add(LUIS).is_failure)


if __name__ == "__main__":
    unittest.main()
