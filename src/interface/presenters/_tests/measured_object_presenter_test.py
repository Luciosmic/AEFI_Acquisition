import unittest
from datetime import datetime, timezone
from uuid import uuid4

from application.services.measured_object_service.measured_object_service import MeasuredObjectService
from domain.measured_object_registry.entities.measured_object.measured_object import MeasuredObject
from infrastructure.in_memory_event_bus.in_memory_event_bus import InMemoryEventBus
from infrastructure.persistence.measured_object_registry.fake.fake_measured_object_repository import FakeMeasuredObjectRepository
from interface.presenters.measured_object_presenter import MeasuredObjectPresenter

LUIS = MeasuredObject(measured_object_id=uuid4(), name="Luis Saluden", registered_at=datetime(2026, 10, 1, tzinfo=timezone.utc))


class TestMeasuredObjectPresenter(unittest.TestCase):
    def setUp(self):
        self.repository = FakeMeasuredObjectRepository([LUIS])
        event_bus = InMemoryEventBus()
        self.presenter = MeasuredObjectPresenter(MeasuredObjectService(self.repository, event_bus), event_bus)
        self.listed, self.registered, self.failed = [], [], []
        self.presenter.measured_objects_listed.connect(self.listed.append)
        self.presenter.measured_object_registered.connect(lambda op, already: self.registered.append((op.name, already)))
        self.presenter.registration_failed.connect(self.failed.append)

    def test_refresh_lists_known_measured_objects(self):
        self.presenter.refresh_state()
        self.assertEqual([o.name for o in self.listed[-1]], ["Luis Saluden"])

    def test_new_measured_object_is_reported_and_every_list_refreshed(self):
        self.presenter.on_register_requested("Marie Curie")
        self.assertEqual(self.registered, [("Marie Curie", False)])
        self.assertEqual([o.name for o in self.listed[-1]], ["Luis Saluden", "Marie Curie"])

    def test_known_spelling_is_reported_as_already_registered(self):
        self.presenter.on_register_requested("luis saluden")
        self.assertEqual(self.registered, [("Luis Saluden", True)])

    def test_refusals_are_reported_in_words(self):
        self.presenter.on_register_requested("  ")
        self.assertIn("un objet mesuré a un nom", self.failed[-1])
        self.repository.read_failure = "registre illisible"
        self.presenter.on_register_requested("Marie Curie")
        self.assertIn("registre illisible", self.failed[-1])


if __name__ == "__main__":
    unittest.main()
