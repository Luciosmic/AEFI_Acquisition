import numpy as np
import pytest

from ....domain.processing._tests.synthetic_scan_generator import SyntheticScanGenerator
from ....domain.processing.processing_steps.processing_steps import STEP_NAMES, ProcessingParameters
from ....domain.processing.planned_scan_grid.planned_scan_grid import PlannedAxis, PlannedScanGrid
from ....infrastructure.acquisition_parameters_scan_plan_reader.fake.fake_acquisition_parameters_scan_plan_reader import (
    FakeAcquisitionParametersScanPlanReader,
)
from ....infrastructure.acquisition_provenance_reader.fake.fake_acquisition_provenance_reader import (
    FakeAcquisitionProvenanceReader,
)
from ....infrastructure.csv_scan_reader.fake.fake_csv_scan_reader import FakeCsvScanReader
from ....infrastructure.hdf5_step_writer.fake.fake_hdf5_step_writer import FakeHdf5StepWriter
from ..dtos.acquisition_provenance_dto import AcquisitionProvenanceDTO
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
    assert writer.source.csv_path == CSV


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


def _rectangular_samples():
    """A complete scan of 6 columns (x from 0 to 10) and 3 rows (y from 0 to 4), every channel at 1."""
    xs, ys = np.linspace(0.0, 10.0, 6), np.linspace(0.0, 4.0, 3)
    x, y = np.meshgrid(xs, ys)
    channels = ('voltage_x_in_phase', 'voltage_x_quadrature', 'voltage_y_in_phase',
                'voltage_y_quadrature', 'voltage_z_in_phase', 'voltage_z_quadrature')
    return ScanSamplesDTO(x=x.ravel(), y=y.ravel(), values=np.ones((18, 6)), channel_names=channels)


def _service_with_plan(plan):
    reader, writer, plans = FakeCsvScanReader(), FakeHdf5StepWriter(), FakeAcquisitionParametersScanPlanReader()
    reader.add_file(CSV, _rectangular_samples())
    if plan is not None:
        plans.add_plan(CSV, plan)
    return PostProcessingService(reader, writer, plans), writer


def test_a_rectangular_scan_described_by_its_acquisition_keeps_its_shape_and_extent():
    plan = PlannedScanGrid(x=PlannedAxis(0.0, 10.0, 6), y=PlannedAxis(0.0, 4.0, 3))
    service, writer = _service_with_plan(plan)

    service.process_scan(ProcessScanDTO(CSV, STORE, skip_interpolation=True))

    grid, metadata = writer.load_step('preprocessed')
    assert grid.shape == (3, 6, 6) and not np.isnan(grid).any()
    assert metadata['extent'] == [-1.0, 11.0, -1.0, 5.0]
    assert metadata['grid_origin'] == 'planned'


def test_a_scan_without_description_keeps_the_square_grid():
    service, writer = _service_with_plan(None)

    service.process_scan(ProcessScanDTO(CSV, STORE, skip_interpolation=True))

    grid, metadata = writer.load_step('preprocessed')
    assert grid.shape == (6, 6, 6) and np.isnan(grid[3:, :, :]).all()
    assert 'grid_origin' not in metadata


# -- les angles que l'acquisition a appliqués passent avant les angles demandés ----------------------------------

APPLIED = (34.9, 45.7, -5.3)
IDEAL = (35.3, 45.0, 0.0)


def _steps(request, caplog=None):
    reader, writer = FakeCsvScanReader(), FakeHdf5StepWriter()
    reader.add_file(CSV, _samples())
    summary = PostProcessingService(reader, writer).process_scan(request)
    return writer, summary


def test_the_angles_the_acquisition_applied_replace_the_requested_ones():
    applied, _ = _steps(ProcessScanDTO(CSV, STORE, ProcessingParameters(rotation_angles=IDEAL), applied_rotation_angles=APPLIED))
    direct, _ = _steps(ProcessScanDTO(CSV, STORE, ProcessingParameters(rotation_angles=APPLIED)))
    ideal, _ = _steps(ProcessScanDTO(CSV, STORE, ProcessingParameters(rotation_angles=IDEAL)))

    assert applied.load_step('rotated_frame')[1]['rotation_angles'] == APPLIED
    assert applied.load_step('interpolated')[1]['rotation_angles'] == APPLIED
    for name in ('rotated_frame', 'interpolated'):
        assert np.array_equal(applied.load_step(name)[0], direct.load_step(name)[0], equal_nan=True)
    assert not np.array_equal(applied.load_step('rotated_frame')[0], ideal.load_step('rotated_frame')[0], equal_nan=True)


