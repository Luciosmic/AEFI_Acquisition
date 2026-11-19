"""
AefiPostProcessorPort — rotation angles follow the active sensor rotation.

The real pipeline is never run here: `ProcessingPipeline` is patched with a
fake that records the `run_full_pipeline` kwargs.
"""
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from application.test_bench_calibration.sensor_calibration_service.sensor_calibration_service import (
    ACTIVE_SENSOR_ROTATION_CHANGED_TOPIC,
)
from domain.test_bench_calibration.events.active_sensor_rotation_changed.active_sensor_rotation_changed import (
    ActiveSensorRotationChanged,
)
from domain.test_bench_calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import (
    SensorRotationAngles,
)
from infrastructure.in_memory_event_bus.in_memory_event_bus import InMemoryEventBus
from infrastructure.aefi_post_processor_port.aefi_post_processor_port import (
    AefiPostProcessorPort,
    rotation_origin,
)


def _make_port(event_bus):
    return AefiPostProcessorPort(
        event_bus, initial_rotation_angles=(35.3, 45.0, 0.0), initial_rotation_origin="ideal default"
    )


def test_port_follows_active_sensor_rotation_changed():
    event_bus = InMemoryEventBus()
    port = _make_port(event_bus)

    event_bus.publish(
        ACTIVE_SENSOR_ROTATION_CHANGED_TOPIC,
        ActiveSensorRotationChanged(
            angles=SensorRotationAngles(theta_x_degrees=36.0, theta_y_degrees=44.0, theta_z_degrees=1.0),
            is_calibrated=False,
            recorded_at=None,
            is_trial=True,
        ),
    )

    assert port._rotation_angles == (36.0, 44.0, 1.0)
    assert port._rotation_origin == "trial"


def test_rotation_origin_trial_wins():
    assert rotation_origin(True, True, datetime(2026, 1, 1)) == "trial"


def test_rotation_origin_calibrated_includes_recorded_at():
    recorded_at = datetime(2026, 9, 25, 10, 30)
    assert rotation_origin(False, True, recorded_at) == "calibrated " + recorded_at.isoformat()


def test_rotation_origin_ideal_default():
    assert rotation_origin(False, False, None) == "ideal default"


class _FakePipeline:
    calls = []
    outputs = []

    def __init__(self, output_path):
        self.output_path = output_path
        _FakePipeline.outputs.append(output_path)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def run_full_pipeline(self, csv_path, **kwargs):
        _FakePipeline.calls.append(kwargs)


def test_process_passes_the_active_angles_to_the_pipeline():
    port = _make_port(InMemoryEventBus())
    _FakePipeline.calls = []

    with patch(
        "aefi_post_processor_module.processing.processing_pipeline.ProcessingPipeline", _FakePipeline
    ):
        port._process(Path("scan_aefi.csv"), Path("scan.h5"))

    assert len(_FakePipeline.calls) == 1
    assert _FakePipeline.calls[0]["rotation_angles"] == (35.3, 45.0, 0.0)


def test_run_creates_the_h5_next_to_the_csv_under_the_name_of_the_acquisition_folder():
    """The acquisition exports the CSV only: the `.h5` is the post-processing's, at the path the catalog looks it up."""
    port = _make_port(InMemoryEventBus())
    launched = []
    port._launch_visualizer = launched.append
    _FakePipeline.calls, _FakePipeline.outputs = [], []
    folder = Path("exports/2026-11-19_101500_stepScan_plaque")

    with patch(
        "aefi_post_processor_module.processing.processing_pipeline.ProcessingPipeline", _FakePipeline
    ):
        port.run(folder / "2026-11-19_101500_stepScan_plaque_aefi.csv")

    assert _FakePipeline.outputs == [folder / "2026-11-19_101500_stepScan_plaque.h5"]
    assert launched == [folder]


def test_a_failed_post_processing_does_not_open_the_visualizer():
    port = _make_port(InMemoryEventBus())
    launched = []
    port._launch_visualizer = launched.append

    class _Failing(_FakePipeline):
        def run_full_pipeline(self, csv_path, **kwargs):
            raise RuntimeError("boom")

    with patch("aefi_post_processor_module.processing.processing_pipeline.ProcessingPipeline", _Failing):
        port.run(Path("exports/a/a_aefi.csv"))

    assert launched == []
