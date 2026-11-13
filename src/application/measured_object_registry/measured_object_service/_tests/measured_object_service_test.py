import unittest
from datetime import datetime, timezone
from uuid import uuid4

from application.measured_object_registry.measured_object_service.measured_object_service import (
    MEASURED_OBJECT_DELETED_TOPIC,
    MEASURED_OBJECT_REGISTERED_TOPIC,
    MEASURED_OBJECT_RENAMED_TOPIC,
    MeasuredObjectService,
)
from application.measured_object_registry.measured_object_service.measured_object_service_errors import (
    MeasuredObjectNameBlank,
    MeasuredObjectNameTaken,
    MeasuredObjectNotFound,
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


class TestMeasuredObjectServiceManagement(unittest.TestCase):
    """Rename and delete — the use cases of the Objets mesurés panel."""

    def setUp(self):
        self.marie = MeasuredObject(measured_object_id=uuid4(), name="Marie Curie", registered_at=datetime.now(timezone.utc))
        self.repository = FakeMeasuredObjectRepository([LUIS, self.marie])
        self.event_bus = InMemoryEventBus()
        self.renamed, self.deleted = [], []
        self.event_bus.subscribe(MEASURED_OBJECT_RENAMED_TOPIC, self.renamed.append)
        self.event_bus.subscribe(MEASURED_OBJECT_DELETED_TOPIC, self.deleted.append)
        self.service = MeasuredObjectService(self.repository, self.event_bus)

    def test_a_rename_is_saved_and_published_under_the_same_identity(self):
        result = self.service.rename_measured_object(str(self.marie.measured_object_id), "Marie  Sklodowska")

        self.assertEqual(result.value.name, "Marie Sklodowska")
        self.assertEqual(result.value.measured_object_id, str(self.marie.measured_object_id))
        self.assertEqual([o.name for o in self.repository.measured_objects], ["Luis Saluden", "Marie Sklodowska"])
        self.assertEqual([(e.previous_name, e.name) for e in self.renamed], [("Marie Curie", "Marie Sklodowska")])

    def test_the_same_spelling_saves_and_publishes_nothing(self):
        self.repository.write_failure = "disque plein"  # would fail if it tried to write
        result = self.service.rename_measured_object(str(self.marie.measured_object_id), "Marie Curie")
        self.assertEqual(result.value.name, "Marie Curie")
        self.assertEqual(self.renamed, [])

    def test_a_rename_to_another_spelling_is_refused(self):
        result = self.service.rename_measured_object(str(self.marie.measured_object_id), "luis saluden")
        self.assertIsInstance(result.error, MeasuredObjectNameTaken)
        self.assertIn("Luis Saluden", result.error.message)
        self.assertEqual(self.renamed, [])

    def test_a_blank_rename_is_refused(self):
        result = self.service.rename_measured_object(str(self.marie.measured_object_id), "  ")
        self.assertIsInstance(result.error, MeasuredObjectNameBlank)

    def test_a_deletion_is_saved_and_published(self):
        result = self.service.delete_measured_object(str(self.marie.measured_object_id))

        self.assertEqual(result.value.name, "Marie Curie")
        self.assertEqual(self.repository.measured_objects, [LUIS])
        self.assertEqual([e.name for e in self.deleted], ["Marie Curie"])

    def test_an_unknown_or_malformed_identity_is_not_found(self):
        for identity in (str(uuid4()), "pas-un-uuid"):
            self.assertIsInstance(self.service.delete_measured_object(identity).error, MeasuredObjectNotFound)
            self.assertIsInstance(self.service.rename_measured_object(identity, "x").error, MeasuredObjectNotFound)
        self.assertEqual(len(self.repository.measured_objects), 2)

    def test_registry_failures_change_and_publish_nothing(self):
        self.repository.write_failure = "disque plein"
        self.assertIsInstance(self.service.delete_measured_object(str(LUIS.measured_object_id)).error, MeasuredObjectRegistryUnavailable)
        self.assertIsInstance(self.service.rename_measured_object(str(LUIS.measured_object_id), "Luis").error, MeasuredObjectRegistryUnavailable)
        self.repository.write_failure, self.repository.read_failure = None, "registre illisible"
        self.assertIsInstance(self.service.delete_measured_object(str(LUIS.measured_object_id)).error, MeasuredObjectRegistryUnavailable)
        self.assertEqual(len(self.repository.measured_objects), 2)
        self.assertEqual((self.renamed, self.deleted), ([], []))


if __name__ == "__main__":
    unittest.main()
