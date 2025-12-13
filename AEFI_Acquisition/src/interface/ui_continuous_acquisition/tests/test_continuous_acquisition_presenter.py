import sys
import time
from typing import List, Dict, Any

from PyQt6.QtWidgets import QApplication

from infrastructure.tests.diagram_friendly_test import DiagramFriendlyTest
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.continuous_acquisition_executor import (
    ContinuousAcquisitionExecutor,
)
from infrastructure.tests.mock_ports import MockAcquisitionPort

from application.continuous_acquisition_service.continuous_acquisition_service import (
    ContinuousAcquisitionService,
)

from interface.presenters.continuous_acquisition_presenter import (
    ContinuousAcquisitionPresenter,
)


# Assurer une unique instance de QApplication pour tous les tests UI
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)


class TestContinuousAcquisitionPresenter(DiagramFriendlyTest):
    """
    Test diagram‑friendly pour ContinuousAcquisitionPresenter.

    Utilise MockAcquisitionPort (signal synthétique) + ContinuousAcquisitionExecutor +
    ContinuousAcquisitionService + ContinuousAcquisitionPresenter.
    """

    def setUp(self) -> None:
        super().setUp()

        self.log_interaction(
            "Test",
            "CREATE",
            "ContinuousAcquisitionPresenter",
            "Setup presenter, service, executor, event bus and mock acquisition port",
        )

        # Infrastructure : event bus + mock acquisition (noisy signal)
        self.event_bus = InMemoryEventBus()
        self.mock_acquisition = MockAcquisitionPort()

        # Executor + service
        self.executor = ContinuousAcquisitionExecutor(
            acquisition_port=self.mock_acquisition,
            event_bus=self.event_bus,
        )
        self.service = ContinuousAcquisitionService(self.executor)

        # Presenter
        self.presenter = ContinuousAcquisitionPresenter(
            service=self.service,
            event_bus=self.event_bus,
        )

        # Récupérer les signaux du presenter
        self.samples: List[Dict[str, Any]] = []
        self.started_ids: List[str] = []
        self.stopped_ids: List[str] = []

        self.presenter.acquisition_started.connect(self._on_started)
        self.presenter.acquisition_stopped.connect(self._on_stopped)
        self.presenter.sample_acquired.connect(self._on_sample)

    # ------------------------------------------------------------------ #
    # Slots de test (côté "vue")
    # ------------------------------------------------------------------ #

    def _on_started(self, acquisition_id: str) -> None:
        data = {"acquisition_id": acquisition_id}
        self.log_interaction(
            "View",
            "SIGNAL",
            "Presenter",
            "acquisition_started",
            data=data,
        )
        self.started_ids.append(acquisition_id)

    def _on_stopped(self, acquisition_id: str) -> None:
        data = {"acquisition_id": acquisition_id}
        self.log_interaction(
            "View",
            "SIGNAL",
            "Presenter",
            "acquisition_stopped",
            data=data,
        )
        self.stopped_ids.append(acquisition_id)

    def _on_sample(self, sample_data: Dict[str, Any]) -> None:
        self.log_interaction(
            "View",
            "SIGNAL",
            "Presenter",
            "sample_acquired",
            data=sample_data,
        )
        self.samples.append(sample_data)

    # ------------------------------------------------------------------ #
    # Test principal
    # ------------------------------------------------------------------ #

    def test_continuous_acquisition_presenter_flow(self) -> None:
        """
        Scénario :
        - Start acquisition (20 Hz, 0.1 s max)
        - Laisser tourner un court instant en processant les événements Qt
        - Stop acquisition
        - Vérifier qu'au moins un sample a été reçu et que start/stop ont été signalés.
        """

        params = {"sample_rate_hz": 20.0, "max_duration_s": 0.1}
        self.log_interaction(
            "Test",
            "CALL",
            "ContinuousAcquisitionPresenter",
            "start_acquisition",
            data=params,
        )
        self.presenter.start_acquisition(params)

        # Boucle d'attente avec traitement des événements Qt
        self.log_interaction(
            "Test",
            "WAIT",
            "QtEventLoop",
            "Process events during continuous acquisition",
        )
        end_time = time.time() + 0.25
        while time.time() < end_time:
            app.processEvents()
            time.sleep(0.01)

        self.log_interaction(
            "Test",
            "CALL",
            "ContinuousAcquisitionPresenter",
            "stop_acquisition",
        )
        self.presenter.stop_acquisition()
        app.processEvents()

        # Assertions
        nb_samples = len(self.samples)
        self.log_interaction(
            "Test",
            "ASSERT",
            "ContinuousAcquisitionPresenter",
            "Verify at least one sample acquired via presenter",
            expect=">=1",
            got=nb_samples,
        )
        assert nb_samples >= 1

        self.log_interaction(
            "Test",
            "ASSERT",
            "ContinuousAcquisitionPresenter",
            "Verify acquisition_started signal emitted",
            expect=">=1",
            got=len(self.started_ids),
        )
        assert len(self.started_ids) >= 1

        self.log_interaction(
            "Test",
            "ASSERT",
            "ContinuousAcquisitionPresenter",
            "Verify acquisition_stopped signal emitted",
            expect=">=1",
            got=len(self.stopped_ids),
        )
        assert len(self.stopped_ids) >= 1


if __name__ == "__main__":
    import unittest

    unittest.main()


