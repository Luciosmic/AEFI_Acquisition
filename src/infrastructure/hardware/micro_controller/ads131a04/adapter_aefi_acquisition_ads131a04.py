"""
ADS131A04 Continuous Acquisition Adapter

Responsibility:
- Implement IAefiAcquisitionExecutor for the ADS131A04 hardware.
- Manage the continuous acquisition loop using a background thread.
- Publish events via the EventBus.

Rationale:
- Provides a concrete implementation for continuous acquisition specific to this hardware context.
- Currently uses polling (threading) but can be extended to use hardware interrupts/streaming if available.
"""

from __future__ import annotations

import threading
import time
from uuid import uuid4, UUID
from typing import Optional

from application.services.aefi_acquisition_service.ports.i_aefi_acquisition_executor import (
    IAefiAcquisitionExecutor,
    AefiAcquisitionConfig,
)
from application.services.scan_application_service.ports.i_acquisition_port import IAcquisitionPort
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.events.aefi_voltage_sample_acquired.aefi_voltage_sample_acquired import (
    AefiVoltageSampleAcquired,
)
from domain.shared_kernel.events.aefi_voltage_reading_started.aefi_voltage_reading_started import (
    AefiVoltageReadingStarted,
)
from domain.shared_kernel.events.aefi_voltage_reading_failed.aefi_voltage_reading_failed import (
    AefiVoltageReadingFailed,
)
from domain.shared_kernel.events.aefi_voltage_reading_stopped.aefi_voltage_reading_stopped import (
    AefiVoltageReadingStopped,
)

class AdapterAefiAcquisitionAds131a04(IAefiAcquisitionExecutor):
    """
    Adapter for continuous acquisition using ADS131A04.
    """
    
    def __init__(self, event_bus: IDomainEventBus) -> None:
        self._event_bus = event_bus
        self._thread: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()
        self._current_acquisition_id: Optional[UUID] = None

    def start(self, config: AefiAcquisitionConfig, acquisition_port: IAcquisitionPort) -> None:
        """
        Start continuous acquisition.
        """
        if self._thread and self._thread.is_alive():
            return

        self._stop_flag.clear()
        self._current_acquisition_id = uuid4()
        
        # Start background worker
        self._thread = threading.Thread(
            target=self._worker,
            args=(self._current_acquisition_id, config, acquisition_port),
            daemon=True,
            name="ADS131A04_Acquisition_Thread"
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop continuous acquisition."""
        self._stop_flag.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _worker(
        self,
        acquisition_id: UUID,
        config: AefiAcquisitionConfig,
        acquisition_port: IAcquisitionPort,
    ) -> None:
        """Background acquisition loop."""
        print(f"[ContinuousAcquisition] Worker started. ID: {acquisition_id}")
        started_event = AefiVoltageReadingStarted(acquisition_id=acquisition_id)
        self._event_bus.publish("aefivoltagereadingstarted", started_event)

        # Best-effort: acquire back-to-back at whatever rate the serial link
        # allows. The ADC round-trip (OSR x n_avg, set in hardware advanced
        # config) dominates timing by orders of magnitude, so no software
        # pacing is added here.
        t0 = time.time()
        index = 0

        try:
            while not self._stop_flag.is_set():
                # Check duration limit
                if config.max_duration_s is not None and (time.time() - t0) > config.max_duration_s:
                    print("[ContinuousAcquisition] Max duration reached.")
                    break

                # Acquire sample
                # Note: In a real hardware streaming scenario, we might block here waiting for an interrupt
                # or read from a buffer. For now, we poll the single-shot acquisition.
                try:
                    sample = acquisition_port.acquire_sample()
                except Exception as e:
                    print(f"[ContinuousAcquisition] Error acquiring sample: {e}")
                    raise e

                # Publish event
                event = AefiVoltageSampleAcquired(
                    acquisition_id=acquisition_id,
                    sample_index=index,
                    sample=sample,
                )
                self._event_bus.publish("aefivoltagesampleacquired", event)

                index += 1

        except Exception as e:
            print(f"[ContinuousAcquisition] Loop failed: {e}")
            error_event = AefiVoltageReadingFailed(
                acquisition_id=acquisition_id,
                reason=str(e)
            )
            self._event_bus.publish("aefivoltagereadingfailed", error_event)
        finally:
            print("[ContinuousAcquisition] Worker stopping.")
            stop_event = AefiVoltageReadingStopped(acquisition_id=acquisition_id)
            self._event_bus.publish("aefivoltagereadingstopped", stop_event)
