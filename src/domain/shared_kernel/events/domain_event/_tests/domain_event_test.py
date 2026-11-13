import dataclasses
import unittest
from datetime import timezone
from uuid import UUID

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


class DomainEventTest(unittest.TestCase):
    def test_an_event_carries_a_unique_id_and_a_utc_timestamp(self) -> None:
        first, second = DomainEvent(), DomainEvent()

        self.assertIsInstance(first.event_id, UUID)
        self.assertNotEqual(first.event_id, second.event_id)
        self.assertEqual(first.occurred_on.tzinfo, timezone.utc)

    def test_an_event_is_immutable(self) -> None:
        event = DomainEvent()

        with self.assertRaises(dataclasses.FrozenInstanceError):
            event.event_id = UUID(int=0)  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
