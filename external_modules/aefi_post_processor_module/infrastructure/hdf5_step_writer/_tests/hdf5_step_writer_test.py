import json

import h5py
import numpy as np
import pytest

from ....application.post_processing_service.dtos.scan_samples_dto import ScanSamplesDTO
from ....application.post_processing_service.dtos.source_record_dto import SourceRecordDTO
from ..hdf5_step_writer import Hdf5StepWriter
from .hdf5_step_writer_contract import StepWriterContract


class TestHdf5StepWriter(StepWriterContract):
    @pytest.fixture(autouse=True)
    def _folder(self, tmp_path):
        self.folder = tmp_path

    def make_writer(self):
        return Hdf5StepWriter(str(self.folder / "acquisition.h5"))

    def test_the_source_scan_and_the_history_are_attributes_of_the_file(self):
        path = str(self.folder / "acquisition.h5")
        writer = Hdf5StepWriter(path)
        writer.record_source(SourceRecordDTO("/scans/a_aefi.csv", sha256="aa" * 32))
        writer.save_step('preprocessed', np.zeros((1, 1, 1)), {})
        writer.close()

        with h5py.File(path, "r") as h5:
            assert h5.attrs["source_csv"] == "/scans/a_aefi.csv"
            assert "load_timestamp" in h5.attrs and list(h5["preprocessed"].keys()) == ["data"]

    def test_the_history_of_a_file_is_kept_when_it_is_opened_again(self):
        path = str(self.folder / "acquisition.h5")
        first = Hdf5StepWriter(path)
        first.save_step('preprocessed', np.zeros((1, 1, 1)), {})
        first.close()

        second = Hdf5StepWriter(path)
        second.save_step('phase_calibrated', np.zeros((1, 1, 1)), {})

        assert [e.split(' @ ')[0] for e in second.processing_history()] == ['preprocessed', 'phase_calibrated']

    def test_writing_after_close_is_refused(self):
        writer = self.make_writer()
        writer.close()

        with pytest.raises(RuntimeError):
            writer.save_step('preprocessed', np.zeros((1, 1, 1)), {})

    def test_the_hash_the_activity_and_the_match_of_the_source_are_attributes_of_the_file(self):
        path = str(self.folder / "acquisition.h5")
        writer = Hdf5StepWriter(path)
        writer.record_source(SourceRecordDTO("/scans/a_aefi.csv", sha256="aa" * 32, activity_id="act-1", declared_sha256="aa" * 32))
        writer.close()

        with h5py.File(path, "r") as h5:
            assert h5.attrs["source_sha256"] == "aa" * 32
            assert h5.attrs["source_activity_id"] == "act-1"
            assert h5.attrs["source_declared_sha256"] == "aa" * 32
            assert bool(h5.attrs["source_sha256_matches"]) is True

    def test_a_source_the_acquisition_hashed_differently_is_recorded_as_not_matching(self):
        path = str(self.folder / "acquisition.h5")
        writer = Hdf5StepWriter(path)
        writer.record_source(SourceRecordDTO("/scans/a_aefi.csv", sha256="aa" * 32, declared_sha256="bb" * 32))
        writer.close()

        with h5py.File(path, "r") as h5:
            assert bool(h5.attrs["source_sha256_matches"]) is False

    def test_a_source_without_description_records_its_hash_and_nothing_about_the_acquisition(self):
        path = str(self.folder / "acquisition.h5")
        writer = Hdf5StepWriter(path)
        writer.record_source(SourceRecordDTO("/scans/a_aefi.csv", sha256="aa" * 32))
        writer.close()

        with h5py.File(path, "r") as h5:
            assert h5.attrs["source_sha256"] == "aa" * 32
            assert not {"source_activity_id", "source_declared_sha256", "source_sha256_matches"} & set(h5.attrs)

    def test_the_raw_points_re_read_from_the_csv_are_stored_beside_the_steps(self):
        path = str(self.folder / "acquisition.h5")
        samples = ScanSamplesDTO(
            x=np.array([0.0, 1.0]), y=np.array([2.0, 3.0]),
            values=np.array([[1.0, 2.0], [3.0, 4.0]]), channel_names=('voltage_x_in_phase', 'voltage_x_quadrature'),
        )
        writer = Hdf5StepWriter(path)
        writer.save_raw_scan(samples)
        writer.close()

        with h5py.File(path, "r") as h5:
            group = h5["raw_scan"]
            assert np.array_equal(group["positions"][...], [[0.0, 2.0], [1.0, 3.0]])
            assert np.array_equal(group["values"][...], samples.values)
            assert json.loads(group.attrs["channel_names"]) == ['voltage_x_in_phase', 'voltage_x_quadrature']

    def test_a_file_the_acquisition_did_not_create_is_created_by_the_writer(self):
        path = self.folder / "new_acquisition.h5"

        Hdf5StepWriter(str(path)).close()

        assert path.exists()
