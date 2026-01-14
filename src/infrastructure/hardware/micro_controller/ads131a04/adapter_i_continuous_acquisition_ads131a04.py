"""
ADS131A04 Continuous Acquisition Adapter

Responsibility:
- Implement IContinuousAcquisitionExecutor for the ADS131A04 hardware.
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

from application.services.continuous_acquisition_service.i_continuous_acquisition_executor import (
    IContinuousAcquisitionExecutor,
    ContinuousAcquisitionConfig,
)
from application.services.scan_application_service.i_acquisition_port import IAcquisitionPort
from domain.events.i_domain_event_bus import IDomainEventBus
from domain.events.continuous_acquisition_events import (
    ContinuousAcquisitionSampleAcquired,
    ContinuousAcquisitionFailed,
    ContinuousAcquisitionStopped,
)

class AdapterIContinuousAcquisitionAds131a04(IContinuousAcquisitionExecutor):
    """
    Adapter for continuous acquisition using ADS131A04.
    """
    
    def __init__(self, event_bus: IDomainEventBus) -> None:
        self._event_bus = event_bus
        self._thread: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()
        self._current_acquisition_id: Optional[UUID] = None

    def start(self, config: ContinuousAcquisitionConfig, acquisition_port: IAcquisitionPort) -> None:
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

    def update_config(self, config: ContinuousAcquisitionConfig) -> None:
        """Update configuration (not fully supported in this simple version yet)."""
        # TODO: Implement dynamic config update if needed
        pass

    def _worker(
        self,
        acquisition_id: UUID,
        config: ContinuousAcquisitionConfig,
        acquisition_port: IAcquisitionPort,
    ) -> None:
        """Background acquisition loop."""
        print(f"[ContinuousAcquisition] Worker started. ID: {acquisition_id}")
        if not config.sample_rate_hz or config.sample_rate_hz <= 0:
            print("[ContinuousAcquisition] Invalid sample rate.")
            return

        dt = 1.0 / config.sample_rate_hz
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
                    # DEBUG: Trace sample index (every 10 samples to avoid spam)
                    if index % 10 == 0:
                        print(f"[ContinuousAcquisition] Acquired sample #{index}")
                except Exception as e:
                    print(f"[ContinuousAcquisition] Error acquiring sample: {e}")
                    raise e

                # Publish event
                event = ContinuousAcquisitionSampleAcquired(
                    acquisition_id=acquisition_id,
                    sample_index=index,
                    sample=sample,
                )
                self._event_bus.publish("continuousacquisitionsampleacquired", event)

                index += 1
                
                # Simple timing control (drift prone but sufficient for basic polling)
                # For high precision, we would rely on hardware timing.
                time.sleep(dt)
                
        except Exception as e:
            print(f"[ContinuousAcquisition] Loop failed: {e}")
            error_event = ContinuousAcquisitionFailed(
                acquisition_id=acquisition_id,
                reason=str(e)
            )
            self._event_bus.publish("continuousacquisitionfailed", error_event)
        finally:
            print("[ContinuousAcquisition] Worker stopping.")
            stop_event = ContinuousAcquisitionStopped(acquisition_id=acquisition_id)
            self._event_bus.publish("continuousacquisitionstopped", stop_event)
