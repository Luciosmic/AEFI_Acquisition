import unittest
from datetime import datetime, timezone
from uuid import uuid4

from application.services.operator_service.operator_service import OperatorService
from domain.operator_registry.entities.operator.operator import Operator
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.persistence.operator_registry.fake.fake_operator_repository import FakeOperatorRepository
from interface.presenters.operator_presenter import OperatorPresenter

LUIS = Operator(operator_id=uuid4(), name="Luis Saluden", registered_at=datetime(2026, 10, 1, tzinfo=timezone.utc))


class TestOperatorPresenter(unittest.TestCase):
    def setUp(self):
        self.repository = FakeOperatorRepository([LUIS])
        event_bus = InMemoryEventBus()
        self.presenter = OperatorPresenter(OperatorService(self.repository, event_bus), event_bus)
        self.listed, self.registered, self.failed = [], [], []
        self.presenter.operators_listed.connect(self.listed.append)
        self.presenter.operator_registered.connect(lambda op, already: self.registered.append((op.name, already)))
        self.presenter.registration_failed.connect(self.failed.append)

    def test_refresh_lists_known_operators(self):
        self.presenter.refresh_state()
        self.assertEqual([o.name for o in self.listed[-1]], ["Luis Saluden"])

    def test_new_operator_is_reported_and_every_list_refreshed(self):
        self.presenter.on_register_requested("Marie Curie")
        self.assertEqual(self.registered, [("Marie Curie", False)])
        self.assertEqual([o.name for o in self.listed[-1]], ["Luis Saluden", "Marie Curie"])

    def test_known_spelling_is_reported_as_already_registered(self):
        self.presenter.on_register_requested("luis saluden")
        self.assertEqual(self.registered, [("Luis Saluden", True)])

    def test_refusals_are_reported_in_words(self):
        self.presenter.on_register_requested("  ")
        self.assertIn("un opérateur a un nom", self.failed[-1])
        self.repository.read_failure = "registre illisible"
        self.presenter.on_register_requested("Marie Curie")
        self.assertIn("registre illisible", self.failed[-1])


if __name__ == "__main__":
    unittest.main()
