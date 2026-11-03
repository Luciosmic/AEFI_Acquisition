import unittest
from datetime import datetime, timezone
from uuid import uuid4

from domain.operator_registry.entities.operator.operator import Operator
from domain.operator_registry.errors.operator_name_blank_error import OperatorNameBlankError
from domain.operator_registry.events.operator_registered.operator_registered import OperatorRegistered
from domain.operator_registry.operator_registry import OperatorRegistry

LUIS = Operator(operator_id=uuid4(), name="Luis Saluden", registered_at=datetime(2026, 10, 1, tzinfo=timezone.utc))


class TestOperatorRegistry(unittest.TestCase):
    def test_a_new_name_creates_an_operator_and_records_it(self):
        registry = OperatorRegistry.reconstitute([])

        operator, created = registry.register("  Luis   Saluden ")

        self.assertTrue(created)
        self.assertEqual(operator.name, "Luis Saluden")
        self.assertEqual(registry.operators, [operator])
        events = registry.domain_events
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], OperatorRegistered)
        self.assertEqual((events[0].operator_id, events[0].name), (operator.operator_id, "Luis Saluden"))

    def test_a_known_spelling_returns_the_existing_operator_without_event(self):
        """I1: one operator, one spelling — up to case and spacing."""
        registry = OperatorRegistry.reconstitute([LUIS])

        operator, created = registry.register("luis  SALUDEN")

        self.assertFalse(created)
        self.assertIs(operator, LUIS)
        self.assertEqual(registry.operators, [LUIS])
        self.assertEqual(registry.domain_events, [])

    def test_a_blank_name_is_refused(self):
        """I2: an operator has a name."""
        registry = OperatorRegistry.reconstitute([])
        for blank in ("", "   ", "\t\n"):
            with self.assertRaises(OperatorNameBlankError):
                registry.register(blank)
        self.assertEqual(registry.operators, [])

    def test_identities_are_never_reused(self):
        """I3: each new operator gets its own stable identity."""
        registry = OperatorRegistry.reconstitute([LUIS])
        other, _ = registry.register("Marie Curie")
        self.assertNotEqual(other.operator_id, LUIS.operator_id)

    def test_domain_events_are_handed_out_once(self):
        registry = OperatorRegistry.reconstitute([])
        registry.register("Marie Curie")
        self.assertEqual(len(registry.domain_events), 1)
        self.assertEqual(registry.domain_events, [])


if __name__ == "__main__":
    unittest.main()
