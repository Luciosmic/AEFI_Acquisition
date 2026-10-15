"""
Mock IInertialSensorAcquisitionExecutor

Responsibility:
- Record start/stop calls and expose a running flag, without any thread, so
  InertialSensorService is tested without worker timing.
"""

from typing import List, Optional

from application.services.inertial_sensor_service.dtos.inertial_sensor_dtos import (
    InertialSensorAcquisitionConfig,
)
from application.services.inertial_sensor_service.ports.i_inertial_sensor_acquisition_executor import (
    IInertialSensorAcquisitionExecutor,
)
from application.services.inertial_sensor_service.ports.i_inertial_sensor_stream_port import (
    IInertialSensorStreamPort,
)


class MockInertialSensorAcquisitionExecutor(IInertialSensorAcquisitionExecutor):
    def __init__(self) -> None:
        self.started_configs: List[InertialSensorAcquisitionConfig] = []
        self.stop_calls = 0
        self.stream_port: Optional[IInertialSensorStreamPort] = None
        self._running = False

    def start(self, config: InertialSensorAcquisitionConfig, stream_port: IInertialSensorStreamPort) -> None:
        self.started_configs.append(config)
        self.stream_port = stream_port
        self._running = True

    def stop(self) -> None:
        self.stop_calls += 1
        self._running = False

    def is_running(self) -> bool:
        return self._running
