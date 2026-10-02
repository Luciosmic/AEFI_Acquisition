import unittest
from datetime import datetime, timezone
from uuid import uuid4

from domain.operator_registry.events.operator_registered.operator_registered import OperatorRegistered


class TestOperatorRegistered(unittest.TestCase):
    def test_carries_a_replayable_snapshot_of_the_new_operator(self):
        operator_id, at = uuid4(), datetime(2026, 10, 2, tzinfo=timezone.utc)
        event = OperatorRegistered(operator_id=operator_id, name="Luis Saluden", registered_at=at)
        self.assertEqual((event.operator_id, event.name, event.registered_at), (operator_id, "Luis Saluden", at))

    def test_is_frozen(self):
        event = OperatorRegistered(operator_id=uuid4(), name="Luis", registered_at=datetime.now(timezone.utc))
        with self.assertRaises(Exception):
            event.name = "Autre"


if __name__ == "__main__":
    unittest.main()
