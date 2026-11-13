"""
Integration test: the scan loops settle each point (step scan) or each line
start (fly scan) on the accelerometer when it streams, and fall back to the
fixed stabilization delay when it does not. Short criterion (rest 0.2 s,
window 0.1 s) and an accelerometer stream simulated on the real event bus.
"""
import threading
import time
import unittest

from application.services.aefi_acquisition_service.aefi_acquisition_service import AefiAcquisitionService
from application.services.scan_application_service.column_stabilization.column_stabilization import (
    ACCELEROMETER,
    FIXED_DELAY,
    INERTIAL_PROBE_SAMPLE_TOPIC,
    ColumnStabilization,
)
from application.services.scan_application_service.dtos.scan_dtos import Scan2DConfigDTO
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.scan_application_service.scan_closure_handler.scan_closure_handler import ScanClosureHandler
from domain.detection_devices.inertial_probe.events.inertial_probe_sample_acquired.inertial_probe_sample_acquired import (
    InertialProbeSampleAcquired,
)
from domain.scan.value_objects.column_rest_criterion.column_rest_criterion import ColumnRestCriterion
from domain.step_scan.value_objects.scan_status.scan_status import ScanStatus
from infrastructure.in_memory_event_bus.in_memory_event_bus import InMemoryEventBus
from infrastructure.event_bus_motion_synchronizer.event_bus_motion_synchronizer import EventBusMotionSynchronizer
from infrastructure.execution.thread_pool_task_runner import ThreadPoolTaskRunner
from infrastructure.hardware.arcus_performax_4ex.adapter_motion_port_arcus_performax4ex import ArcusAdapter
from infrastructure.hardware.arcus_performax_4ex.fake.fake_arcus_performax4ex_controller import (
    FakeArcusPerformax4EXController,
)
from infrastructure.mocks.adapter_mock_i_acquisition_port import MockAcquisitionPort
from infrastructure.mocks.adapter_mock_i_aefi_acquisition_executor import MockAefiAcquisitionExecutor
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.unit_of_work.in_memory_unit_of_work import InMemoryUnitOfWork
from uuid import uuid4

SHORT = ColumnRestCriterion(rest_measurement_s=0.2, window_s=0.1, factor=1.5, timeout_s=1.0)
DELAY_MS = 50


class _RecordingStabilization(ColumnStabilization):
    def __init__(self, event_bus):
        super().__init__(event_bus, criterion=SHORT)
        self.rests, self.outcomes = [], []

    def measure_rest(self, *args, **kwargs):
        self.rests.append(super().measure_rest(*args, **kwargs))
        return self.rests[-1]

    def wait_until_settled(self, *args, **kwargs):
        self.outcomes.append(super().wait_until_settled(*args, **kwargs))
        return self.outcomes[-1]


class _StillAccelerometer:
    """Streams a still column (±2 mg) at 200 Hz, timestamped on perf_counter like the real worker."""

    def __init__(self, event_bus):
        self._bus, self._stop = event_bus, threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def start(self) -> None:
        self._thread.start()
        time.sleep(0.05)  # started by the operator before the scan

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(1.0)

    def _loop(self) -> None:
        acquisition_id, k = uuid4(), 0
        while not self._stop.is_set():
            a = 0.002 if k % 2 else -0.002
            self._bus.publish(INERTIAL_PROBE_SAMPLE_TOPIC, InertialProbeSampleAcquired(
                acquisition_id=acquisition_id, sample_index=k, timestamp_s=time.perf_counter(),
                acceleration_g=(a, 0.0, 1.0)))
            k += 1
            time.sleep(0.005)


def _step_dto(**overrides):
    params = dict(x_min=0, x_max=1, x_nb_points=2, y_min=0, y_max=1, y_nb_points=2,
                  scan_pattern="RASTER", stabilization_delay_ms=DELAY_MS,
                  averaging_per_position=1, uncertainty_volts=1e-6)
    params.update(overrides)
    return Scan2DConfigDTO(**params)