def test_without_applied_angles_the_requested_ones_are_used_as_before():
    plain, _ = _steps(ProcessScanDTO(CSV, STORE, ProcessingParameters(rotation_angles=IDEAL)))
    none, _ = _steps(ProcessScanDTO(CSV, STORE, ProcessingParameters(rotation_angles=IDEAL), applied_rotation_angles=None))

    assert plain.load_step('rotated_frame')[1]['rotation_angles'] == IDEAL
    assert np.array_equal(plain.load_step('rotated_frame')[0], none.load_step('rotated_frame')[0], equal_nan=True)


def test_applied_angles_rotate_the_frame_even_when_none_were_requested():
    writer, summary = _steps(ProcessScanDTO(CSV, STORE, applied_rotation_angles=APPLIED))

    assert 'frame_rotation' in summary.steps_completed
    assert writer.load_step('rotated_frame')[1]['rotation_angles'] == APPLIED


def test_the_journal_says_where_the_angles_come_from(caplog):
    import logging

    with caplog.at_level(logging.INFO):
        _steps(ProcessScanDTO(CSV, STORE, ProcessingParameters(rotation_angles=IDEAL), applied_rotation_angles=APPLIED))
        _steps(ProcessScanDTO(CSV, STORE, ProcessingParameters(rotation_angles=IDEAL)))
        _steps(ProcessScanDTO(CSV, STORE))

    sources = [r.getMessage() for r in caplog.records if r.getMessage().startswith("pipeline.rotation_source")]
    assert [s.split(" source=")[1].split(" ")[0] for s in sources] == ["acquisition_parameters", "request", "none"]
    assert "angles_deg=(34.9, 45.7, -5.3)" in sources[0]


# -- la source du traitement : empreinte du CSV relu, activité et empreinte déclarées par l'acquisition ---------------

SHA = "ab" * 32


def _service_with_provenance(provenance, sha256=SHA):
    reader, writer, provenances = FakeCsvScanReader(), FakeHdf5StepWriter(), FakeAcquisitionProvenanceReader()
    samples = _samples()
    reader.add_file(CSV, ScanSamplesDTO(samples.x, samples.y, samples.values, samples.channel_names, sha256=sha256))
    if provenance is not None:
        provenances.add_provenance(CSV, provenance)
    service = PostProcessingService(reader, writer, acquisition_provenance_reader=provenances)
    return service, writer


def test_the_source_records_the_hash_of_the_csv_read_and_the_activity_of_its_acquisition():
    service, writer = _service_with_provenance(AcquisitionProvenanceDTO("act-7", declared_csv_sha256=SHA))

    service.process_scan(ProcessScanDTO(CSV, STORE, skip_interpolation=True))

    assert (writer.source.csv_path, writer.source.sha256) == (CSV, SHA)
    assert (writer.source.activity_id, writer.source.declared_sha256) == ("act-7", SHA)


def test_the_raw_points_re_read_from_the_csv_are_stored_before_the_steps():
    service, writer = _service_with_provenance(None)

    service.process_scan(ProcessScanDTO(CSV, STORE, skip_interpolation=True))

    assert writer.raw_scan.values.shape == (144, 6) and writer.raw_scan.sha256 == SHA


def test_a_csv_changed_since_the_acquisition_closed_is_still_processed_and_the_mismatch_is_logged(caplog):
    service, writer = _service_with_provenance(AcquisitionProvenanceDTO("act-7", declared_csv_sha256="cd" * 32))

    with caplog.at_level("WARNING"):
        summary = service.process_scan(ProcessScanDTO(CSV, STORE, skip_interpolation=True))

    assert summary.success is True
    assert (writer.source.sha256, writer.source.declared_sha256) == (SHA, "cd" * 32)
    assert any("pipeline.source_changed" in r.message for r in caplog.records)


def test_a_scan_without_description_records_its_hash_alone():
    service, writer = _service_with_provenance(None)

    service.process_scan(ProcessScanDTO(CSV, STORE, skip_interpolation=True))

    assert (writer.source.sha256, writer.source.activity_id, writer.source.declared_sha256) == (SHA, None, None)


def test_a_file_that_makes_no_grid_leaves_no_raw_points_behind():
    reader, writer = FakeCsvScanReader(), FakeHdf5StepWriter()
    reader.add_file(CSV, ScanSamplesDTO(x=np.zeros(0), y=np.zeros(0), values=np.zeros((0, 0)), channel_names=()))

    with pytest.raises(ValueError):
        PostProcessingService(reader, writer).process_scan(ProcessScanDTO(CSV, STORE))

    assert writer.raw_scan is None
