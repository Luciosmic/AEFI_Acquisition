import unittest
from datetime import datetime, timezone
from uuid import uuid4

from application.services.measured_object_service.measured_object_service import MEASURED_OBJECT_REGISTERED_TOPIC, MeasuredObjectService
from application.services.measured_object_service.measured_object_service_errors import (
    MeasuredObjectNameBlank,
    MeasuredObjectRegistryUnavailable,
)
from domain.measured_object_registry.entities.measured_object.measured_object import MeasuredObject
from infrastructure.in_memory_event_bus.in_memory_event_bus import InMemoryEventBus
from infrastructure.persistence.measured_object_registry.fake.fake_measured_object_repository import FakeMeasuredObjectRepository

LUIS = MeasuredObject(measured_object_id=uuid4(), name="Luis Saluden", registered_at=datetime(2026, 10, 1, tzinfo=timezone.utc))


class TestMeasuredObjectService(unittest.TestCase):
    def setUp(self):
        self.repository = FakeMeasuredObjectRepository([LUIS])
        self.event_bus = InMemoryEventBus()
        self.published = []
        self.event_bus.subscribe(MEASURED_OBJECT_REGISTERED_TOPIC, self.published.append)
        self.service = MeasuredObjectService(self.repository, self.event_bus)

    def test_lists_known_measured_objects_sorted_by_name(self):
        self.repository.measured_objects.append(
            MeasuredObject(measured_object_id=uuid4(), name="Anne Dupont", registered_at=datetime.now(timezone.utc))
        )
        names = [o.name for o in self.service.list_measured_objects().value]
        self.assertEqual(names, ["Anne Dupont", "Luis Saluden"])

    def test_registering_a_new_measured_object_persists_and_publishes_it(self):
        result = self.service.register_measured_object("Marie  Curie")

        registration = result.value
        self.assertFalse(registration.already_registered)
        self.assertEqual(registration.measured_object.name, "Marie Curie")
        self.assertEqual([o.name for o in self.repository.measured_objects], ["Luis Saluden", "Marie Curie"])
        self.assertEqual([e.name for e in self.published], ["Marie Curie"])
        self.assertEqual(str(self.published[0].measured_object_id), registration.measured_object.measured_object_id)

    def test_a_known_spelling_returns_the_existing_measured_object_and_changes_nothing(self):
        result = self.service.register_measured_object("luis saluden")

        registration = result.value
        self.assertTrue(registration.already_registered)
        self.assertEqual(registration.measured_object.measured_object_id, str(LUIS.measured_object_id))
        self.assertEqual(len(self.repository.measured_objects), 1)
        self.assertEqual(self.published, [])

    def test_blank_name_is_refused(self):
        result = self.service.register_measured_object("   ")
        self.assertIsInstance(result.error, MeasuredObjectNameBlank)
        self.assertEqual(self.published, [])

    def test_unreadable_registry_is_unavailable_for_listing_and_registering(self):
        self.repository.read_failure = "registre illisible"
        self.assertIsInstance(self.service.list_measured_objects().error, MeasuredObjectRegistryUnavailable)
        result = self.service.register_measured_object("Marie Curie")
        self.assertIsInstance(result.error, MeasuredObjectRegistryUnavailable)
        self.assertIn("registre illisible", result.error.reason)

    def test_failed_write_publishes_nothing(self):
        self.repository.write_failure = "disque plein"
        result = self.service.register_measured_object("Marie Curie")
        self.assertIsInstance(result.error, MeasuredObjectRegistryUnavailable)
        self.assertEqual(self.published, [])


if __name__ == "__main__":
    unittest.main()
