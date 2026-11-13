import unittest
from datetime import datetime, timezone
from uuid import uuid4

from domain.measured_object_registry.entities.measured_object.measured_object import MeasuredObject
from domain.measured_object_registry.errors.measured_object_name_blank_error import MeasuredObjectNameBlankError
from domain.measured_object_registry.errors.measured_object_name_taken_error import MeasuredObjectNameTakenError
from domain.measured_object_registry.errors.measured_object_not_found_error import MeasuredObjectNotFoundError
from domain.measured_object_registry.events.measured_object_deleted.measured_object_deleted import MeasuredObjectDeleted
from domain.measured_object_registry.events.measured_object_registered.measured_object_registered import MeasuredObjectRegistered
from domain.measured_object_registry.events.measured_object_renamed.measured_object_renamed import MeasuredObjectRenamed
from domain.measured_object_registry.measured_object_registry import MeasuredObjectRegistry

LUIS = MeasuredObject(measured_object_id=uuid4(), name="Luis Saluden", registered_at=datetime(2026, 10, 1, tzinfo=timezone.utc))
PLAQUE = MeasuredObject(measured_object_id=uuid4(), name="plaque", registered_at=datetime(2026, 10, 2, tzinfo=timezone.utc))


class TestMeasuredObjectRegistry(unittest.TestCase):
    def test_a_new_name_creates_an_measured_object_and_records_it(self) -> None:
        registry = MeasuredObjectRegistry.reconstitute([])

        measured_object, created = registry.register("  Luis   Saluden ")

        self.assertTrue(created)
        self.assertEqual(measured_object.name, "Luis Saluden")
        self.assertEqual(registry.measured_objects, [measured_object])
        events = registry.domain_events
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], MeasuredObjectRegistered)
        self.assertEqual((events[0].measured_object_id, events[0].name), (measured_object.measured_object_id, "Luis Saluden"))

    def test_a_known_spelling_returns_the_existing_measured_object_without_event(self) -> None:
        """I1: one measured_object, one spelling — up to case and spacing."""
        registry = MeasuredObjectRegistry.reconstitute([LUIS])

        measured_object, created = registry.register("luis  SALUDEN")

        self.assertFalse(created)
        self.assertIs(measured_object, LUIS)
        self.assertEqual(registry.measured_objects, [LUIS])
        self.assertEqual(registry.domain_events, [])

    def test_a_blank_name_is_refused(self) -> None:
        """I2: an measured_object has a name."""
        registry = MeasuredObjectRegistry.reconstitute([])
        for blank in ("", "   ", "\t\n"):
            with self.assertRaises(MeasuredObjectNameBlankError):
                registry.register(blank)
        self.assertEqual(registry.measured_objects, [])

    def test_identities_are_never_reused(self) -> None:
        """I3: each new measured_object gets its own stable identity."""
        registry = MeasuredObjectRegistry.reconstitute([LUIS])
        other, _ = registry.register("Marie Curie")
        self.assertNotEqual(other.measured_object_id, LUIS.measured_object_id)

    def test_domain_events_are_handed_out_once(self) -> None:
        registry = MeasuredObjectRegistry.reconstitute([])
        registry.register("Marie Curie")
        self.assertEqual(len(registry.domain_events), 1)
        self.assertEqual(registry.domain_events, [])


class TestMeasuredObjectRegistryRename(unittest.TestCase):
    def test_a_rename_keeps_the_identity_and_records_both_names(self) -> None:
        registry = MeasuredObjectRegistry.reconstitute([LUIS, PLAQUE])

        renamed, changed = registry.rename(PLAQUE.measured_object_id, "  plaque   de cuivre ")

        self.assertTrue(changed)
        self.assertEqual((renamed.measured_object_id, renamed.name), (PLAQUE.measured_object_id, "plaque de cuivre"))
        self.assertEqual(renamed.registered_at, PLAQUE.registered_at)
        self.assertEqual([o.name for o in registry.measured_objects], ["Luis Saluden", "plaque de cuivre"])
        [event] = registry.domain_events
        self.assertIsInstance(event, MeasuredObjectRenamed)
        self.assertEqual((event.previous_name, event.name), ("plaque", "plaque de cuivre"))

    def test_the_same_spelling_changes_nothing(self) -> None:
        registry = MeasuredObjectRegistry.reconstitute([PLAQUE])
        renamed, changed = registry.rename(PLAQUE.measured_object_id, " plaque ")
        self.assertFalse(changed)
        self.assertIs(renamed, PLAQUE)
        self.assertEqual(registry.domain_events, [])

    def test_a_change_of_case_is_a_rename(self) -> None:
        registry = MeasuredObjectRegistry.reconstitute([PLAQUE])
        renamed, changed = registry.rename(PLAQUE.measured_object_id, "Plaque")
        self.assertTrue(changed)
        self.assertEqual(renamed.name, "Plaque")

    def test_the_spelling_of_another_measured_object_is_refused(self) -> None:
        """I1 holds on a rename too."""
        registry = MeasuredObjectRegistry.reconstitute([LUIS, PLAQUE])
        with self.assertRaises(MeasuredObjectNameTakenError):
            registry.rename(PLAQUE.measured_object_id, "luis  saluden")
        self.assertEqual(registry.measured_objects, [LUIS, PLAQUE])
        self.assertEqual(registry.domain_events, [])

    def test_a_blank_name_is_refused(self) -> None:
        registry = MeasuredObjectRegistry.reconstitute([PLAQUE])
        with self.assertRaises(MeasuredObjectNameBlankError):
            registry.rename(PLAQUE.measured_object_id, "  ")

    def test_an_unknown_identity_is_refused(self) -> None:
        registry = MeasuredObjectRegistry.reconstitute([PLAQUE])
        with self.assertRaises(MeasuredObjectNotFoundError):
            registry.rename(uuid4(), "autre")


class TestMeasuredObjectRegistryDelete(unittest.TestCase):
    def test_a_deleted_measured_object_leaves_the_registry_and_is_recorded(self) -> None:
        registry = MeasuredObjectRegistry.reconstitute([LUIS, PLAQUE])

        removed = registry.delete(PLAQUE.measured_object_id)

        self.assertIs(removed, PLAQUE)
        self.assertEqual(registry.measured_objects, [LUIS])
        [event] = registry.domain_events
        self.assertIsInstance(event, MeasuredObjectDeleted)
        self.assertEqual((event.measured_object_id, event.name), (PLAQUE.measured_object_id, "plaque"))

    def test_an_unknown_identity_is_refused(self) -> None:
        registry = MeasuredObjectRegistry.reconstitute([LUIS])
        with self.assertRaises(MeasuredObjectNotFoundError):
            registry.delete(PLAQUE.measured_object_id)
        self.assertEqual(registry.measured_objects, [LUIS])

    def test_the_name_of_a_deleted_measured_object_can_be_registered_again_under_a_new_identity(self) -> None:
        registry = MeasuredObjectRegistry.reconstitute([PLAQUE])
        registry.delete(PLAQUE.measured_object_id)
        again, created = registry.register("plaque")
        self.assertTrue(created)
        self.assertNotEqual(again.measured_object_id, PLAQUE.measured_object_id)


if __name__ == "__main__":
    unittest.main()
