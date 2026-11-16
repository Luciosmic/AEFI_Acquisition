import numpy as np
import pytest

from ...hdf5_step_writer.hdf5_step_writer import Hdf5StepWriter
from ..hdf5_step_reader import Hdf5StepReader
from .hdf5_step_reader_contract import StepReaderContract


class TestHdf5StepReader(StepReaderContract):
    @pytest.fixture(autouse=True)
    def _folder(self, tmp_path):
        self.acquisition_file = str(tmp_path / "acquisition.h5")

    def reader_holding(self, steps):
        if steps:
            writer = Hdf5StepWriter(self.acquisition_file)
            for name, (data, metadata) in steps.items():
                writer.save_step(name, data, metadata)
            writer.close()
        return Hdf5StepReader()

    def test_what_the_step_writer_stored_is_read_back_with_its_decoded_metadata_forms(self):
        reader = self.reader_holding({'preprocessed': (np.zeros((2, 2, 2)),
                                                       {'extent': [0.0, 1.0, 2.0, 3.0], 'channel_names': ['a', 'b']})})

        metadata = reader.read_step(self.acquisition_file, 'preprocessed').metadata

        assert list(metadata['extent']) == [0.0, 1.0, 2.0, 3.0]
        assert metadata['channel_names'] == '["a", "b"]'
