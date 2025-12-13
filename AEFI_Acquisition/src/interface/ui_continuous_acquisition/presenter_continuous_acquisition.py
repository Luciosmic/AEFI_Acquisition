from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, Any


from application.services.continuous_acquisition_service.continuous_acquisition_service import (
    ContinuousAcquisitionService,
)
from application.services.continuous_acquisition_service.i_continuous_acquisition_executor import ContinuousAcquisitionConfig
from domain.events.continuous_acquisition_events import (
    ContinuousAcquisitionSampleAcquired,
    ContinuousAcquisitionFailed,
    ContinuousAcquisitionStopped,
)
from domain.events.i_domain_event_bus import IDomainEventBus


class ContinuousAcquisitionPresenter(QObject):
    """
    Presenter pour l'acquisition continue.

    Rôle :
    - Traduire les interactions UI (start/stop) en appels au ContinuousAcquisitionService.
    - S'abonner aux événements de type ContinuousAcquisitionSampleAcquired sur l'EventBus.
    - Émettre des signaux Qt adaptés à la vue (thread‑safe).
    """

    acquisition_started = pyqtSignal(str)  # acquisition_id
    acquisition_stopped = pyqtSignal(str)  # acquisition_id
    acquisition_failed = pyqtSignal(str)   # reason
    sample_acquired = pyqtSignal(dict)  # {acquisition_id, index, measurement:{...}, timestamp}

    def __init__(
        self,
        service: ContinuousAcquisitionService,
        event_bus: IDomainEventBus,
    ) -> None:
        super().__init__()
        self._service = service
        self._event_bus = event_bus
        self._current_acquisition_id: str | None = None

        # Abonnement au flux d'événements domaine
        # Note: Event bus uses lowercase event names (matching publish calls)
        self._event_bus.subscribe(
            "continuousacquisitionsampleacquired",
            self._on_sample_event,
        )
        self._event_bus.subscribe(
            "continuousacquisitionfailed",
            self._on_failed_event,
        )
        self._event_bus.subscribe(
            "continuousacquisitionstopped",
            self._on_stopped_event,
        )

    # ------------------------------------------------------------------ #
    # API appelée par la Vue
    # ------------------------------------------------------------------ #

    def start_acquisition(self, params: Dict[str, Any]) -> None:
        """
        Démarre l'acquisition continue avec une configuration dérivée des paramètres UI.
        """
        config = ContinuousAcquisitionConfig(
            sample_rate_hz=float(params.get("sample_rate_hz", 20.0)),
            max_duration_s=params.get("max_duration_s", None),
            target_uncertainty=None,
        )
        self._service.start_acquisition(config)
        # L'identifiant concret est déterminé à la réception du premier événement.

    def stop_acquisition(self) -> None:
        """Demande l'arrêt de l'acquisition continue."""
        self._service.stop_acquisition()
        if self._current_acquisition_id is not None:
            self.acquisition_stopped.emit(self._current_acquisition_id)

    def update_parameters(self, params: Dict[str, Any]) -> None:
        """Updates acquisition parameters on the fly."""
        config = ContinuousAcquisitionConfig(
            sample_rate_hz=float(params.get("sample_rate_hz", 20.0)),
            max_duration_s=params.get("max_duration_s", None),
            target_uncertainty=None,
        )
        self._service.update_acquisition_parameters(config)

    # ------------------------------------------------------------------ #
    # Gestion des événements domaine
    # ------------------------------------------------------------------ #

    def _on_failed_event(self, event: ContinuousAcquisitionFailed) -> None:
        """Handler for acquisition failure."""
        self.acquisition_failed.emit(str(event.reason))

    def _on_stopped_event(self, event: ContinuousAcquisitionStopped) -> None:
        """Handler for acquisition stop."""
        if self._current_acquisition_id is not None:
            self.acquisition_stopped.emit(str(event.acquisition_id))
            self._current_acquisition_id = None



    def _on_sample_event(self, event: ContinuousAcquisitionSampleAcquired) -> None:
        """
        Handler appelé depuis le thread d'exécution (executor).
        On se contente d'émettre des signaux Qt pour le thread UI.
        """
        acquisition_id_str = str(event.acquisition_id)

        if self._current_acquisition_id is None:
            self._current_acquisition_id = acquisition_id_str
            self.acquisition_started.emit(acquisition_id_str)

        m = event.sample
        
        data = {
            "acquisition_id": acquisition_id_str,
            "index": event.sample_index,
            "measurement": {
                "Ux In-Phase": m.voltage_x_in_phase,
                "Ux Quadrature": m.voltage_x_quadrature,
                
                "Uy In-Phase": m.voltage_y_in_phase,
                "Uy Quadrature": m.voltage_y_quadrature,
                
                "Uz In-Phase": m.voltage_z_in_phase,
                "Uz Quadrature": m.voltage_z_quadrature,
            },
            "timestamp": event.sample.timestamp.isoformat(),
        }
        self.sample_acquired.emit(data)


