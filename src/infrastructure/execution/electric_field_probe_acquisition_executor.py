"""
ElectricFieldProbeAcquisitionExecutor

Responsibility:
- Run a continuous acquisition loop for an electric field probe in a
  background worker thread, publishing domain events for each sample.
- Tolerate a bounded run of consecutive sample failures before treating the
  stream as failed — the Narda probe is known to be flaky (transient
  USB/serial errors), and a single bad read must not kill the streaming
  worker (consumers off the event bus have no way to restart it).

Design:
- Non-blocking `start(config, probe_port)`; loop runs in a daemon thread.
- `stop()` uses an Event flag and join with timeout.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional
from uuid import UUID, uuid4

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
from domain.electric_field_probe.events.electric_field_probe_frequency_correction_changed.electric_field_probe_frequency_correction_changed import (
    ElectricFieldProbeFrequencyCorrectionChanged,
)
from domain.electric_field_probe.events.electric_field_probe_reading_started.electric_field_probe_reading_started import (
    ElectricFieldProbeReadingStarted,
)
from domain.electric_field_probe.events.electric_field_probe_reading_failed.electric_field_probe_reading_failed import (
    ElectricFieldProbeReadingFailed,
)
from domain.electric_field_probe.events.electric_field_probe_reading_stopped.electric_field_probe_reading_stopped import (
    ElectricFieldProbeReadingStopped,
)

logger = logging.getLogger(__name__)

SAMPLE_ACQUIRED_TOPIC = "fieldsampleacquired"
ACQUISITION_STARTED_TOPIC = "electricfieldprobereadingstarted"
ACQUISITION_FAILED_TOPIC = "electricfieldprobereadingfailed"
ACQUISITION_STOPPED_TOPIC = "electricfieldprobereadingstopped"
FREQUENCY_CORRECTION_CHANGED_TOPIC = "electricfieldprobefrequencycorrectionchanged"


class ElectricFieldProbeAcquisitionExecutor(IElectricFieldProbeAcquisitionExecutor):
    # ponytail: events renamed Acquisition->Reading (ElectricFieldProbeReadingStarted/
    # Stopped/Failed) but this class/its port (IElectricFieldProbeAcquisitionExecutor)
    # and the DTOs (ElectricFieldProbeAcquisitionConfig) still say "Acquisition" —
    # cascade deliberately scoped out. Upgrade: rename those too if the
    # vocabulary mismatch causes real confusion.
    MAX_CONSECUTIVE_SAMPLE_FAILURES = 2

    # ponytail: fixed inter-sample delay, not a configurable rate. Acquisition
    # is best-effort — against the real Narda probe, its own serial
    # round-trip already paces the loop and this sleep barely adds delay on
    # top. But this same executor also drives FakeElectricFieldProbeAdapter
    # in mock hardware mode, whose acquire_sample() is near-instant pure
    # Python — without this floor the loop would flood the event bus / Qt UI
    # with samples. 50Hz mirrors the real probe's own physical ceiling (its
    # fastest filter response is ~33Hz at F1), so the simulated cadence stays
    # realistic rather than an arbitrary throttle.
    _SAMPLE_INTERVAL_S = 0.02

    def __init__(self, event_bus: IDomainEventBus) -> None:
        self._event_bus = event_bus
        self._thread: threading.Thread | None = None
        self._stop_flag = threading.Event()
        self._current_acquisition_id: UUID | None = None
        self._pending_frequency_hz: Optional[float] = None

    def start(
        self,
        config: ElectricFieldProbeAcquisitionConfig,
        probe_port: IElectricFieldProbePort,
    ) -> None:
        if self._thread and self._thread.is_alive():
            return

        # Clear any stale request left over from a previous run — the correct
        # frequency is already applied on the probe via the not-running path
        # (ElectricFieldProbeService._on_excitation_frequency_changed), so a
        # fresh worker must not blindly replay an old request_frequency_correction()
        # call from a prior start/stop cycle.
        self._pending_frequency_hz = None
        self._stop_flag.clear()
        self._current_acquisition_id = uuid4()
        self._thread = threading.Thread(
            target=self._worker,
            args=(self._current_acquisition_id, config, probe_port),
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_flag.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def request_frequency_correction(self, frequency_hz: float) -> None:
        # Ecriture de reference unique (atomique sous le GIL) — le worker la lit a chaque
        # iteration. Jamais reinitialisee a None : un read-then-clear introduirait une fenetre
        # ou une requete concurrente serait silencieusement perdue.
        self._pending_frequency_hz = frequency_hz

    # ------------------------------------------------------------------ #
    # Internal worker
    # ------------------------------------------------------------------ #

    def _worker(
        self,
        acquisition_id: UUID,
        config: ElectricFieldProbeAcquisitionConfig,
        probe_port: IElectricFieldProbePort,
    ) -> None:
        started_event = ElectricFieldProbeReadingStarted(acquisition_id=acquisition_id)
        self._event_bus.publish(ACQUISITION_STARTED_TOPIC, started_event)

        t0 = time.time()
        index = 0
        probe = probe_port.get_probe()
        serial_number = probe.serial_number if probe else "unknown"
        consecutive_failures = 0
        last_requested_frequency_hz: Optional[float] = None

        try:
            while not self._stop_flag.is_set():
                if (
                    config.max_duration_s is not None
                    and (time.time() - t0) > config.max_duration_s
                ):
                    break

                requested_frequency_hz = self._pending_frequency_hz
                if (
                    requested_frequency_hz is not None
                    and requested_frequency_hz != last_requested_frequency_hz
                ):
                    last_requested_frequency_hz = requested_frequency_hz
                    try:
                        result = probe_port.apply_frequency_correction(
                            requested_frequency_hz
                        )
                        self._event_bus.publish(
                            FREQUENCY_CORRECTION_CHANGED_TOPIC,
                            ElectricFieldProbeFrequencyCorrectionChanged(
                                requested_hz=result.requested_hz,
                                applied_hz=result.applied_hz,
                                in_range=result.in_range,
                                error=result.error,
                            ),
                        )
                    except Exception as e:
                        self._event_bus.publish(
                            FREQUENCY_CORRECTION_CHANGED_TOPIC,
                            ElectricFieldProbeFrequencyCorrectionChanged(
                                requested_hz=requested_frequency_hz,
                                applied_hz=None,
                                in_range=True,
                                error=str(e),
                            ),
                        )

                try:
                    sample = probe_port.acquire_sample()
                except Exception as e:
                    consecutive_failures += 1
                    logger.warning(
                        "Field probe sample failed (%d/%d consecutive): %s",
                        consecutive_failures,
                        self.MAX_CONSECUTIVE_SAMPLE_FAILURES,
                        e,
                    )
                    if consecutive_failures > self.MAX_CONSECUTIVE_SAMPLE_FAILURES:
                        error_event = ElectricFieldProbeReadingFailed(
                            acquisition_id=acquisition_id, reason=str(e)
                        )
                        self._event_bus.publish(ACQUISITION_FAILED_TOPIC, error_event)
                        return
                    time.sleep(self._SAMPLE_INTERVAL_S)
                    continue

                consecutive_failures = 0
                event = FieldSampleAcquired(
                    probe_serial_number=serial_number,
                    acquisition_id=acquisition_id,
                    sample_index=index,
                    sample=sample,
                )
                self._event_bus.publish(SAMPLE_ACQUIRED_TOPIC, event)

                index += 1
                time.sleep(self._SAMPLE_INTERVAL_S)

        except Exception as e:
            logger.error("Acquisition loop raised unexpectedly: %s", e)
            error_event = ElectricFieldProbeReadingFailed(
                acquisition_id=acquisition_id, reason=str(e)
            )
            self._event_bus.publish(ACQUISITION_FAILED_TOPIC, error_event)
        finally:
            stop_event = ElectricFieldProbeReadingStopped(acquisition_id=acquisition_id)
            self._event_bus.publish(ACQUISITION_STOPPED_TOPIC, stop_event)
