"""
Mock IInertialProbeAcquisitionExecutor

Responsibility:
- Record start/stop calls and expose a running flag, without any thread, so
  InertialProbeService is tested without worker timing.
"""

from typing import List, Optional

from application.inertial_probe.inertial_probe_service.dtos.inertial_probe_dtos import (
    InertialProbeAcquisitionConfig,
)
from application.inertial_probe.inertial_probe_service.ports.i_inertial_probe_acquisition_executor import (
    IInertialProbeAcquisitionExecutor,
)
from application.inertial_probe.inertial_probe_service.ports.i_inertial_probe_stream_port import (
    IInertialProbeStreamPort,
)


class MockInertialProbeAcquisitionExecutor(IInertialProbeAcquisitionExecutor):
    def __init__(self) -> None:
        self.started_configs: List[InertialProbeAcquisitionConfig] = []
        self.stop_calls = 0
        self.stream_port: Optional[IInertialProbeStreamPort] = None
        self._running = False

    def start(self, config: InertialProbeAcquisitionConfig, stream_port: IInertialProbeStreamPort) -> None:
        self.started_configs.append(config)
        self.stream_port = stream_port
        self._running = True

    def stop(self) -> None:
        self.stop_calls += 1
        self._running = False

    def is_running(self) -> bool:
        return self._running
