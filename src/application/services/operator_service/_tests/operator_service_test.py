import unittest
from datetime import datetime, timezone
from uuid import uuid4

from application.services.operator_service.operator_service import OPERATOR_REGISTERED_TOPIC, OperatorService
from application.services.operator_service.operator_service_errors import (
    OperatorNameBlank,
    OperatorRegistryUnavailable,
)
from domain.operator_registry.entities.operator.operator import Operator
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.persistence.operator_registry.fake.fake_operator_repository import FakeOperatorRepository

LUIS = Operator(operator_id=uuid4(), name="Luis Saluden", registered_at=datetime(2026, 10, 1, tzinfo=timezone.utc))


class TestOperatorService(unittest.TestCase):
    def setUp(self):
        self.repository = FakeOperatorRepository([LUIS])
        self.event_bus = InMemoryEventBus()
        self.published = []
        self.event_bus.subscribe(OPERATOR_REGISTERED_TOPIC, self.published.append)
        self.service = OperatorService(self.repository, self.event_bus)

    def test_lists_known_operators_sorted_by_name(self):
        self.repository.operators.append(
            Operator(operator_id=uuid4(), name="Anne Dupont", registered_at=datetime.now(timezone.utc))
        )
        names = [o.name for o in self.service.list_operators().value]
        self.assertEqual(names, ["Anne Dupont", "Luis Saluden"])

    def test_registering_a_new_operator_persists_and_publishes_it(self):
        result = self.service.register_operator("Marie  Curie")

        registration = result.value
        self.assertFalse(registration.already_registered)
        self.assertEqual(registration.operator.name, "Marie Curie")
        self.assertEqual([o.name for o in self.repository.operators], ["Luis Saluden", "Marie Curie"])
        self.assertEqual([e.name for e in self.published], ["Marie Curie"])
        self.assertEqual(str(self.published[0].operator_id), registration.operator.operator_id)

    def test_a_known_spelling_returns_the_existing_operator_and_changes_nothing(self):
        result = self.service.register_operator("luis saluden")

        registration = result.value
        self.assertTrue(registration.already_registered)
        self.assertEqual(registration.operator.operator_id, str(LUIS.operator_id))
        self.assertEqual(len(self.repository.operators), 1)
        self.assertEqual(self.published, [])

    def test_blank_name_is_refused(self):
        result = self.service.register_operator("   ")
        self.assertIsInstance(result.error, OperatorNameBlank)
        self.assertEqual(self.published, [])

    def test_unreadable_registry_is_unavailable_for_listing_and_registering(self):
        self.repository.read_failure = "registre illisible"
        self.assertIsInstance(self.service.list_operators().error, OperatorRegistryUnavailable)
        result = self.service.register_operator("Marie Curie")
        self.assertIsInstance(result.error, OperatorRegistryUnavailable)
        self.assertIn("registre illisible", result.error.reason)

    def test_failed_write_publishes_nothing(self):
        self.repository.write_failure = "disque plein"
        result = self.service.register_operator("Marie Curie")
        self.assertIsInstance(result.error, OperatorRegistryUnavailable)
        self.assertEqual(self.published, [])


if __name__ == "__main__":
    unittest.main()
