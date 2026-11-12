import unittest
from datetime import datetime, timezone
from uuid import uuid4

from domain.measured_object_registry.entities.measured_object.measured_object import MeasuredObject
from domain.measured_object_registry.errors.measured_object_name_blank_error import MeasuredObjectNameBlankError
from domain.measured_object_registry.events.measured_object_registered.measured_object_registered import MeasuredObjectRegistered
from domain.measured_object_registry.measured_object_registry import MeasuredObjectRegistry

LUIS = MeasuredObject(measured_object_id=uuid4(), name="Luis Saluden", registered_at=datetime(2026, 10, 1, tzinfo=timezone.utc))


class TestMeasuredObjectRegistry(unittest.TestCase):
    def test_a_new_name_creates_an_measured_object_and_records_it(self):
        registry = MeasuredObjectRegistry.reconstitute([])

        measured_object, created = registry.register("  Luis   Saluden ")

        self.assertTrue(created)
        self.assertEqual(measured_object.name, "Luis Saluden")
        self.assertEqual(registry.measured_objects, [measured_object])
        events = registry.domain_events
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], MeasuredObjectRegistered)
        self.assertEqual((events[0].measured_object_id, events[0].name), (measured_object.measured_object_id, "Luis Saluden"))

    def test_a_known_spelling_returns_the_existing_measured_object_without_event(self):
        """I1: one measured_object, one spelling — up to case and spacing."""
        registry = MeasuredObjectRegistry.reconstitute([LUIS])

        measured_object, created = registry.register("luis  SALUDEN")

        self.assertFalse(created)
        self.assertIs(measured_object, LUIS)
        self.assertEqual(registry.measured_objects, [LUIS])
        self.assertEqual(registry.domain_events, [])

    def test_a_blank_name_is_refused(self):
        """I2: an measured_object has a name."""
        registry = MeasuredObjectRegistry.reconstitute([])
        for blank in ("", "   ", "\t\n"):
            with self.assertRaises(MeasuredObjectNameBlankError):
                registry.register(blank)
        self.assertEqual(registry.measured_objects, [])

    def test_identities_are_never_reused(self):
        """I3: each new measured_object gets its own stable identity."""
        registry = MeasuredObjectRegistry.reconstitute([LUIS])
        other, _ = registry.register("Marie Curie")
        self.assertNotEqual(other.measured_object_id, LUIS.measured_object_id)

    def test_domain_events_are_handed_out_once(self):
        registry = MeasuredObjectRegistry.reconstitute([])
        registry.register("Marie Curie")
        self.assertEqual(len(registry.domain_events), 1)
        self.assertEqual(registry.domain_events, [])


if __name__ == "__main__":
    unittest.main()