class _Stack(unittest.TestCase):
    def _service(self, motion_port, closure_topics):
        self.uow = InMemoryUnitOfWork(self.event_bus)
        ScanClosureHandler(self.event_bus, self.uow, closure_topics)
        self.stabilization = _RecordingStabilization(self.event_bus)
        self.service = ScanApplicationService(
            motion_port,
            AefiAcquisitionService(MockAefiAcquisitionExecutor(self.event_bus), MockAcquisitionPort()),
            self.event_bus,
            task_runner=ThreadPoolTaskRunner(),
            motion_sync=EventBusMotionSynchronizer(self.event_bus),
            unit_of_work=self.uow,
            column_stabilization=self.stabilization,
        )

    def _run(self, dto, timeout=30.0):
        done = threading.Event()
        self.event_bus.subscribe("scancompleted", lambda e: done.set())
        self.event_bus.subscribe("scanfailed", lambda e: done.set())
        self.assertTrue(self.service.execute_scan(dto))
        self.assertTrue(done.wait(timeout), "scan did not end")
        return self.service._current_scan

    def _stream_accelerometer(self) -> None:
        accelerometer = _StillAccelerometer(self.event_bus)
        accelerometer.start()
        self.addCleanup(accelerometer.stop)


class TestStepScanColumnStabilization(_Stack):
    def setUp(self) -> None:
        self.event_bus = InMemoryEventBus()
        self._service(MockMotionPort(event_bus=self.event_bus, motion_delay_ms=1), ("aefipointacquired",))

    def test_each_point_settles_on_the_accelerometer_when_it_streams(self) -> None:
        self._stream_accelerometer()
        scan = self._run(_step_dto())
        self.assertEqual(scan.status, ScanStatus.COMPLETED)
        self.assertEqual(len(self.stabilization.rests), 1)
        self.assertIsNotNone(self.stabilization.rests[0])
        self.assertEqual([o.method for o in self.stabilization.outcomes], [ACCELEROMETER] * 4)
        # At least one window after the stop, never less than the fixed delay.
        self.assertTrue(all(o.waited_s >= SHORT.window_s for o in self.stabilization.outcomes))

    def test_falls_back_to_the_fixed_delay_when_the_accelerometer_is_not_streaming(self) -> None:
        scan = self._run(_step_dto())
        self.assertEqual(scan.status, ScanStatus.COMPLETED)
        self.assertEqual(self.stabilization.rests, [None])
        self.assertEqual([o.method for o in self.stabilization.outcomes], [FIXED_DELAY] * 4)
        self.assertTrue(all(o.waited_s >= DELAY_MS / 1000.0 for o in self.stabilization.outcomes))

    def test_no_stabilization_at_all_when_the_delay_is_zero(self) -> None:
        self._stream_accelerometer()
        scan = self._run(_step_dto(stabilization_delay_ms=0))
        self.assertEqual(scan.status, ScanStatus.COMPLETED)
        self.assertEqual((self.stabilization.rests, self.stabilization.outcomes), ([], []))


class TestFlyScanColumnStabilization(_Stack):
    def setUp(self) -> None:
        self.event_bus = InMemoryEventBus()
        controller = FakeArcusPerformax4EXController()
        controller.connect()
        controller.home_both()
        for axis in ("x", "y"):
            controller.set_position_reference(axis, round(600.0 * 1000.0 / 21.8))
        adapter = ArcusAdapter(event_bus=self.event_bus)
        adapter.set_microns_per_pulse(21.8)
        adapter.set_controller(controller)
        adapter.enable()
        self.addCleanup(adapter.disable)
        adapter.set_speed_mode("fast")
        self._service(adapter, ("aefipointacquired", "aefilineacquired"))

    def test_each_line_start_settles_on_the_accelerometer(self) -> None:
        self._stream_accelerometer()
        scan = self._run(Scan2DConfigDTO(
            x_min=600.0, x_max=610.0, x_nb_points=2, y_min=600.0, y_max=630.0, y_nb_points=4,
            scan_pattern="SERPENTINE", scan_axis="Y", stabilization_delay_ms=DELAY_MS,
            averaging_per_position=1, uncertainty_volts=0.001, fly_scan=True,
        ))
        self.assertEqual(scan.status, ScanStatus.COMPLETED)
        self.assertEqual(len(self.stabilization.rests), 1)
        self.assertEqual([o.method for o in self.stabilization.outcomes], [ACCELEROMETER] * 2)
