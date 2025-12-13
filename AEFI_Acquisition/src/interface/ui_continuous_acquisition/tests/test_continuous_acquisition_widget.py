import sys
import time
from typing import Any

from PyQt6.QtWidgets import QApplication

from infrastructure.tests.diagram_friendly_test import DiagramFriendlyTest
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.tests.mock_ports import MockAcquisitionPort
from infrastructure.execution.continuous_acquisition_executor import (
    ContinuousAcquisitionExecutor,
)

from application.continuous_acquisition_service.continuous_acquisition_service import (
    ContinuousAcquisitionService,
)

from interface.ui_continuous_acquisition.presenter_continuous_acquisition import (
    ContinuousAcquisitionPresenter,
)
from interface.ui_continuous_acquisition.widget_continuous_acquisition import (
    ContinuousAcquisitionWidget,
)


# Assurer une unique instance de QApplication
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)


class TestContinuousAcquisitionWidget(DiagramFriendlyTest):
    """
    Standalone UI test for ContinuousAcquisitionWidget using MockAcquisitionPort.

    Objectif:
    - Simuler un démarrage/arrêt d'acquisition via les boutons du widget.
    - Vérifier que des échantillons sont bien affichés (times + courbes).
    - Générer une trace JSON pour diagramme de séquence.
    """

    def setUp(self) -> None:
        super().setUp()

        self.log_interaction(
            "Test",
            "CREATE",
            "ContinuousAcquisitionWidget",
            "Setup widget, presenter, service, executor, event bus and mock acquisition port",
        )

        # Infrastructure : EventBus + Mock acquisition
        self.event_bus = InMemoryEventBus()
        self.mock_acquisition = MockAcquisitionPort()

        # Executor + Service
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

        # Widget UI
        self.widget = ContinuousAcquisitionWidget(self.presenter)
        self.widget.show()

    def tearDown(self) -> None:
        self.widget.close()
        super().tearDown()

    def test_continuous_acquisition_widget_flow(self) -> None:
        """
        Flow:
        - Configure sample rate / duration via spinboxes
        - Click Start
        - Process events for a short time
        - Click Stop
        - Assert that some data points have been plotted.
        """

        # Configuration UI
        self.log_interaction(
            "Test",
            "ACTION",
            "ContinuousAcquisitionWidget",
            "Set sample_rate=20Hz, max_duration=None (controlled by Stop button)",
            data={
                "sample_rate_hz": 20.0,
                "max_duration_s": None,
            },
        )
        self.widget.sample_rate_spin.setValue(20.0)
        # 0.0 => pas de limite, l'utilisateur (test) choisit quand arrêter
        self.widget.duration_spin.setValue(0.0)

        # Start acquisition via UI button
        self.log_interaction(
            "Test",
            "CLICK",
            "ContinuousAcquisitionWidget",
            "Click Start button",
        )
        self.widget.btn_start.click()

        # Laisser tourner un peu en processant les événements Qt
        self.log_interaction(
            "Test",
            "WAIT",
            "QtEventLoop",
            "Process events during continuous acquisition (widget)",
        )
        end_time = time.time() + 0.25
        while time.time() < end_time:
            app.processEvents()
            time.sleep(0.01)

        # Stop via UI
        self.log_interaction(
            "Test",
            "CLICK",
            "ContinuousAcquisitionWidget",
            "Click Stop button",
        )
        self.widget.btn_stop.click()
        app.processEvents()

        # Assertions : au moins un point dans la timeline et une courbe non vide
        nb_times = len(self.widget.times)
        nb_points_any_channel = max((len(v) for v in self.widget.values.values()), default=0)

        self.log_interaction(
            "Test",
            "ASSERT",
            "ContinuousAcquisitionWidget",
            "Verify at least one time sample recorded",
            expect=">=1",
            got=nb_times,
        )
        assert nb_times >= 1

        self.log_interaction(
            "Test",
            "ASSERT",
            "ContinuousAcquisitionWidget",
            "Verify at least one channel has data",
            expect=">=1",
            got=nb_points_any_channel,
        )
        assert nb_points_any_channel >= 1


if __name__ == "__main__":
    import unittest

    unittest.main()


