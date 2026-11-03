import unittest
from datetime import datetime, timezone
from uuid import uuid4

from domain.operator_registry.entities.operator.operator import Operator


class TestOperator(unittest.TestCase):
    def test_operator_carries_its_identity_name_and_registration_date(self):
        operator_id, at = uuid4(), datetime(2026, 10, 2, tzinfo=timezone.utc)
        operator = Operator(operator_id=operator_id, name="Luis Saluden", registered_at=at)
        self.assertEqual((operator.operator_id, operator.name, operator.registered_at), (operator_id, "Luis Saluden", at))

    def test_operator_is_immutable(self):
        operator = Operator(operator_id=uuid4(), name="Luis", registered_at=datetime.now(timezone.utc))
        with self.assertRaises(Exception):
            operator.name = "Autre"


if __name__ == "__main__":
    unittest.main()
