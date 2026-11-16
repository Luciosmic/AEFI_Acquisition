import numpy as np
import pytest

from ....domain.processing._tests.synthetic_scan_generator import SyntheticScanGenerator
from ....domain.processing.processing_steps.processing_steps import STEP_NAMES, ProcessingParameters
from ....infrastructure.csv_scan_reader.fake.fake_csv_scan_reader import FakeCsvScanReader
from ....infrastructure.hdf5_step_writer.fake.fake_hdf5_step_writer import FakeHdf5StepWriter
from ..dtos.process_scan_dto import ProcessScanDTO
from ..dtos.scan_samples_dto import ScanSamplesDTO
from ..post_processing_service import PostProcessingService

CSV = "/scans/a/a_aefi.csv"
STORE = "/scans/a/a.h5"


def _samples():
    generator = SyntheticScanGenerator(grid_size=12, scan_range=10.0)
    data = generator.add_phase_offset(generator.generate_base_signal(), (0.3, -0.2, 0.5))
    channels = ('voltage_x_in_phase', 'voltage_x_quadrature', 'voltage_y_in_phase',
                'voltage_y_quadrature', 'voltage_z_in_phase', 'voltage_z_quadrature')
    return ScanSamplesDTO(
        x=generator.X.ravel(), y=generator.Y.ravel(), values=data.reshape(-1, 6), channel_names=channels
    )


@pytest.fixture
def parts():
    reader, writer = FakeCsvScanReader(), FakeHdf5StepWriter()
    reader.add_file(CSV, _samples())
    return PostProcessingService(reader, writer), writer


def test_a_scan_with_angles_gives_the_five_steps_in_order(parts):
    service, writer = parts
    request = ProcessScanDTO(CSV, STORE, ProcessingParameters(rotation_angles=(0.0, 0.0, 45.0)))

    summary = service.process_scan(request)

    assert summary.steps_completed == ('load_csv', 'preprocess', 'phase_calibration', 'amplitude_subtraction',
                                       'frame_rotation', 'interpolation')
    assert [e.split(' @ ')[0] for e in summary.processing_history] == list(STEP_NAMES)
    assert summary.success is True and summary.errors == () and summary.output_file == STORE
    assert writer.source_csv == CSV


def test_each_step_is_stored_with_the_shape_its_calculation_gives(parts):
    service, writer = parts

    service.process_scan(ProcessScanDTO(CSV, STORE, ProcessingParameters(rotation_angles=(10.0, 0.0, 0.0))))

    assert writer.load_step('preprocessed')[0].shape == (12, 12, 6)
    assert writer.load_step('rotated_frame')[0].shape == (12, 12, 6)
    assert writer.load_step('interpolated')[0].shape[:2] == (200, 200)
    assert np.allclose(writer.load_step('preprocessed')[1]['extent'][:2], [-5.4545, 5.4545], atol=1e-3)


def test_without_angles_no_rotated_frame_is_stored_and_the_other_steps_still_are(parts):
    service, writer = parts

    summary = service.process_scan(ProcessScanDTO(CSV, STORE))

    assert 'frame_rotation' not in summary.steps_completed
    with pytest.raises(KeyError):
        writer.load_step('rotated_frame')
    assert writer.load_step('interpolated')[0].shape[:2] == (200, 200)


def test_interpolation_can_be_skipped(parts):
    service, writer = parts

    summary = service.process_scan(ProcessScanDTO(CSV, STORE, skip_interpolation=True))

    assert 'interpolation' not in summary.steps_completed
    with pytest.raises(KeyError):
        writer.load_step('interpolated')


def test_a_missing_scan_file_stops_before_anything_is_stored(parts):
    service, writer = parts

    with pytest.raises(FileNotFoundError):
        service.process_scan(ProcessScanDTO("/scans/absent.csv", STORE))

    assert writer.processing_history() == []


def test_a_failure_names_the_step_it_happened_in_without_changing_the_exception(parts):
    service, _writer = parts

    with pytest.raises(FileNotFoundError) as failure:
        service.process_scan(ProcessScanDTO("/scans/absent.csv", STORE))

    assert failure.value.processing_step == "load_csv"
