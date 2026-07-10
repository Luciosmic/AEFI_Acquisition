"""
ElectricFieldProbeAcquisitionExecutor

Responsibility:
- Run a continuous acquisition loop in a background worker thread using the
  IElectricFieldProbePort and publish domain events for each sample.

Design:
- Mirrors ContinuousAcquisitionExecutor, kept separate to avoid coupling
  electric_field_probe to VoltageMeasurement.
- Non-blocking `start(config, probe_port)`; loop runs in a daemon thread.
- `stop()` uses an Event flag and join with timeout.
"""

from __future__ import annotations

import threading
import time
from uuid import uuid4, UUID

from application.services.electric_field_probe_service.ports.i_electric_field_probe_acquisition_executor import (
    IElectricFieldProbeAcquisitionExecutor,
)
from application.services.electric_field_probe_service.ports.i_electric_field_probe_port import (
    IElectricFieldProbePort,
)
from application.services.electric_field_probe_service.dtos.electric_field_probe_dtos import (
    ElectricFieldProbeAcquisitionConfig,
)

from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.electric_field_probe.events.field_sample_acquired.field_sample_acquired import (
    FieldSampleAcquired,
)
from domain.shared_kernel.events.continuous_acquisition_failed.continuous_acquisition_failed import (
    ContinuousAcquisitionFailed,
)
from domain.shared_kernel.events.continuous_acquisition_stopped.continuous_acquisition_stopped import (
    ContinuousAcquisitionStopped,
)

SAMPLE_ACQUIRED_TOPIC = "fieldsampleacquired"
ACQUISITION_FAILED_TOPIC = "electricfieldprobeacquisitionfailed"
ACQUISITION_STOPPED_TOPIC = "electricfieldprobeacquisitionstopped"


class ElectricFieldProbeAcquisitionExecutor(IElectricFieldProbeAcquisitionExecutor):
    def __init__(self, event_bus: IDomainEventBus) -> None:
        self._event_bus = event_bus
        self._thread: threading.Thread | None = None
        self._stop_flag = threading.Event()
        self._current_acquisition_id: UUID | None = None

    def update_config(self, config: ElectricFieldProbeAcquisitionConfig) -> None:
        """Dynamically update configuration of a running acquisition."""
        # Config is re-read from the worker's local variable each loop via
        # closures would be needed for live update; kept simple for now,
        # matching ContinuousAcquisitionExecutor's current behaviour.
        pass

    def start(
        self,
        config: ElectricFieldProbeAcquisitionConfig,
        probe_port: IElectricFieldProbePort,
    ) -> None:
        """Start a new continuous acquisition in the background."""
        if self._thread and self._thread.is_alive():
            return

        self._stop_flag.clear()
        self._current_acquisition_id = uuid4()
        self._thread = threading.Thread(
            target=self._worker,
            args=(self._current_acquisition_id, config, probe_port),
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Request graceful stop of the running acquisition."""
        self._stop_flag.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    # ------------------------------------------------------------------ #
    # Internal worker
    # ------------------------------------------------------------------ #

    def _worker(
        self,
        acquisition_id: UUID,
        config: ElectricFieldProbeAcquisitionConfig,
        probe_port: IElectricFieldProbePort,
    ) -> None:
        """Background acquisition loop."""
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

                sample = probe_port.acquire_sample()

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
            error_event = ContinuousAcquisitionFailed(
                acquisition_id=acquisition_id, reason=str(e)
            )
            self._event_bus.publish(ACQUISITION_FAILED_TOPIC, error_event)
        finally:
            stop_event = ContinuousAcquisitionStopped(acquisition_id=acquisition_id)
            self._event_bus.publish(ACQUISITION_STOPPED_TOPIC, stop_event)
