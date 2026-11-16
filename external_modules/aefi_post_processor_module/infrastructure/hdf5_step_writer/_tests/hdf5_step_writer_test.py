import h5py
import numpy as np
import pytest

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
        writer.record_source("/scans/a_aefi.csv")
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
