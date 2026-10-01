"""EventLogPresenter against the real service on FakeEventLogStorage."""

import unittest
from datetime import datetime, timedelta, timezone

from application.services.event_log_maintenance_service.event_log_maintenance_service import (
    EventLogMaintenanceService,
)
from application.services.event_log_maintenance_service.ports.i_event_log_storage_port import StoredEventLogSession
from infrastructure.events.fake.fake_event_log_storage import FakeEventLogStorage
from interface.presenters.event_log_presenter import EventLogPresenter

NOW = datetime(2026, 10, 1, tzinfo=timezone.utc)


class TestEventLogPresenter(unittest.TestCase):
    def _presenter(self, *days_ago):
        self.storage = FakeEventLogStorage(
            StoredEventLogSession(f"s{d}", NOW - timedelta(days=d), 100, False) for d in days_ago
        )
        presenter = EventLogPresenter(EventLogMaintenanceService(self.storage, now=lambda: NOW))
        self.summaries, self.confirmations = [], []
        presenter.summary_updated.connect(self.summaries.append)
        presenter.purge_confirmation_needed.connect(self.confirmations.append)
        return presenter

    def test_purge_asks_confirmation_before_deleting(self):
        presenter = self._presenter(120, 10)

        presenter.on_purge_requested()

        self.assertEqual(self.confirmations[-1].expired_session_count, 1)
        self.assertEqual(set(self.storage.sessions), {"s120", "s10"})

        presenter.on_purge_confirmed()

        self.assertEqual(set(self.storage.sessions), {"s10"})
        self.assertEqual(self.summaries[-1].session_count, 1)

    def test_nothing_to_delete_refreshes_without_asking(self):
        presenter = self._presenter(10)

        presenter.on_purge_requested()

        self.assertEqual(self.confirmations, [])
        self.assertEqual(self.summaries[-1].expired_session_count, 0)


if __name__ == "__main__":
    unittest.main()
