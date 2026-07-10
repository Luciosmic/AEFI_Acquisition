"""
Electric Field Probe Application Service

Responsibility:
- Connect/disconnect the probe on demand, absorbing hardware exceptions.
- Run a continuous acquisition loop in a background task via IAsyncTaskRunner.
- Own the stop signal (threading.Event) that controls the acquisition loop.

Rationale:
- The acquisition loop contains use-case logic (rate control, max-duration
  enforcement, event publication) and belongs in the Application layer.
- The stop condition is an application concept ("the caller asked us to stop"),
  not an infrastructure concern — so the threading.Event lives here.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional
from uuid import UUID, uuid4

from application._shared.ports.i_async_task_runner import IAsyncTaskRunner, TaskHandle
from application.services.electric_field_probe_service.i_api_electric_field_probe_service import (
    IApiElectricFieldProbeService,
)
from application.services.electric_field_probe_service.ports.i_electric_field_probe_port import (
    IElectricFieldProbePort,
)
from application.services.electric_field_probe_service.dtos.electric_field_probe_dtos import (
    ElectricFieldProbeAcquisitionConfig,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.electric_field_probe.events.electric_field_probe_connection_changed.electric_field_probe_connection_changed import (
    ElectricFieldProbeConnectionChanged,
)
from domain.electric_field_probe.events.field_sample_acquired.field_sample_acquired import (
    FieldSampleAcquired,
)
from domain.shared_kernel.events.continuous_acquisition_failed.continuous_acquisition_failed import (
    ContinuousAcquisitionFailed,
)
from domain.shared_kernel.events.continuous_acquisition_stopped.continuous_acquisition_stopped import (
    ContinuousAcquisitionStopped,
)

logger = logging.getLogger(__name__)

CONNECTION_CHANGED_TOPIC = "electricfieldprobeconnectionchanged"
SAMPLE_ACQUIRED_TOPIC = "fieldsampleacquired"
ACQUISITION_FAILED_TOPIC = "electricfieldprobeacquisitionfailed"
ACQUISITION_STOPPED_TOPIC = "electricfieldprobeacquisitionstopped"


class ElectricFieldProbeService(IApiElectricFieldProbeService):
    """Application service for a generic electric field probe."""

    def __init__(
        self,
        task_runner: IAsyncTaskRunner,
        probe_port: IElectricFieldProbePort,
        event_bus: IDomainEventBus,
    ) -> None:
        self._task_runner = task_runner
        self._probe_port = probe_port
        self._event_bus = event_bus
        self._stop_flag = threading.Event()
        self._current_task: Optional[TaskHandle] = None

    def connect_probe(self) -> None:
        try:
            self._probe_port.connect()
        except Exception as e:
            self._event_bus.publish(
                CONNECTION_CHANGED_TOPIC,
                ElectricFieldProbeConnectionChanged(connected=False, error=str(e)),
            )
            return
        self._event_bus.publish(
            CONNECTION_CHANGED_TOPIC,
            ElectricFieldProbeConnectionChanged(
                connected=True, probe=self._probe_port.get_probe()
            ),
        )

    def disconnect_probe(self) -> None:
        self._probe_port.disconnect()
        self._event_bus.publish(
            CONNECTION_CHANGED_TOPIC,
            ElectricFieldProbeConnectionChanged(connected=False),
        )

    def start_acquisition(self, config: ElectricFieldProbeAcquisitionConfig) -> None:
        if self._current_task and self._current_task.is_running():
            return
        self._stop_flag.clear()
        acquisition_id = uuid4()
        self._current_task = self._task_runner.submit(
            lambda: self._acquisition_loop(acquisition_id, config, self._probe_port)
        )

    def stop_acquisition(self) -> None:
        self._stop_flag.set()
        if self._current_task:
            self._current_task.wait(timeout=2.0)
            self._current_task = None

    def update_acquisition_parameters(
        self, config: ElectricFieldProbeAcquisitionConfig
    ) -> None:
        if self._current_task and self._current_task.is_running():
            self.stop_acquisition()
        self.start_acquisition(config)

    # ------------------------------------------------------------------ #
    # Acquisition loop (runs inside the task submitted to IAsyncTaskRunner)
    # ------------------------------------------------------------------ #

    def _acquisition_loop(
        self,
        acquisition_id: UUID,
        config: ElectricFieldProbeAcquisitionConfig,
        probe_port: IElectricFieldProbePort,
    ) -> None:
        if config.sample_rate_hz <= 0:
            return

        dt = 1.0 / config.sample_rate_hz
        t0 = time.time()
        index = 0
        probe = probe_port.get_probe()
        serial_number = probe.serial_number if probe else "unknown"

        try:
            while not self._stop_flag.is_set():
                if (
                    config.max_duration_s is not None
                    and (time.time() - t0) > config.max_duration_s
                ):
                    break

                try:
                    sample = probe_port.acquire_sample()
                except Exception as e:
                    error_event = ContinuousAcquisitionFailed(
                        acquisition_id=acquisition_id, reason=str(e)
                    )
                    self._event_bus.publish(ACQUISITION_FAILED_TOPIC, error_event)
                    return

                event = FieldSampleAcquired(
                    probe_serial_number=serial_number,
                    acquisition_id=acquisition_id,
                    sample_index=index,
                    sample=sample,
                )
                self._event_bus.publish(SAMPLE_ACQUIRED_TOPIC, event)

                index += 1
                time.sleep(dt)

        except Exception as e:
            logger.error("Acquisition loop raised unexpectedly: %s", e)
            error_event = ContinuousAcquisitionFailed(
                acquisition_id=acquisition_id, reason=str(e)
            )
            self._event_bus.publish(ACQUISITION_FAILED_TOPIC, error_event)
        finally:
            stop_event = ContinuousAcquisitionStopped(acquisition_id=acquisition_id)
            self._event_bus.publish(ACQUISITION_STOPPED_TOPIC, stop_event)
