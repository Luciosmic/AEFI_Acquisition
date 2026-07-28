import threading
import time
from typing import Optional
from uuid import uuid4

from application.services.aefi_acquisition_service.ports.i_aefi_acquisition_executor import (
    IAefiAcquisitionExecutor,
    AefiAcquisitionConfig,
)
from application.services.scan_application_service.ports.i_acquisition_port import IAcquisitionPort
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.events.aefi_voltage_sample_acquired.aefi_voltage_sample_acquired import (
    AefiVoltageSampleAcquired,
)
from domain.shared_kernel.events.continuous_acquisition_stopped.continuous_acquisition_stopped import (
    ContinuousAcquisitionStopped,
)

class MockAefiAcquisitionExecutor(IAefiAcquisitionExecutor):
    """
    Mock implementation of IAefiAcquisitionExecutor.
    
    Simulates a background thread that "acquires" data from the passed acquisition port.
    """
    
    def __init__(self, event_bus: IDomainEventBus):
        self._event_bus = event_bus
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._current_acquisition_id = None
        
    def start(self, config: AefiAcquisitionConfig, acquisition_port: IAcquisitionPort) -> None:
        """
        Starts a mock acquisition thread.
        """
        if self._is_running:
            print("[MockAefiAcquisitionExecutor] Already running, ignoring start.")
            return

        self._current_acquisition_id = uuid4()
        print(f"[MockAefiAcquisitionExecutor] Starting continuous acquisition (ID={self._current_acquisition_id}). Rate: {config.sample_rate_hz if config.sample_rate_hz else 'MAX'} Hz")
        
        # Configure port only if uncertainty is provided
        if config.target_uncertainty:
             acquisition_port.configure_for_uncertainty(config.target_uncertainty)
             
        self._stop_event.clear()
        self._is_running = True
        
        # Determine sleep time (0.0 means run as fast as possible/yield)
        if config.sample_rate_hz and config.sample_rate_hz > 0:
            interval = 1.0 / config.sample_rate_hz
        else:
            interval = 0.0 # Best effort / max speed
        
        self._current_interval = interval
        
        def _worker():
            sample_index = 0
            while not self._stop_event.is_set():
                if acquisition_port.is_ready():
                    sample = acquisition_port.acquire_sample()
                    
                    event = AefiVoltageSampleAcquired(
                        acquisition_id=self._current_acquisition_id,
                        sample_index=sample_index,
                        sample=sample
                    )
                    self._event_bus.publish(type(event).__name__.lower(), event)
                    sample_index += 1
                
                time.sleep(self._current_interval)
            
            self._is_running = False
            print("[MockAefiAcquisitionExecutor] Stopped.")
            event = ContinuousAcquisitionStopped(acquisition_id=self._current_acquisition_id)
            self._event_bus.publish(type(event).__name__.lower(), event)

        self._thread = threading.Thread(target=_worker, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """
        Signals the worker thread to stop.
        """
        print("[MockAefiAcquisitionExecutor] Stop requested.")
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def update_config(self, config: AefiAcquisitionConfig) -> None:
        """
        Dynamically update configuration of running acquisition.
        """
        print(f"[MockAefiAcquisitionExecutor] Updating config. New Rate: {config.sample_rate_hz} Hz")
        if config.sample_rate_hz and config.sample_rate_hz > 0:
            self._current_interval = 1.0 / config.sample_rate_hz
        else:
            self._current_interval = 0.0

    def is_running(self) -> bool:
        return self._is_running
