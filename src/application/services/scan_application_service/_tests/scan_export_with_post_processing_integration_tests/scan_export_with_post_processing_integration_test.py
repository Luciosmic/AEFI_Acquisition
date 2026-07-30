"""
Integration Test: Scan -> Export (CSV+HDF5) -> Real Post-Processing (Headless)

Responsibility:
    Verify the full downstream chain with mocked hardware but REAL export
    ports and a REAL aefi_post_processor_module pipeline:
    Scan Execution -> ScanCompleted -> CSV+HDF5 written -> post-processing
    pipeline fills the HDF5 with processing steps.

    Only the visualization launch (spawns an external GUI process) is
    stubbed out, to keep this test headless.
"""
import shutil
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Any, Dict, List

import h5py

from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.thread_pool_task_runner import ThreadPoolTaskRunner
from infrastructure.execution.fake.fake_thread_pool_task_runner import FakeThreadPoolTaskRunner
from infrastructure.execution.event_bus_motion_synchronizer import EventBusMotionSynchronizer
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.mocks.adapter_mock_i_acquisition_port import MockAcquisitionPort
from infrastructure.mocks.adapter_mock_i_aefi_acquisition_executor import MockAefiAcquisitionExecutor
from infrastructure.mocks.adapter_mock_i_excitation_port import MockExcitationPort
from infrastructure.persistence.csv_scan_export_port import CsvScanExportPort
from infrastructure.persistence.hdf5_scan_export_port import Hdf5ScanExportPort
from infrastructure.post_processing.aefi_post_processor_port import AefiPostProcessorPort

from application.services.aefi_acquisition_service.aefi_acquisition_service import AefiAcquisitionService
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.scan_application_service.dtos.scan_dtos import Scan2DConfigDTO
from application.services.excitation_configuration_service.excitation_configuration_service import (
    ExcitationConfigurationService,
)
from application.services.scan_export_service.scan_export_service import ScanExportService
from application.services.scan_export_service.dtos.scan_export_dtos import ExportConfigDTO
from application.services.scan_export_service.ports.i_acquisition_snapshot_port import IAcquisitionSnapshotPort

from domain.shared_kernel.excitation.value_objects.excitation_mode import ExcitationMode


class _FakeSnapshotPort(IAcquisitionSnapshotPort):
    def read(self) -> Dict[str, Any]:
        return {}


class _RecordingPostProcessorPort(AefiPostProcessorPort):
    """Real `_process()` (real ProcessingPipeline), but `_launch_visualizer`
    is stubbed — the real one spawns an external GUI process, which would
    make this test non-headless and flaky in CI."""

    def __init__(self) -> None:
        self.launched_dirs: List[Path] = []

    def _launch_visualizer(self, acquisition_dir: Path) -> None:
        self.launched_dirs.append(acquisition_dir)


class ScanExportWithPostProcessingIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.output_dir = Path(tempfile.mkdtemp())
        self.event_bus = InMemoryEventBus()

        motion_port = MockMotionPort(event_bus=self.event_bus, motion_delay_ms=1)
        acquisition_port = MockAcquisitionPort()
        continuous_service = AefiAcquisitionService(
            MockAefiAcquisitionExecutor(self.event_bus), acquisition_port
        )
        motion_sync = EventBusMotionSynchronizer(self.event_bus)
        self.scan_service = ScanApplicationService(
            motion_port, continuous_service, self.event_bus,
            task_runner=ThreadPoolTaskRunner(),
            motion_sync=motion_sync,
        )

        excitation_service = ExcitationConfigurationService(MockExcitationPort(), self.event_bus)
        excitation_service.set_excitation(
            mode=ExcitationMode.X_DIR, level_s1_s2_percent=80.0, level_s3_s4_percent=60.0, frequency=1000.0
        )

        self.post_processing_port = _RecordingPostProcessorPort()
        self.export_service = ScanExportService(
            self.event_bus,
            csv_export_port=CsvScanExportPort(),
            hdf5_export_port=Hdf5ScanExportPort(),
            excitation_service=excitation_service,
            acquisition_snapshot_port=_FakeSnapshotPort(),
            post_processing_port=self.post_processing_port,
            # Synchronous: by the time "scancompleted" finishes propagating,
            # post-processing (real pipeline, stubbed viz launch) has run.
            task_runner=FakeThreadPoolTaskRunner(),
        )
        self.export_service.configure_export(
            ExportConfigDTO(enabled=True, output_directory=str(self.output_dir), filename_base="e2e")
        )

    def tearDown(self):
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_scan_exports_both_formats_and_real_pipeline_fills_the_hdf5(self):
        config = Scan2DConfigDTO(
            x_min=0, x_max=2, x_nb_points=3,
            y_min=0, y_max=2, y_nb_points=3,
            scan_pattern="RASTER",
            stabilization_delay_ms=0,
            averaging_per_position=1,
            uncertainty_volts=1e-6,
        )

        done = threading.Event()
        self.event_bus.subscribe("scancompleted", lambda e: done.set())

        self.assertTrue(self.scan_service.execute_scan(config))
        self.assertTrue(done.wait(timeout=30.0), "Scan + post-processing did not complete in time")

        acquisition_dirs = [p for p in self.output_dir.iterdir() if p.is_dir()]
        self.assertEqual(len(acquisition_dirs), 1)
        acquisition_dir = acquisition_dirs[0]

        csv_files = list(acquisition_dir.glob("*_aefi.csv"))
        h5_files = list(acquisition_dir.glob("*.h5"))
        self.assertEqual(len(csv_files), 1)
        self.assertEqual(len(h5_files), 1)

        with csv_files[0].open(encoding="utf-8") as f:
            self.assertEqual(sum(1 for _ in f) - 1, 9)  # header + 9 points (3x3 grid)

        with h5py.File(h5_files[0], "r") as f:
            self.assertEqual(f["scan_data/positions"].shape, (9, 2))
            # Real pipeline steps, written by the real ProcessingPipeline —
            # not just the raw export.
            for step in ("preprocessed", "phase_calibrated", "amplitude_subtracted", "rotated_frame", "interpolated"):
                self.assertIn(step, f.keys(), f"missing post-processing step '{step}' in HDF5")

        # Visualizer would have been launched on the acquisition folder
        # (stubbed here, so no real GUI process was spawned).
        self.assertEqual(self.post_processing_port.launched_dirs, [acquisition_dir])


if __name__ == "__main__":
    unittest.main()
