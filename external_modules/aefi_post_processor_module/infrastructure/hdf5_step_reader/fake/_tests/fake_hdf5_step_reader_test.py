from ....hdf5_step_reader._tests.hdf5_step_reader_contract import StepReaderContract
from ..fake_hdf5_step_reader import FakeHdf5StepReader


class TestFakeHdf5StepReader(StepReaderContract):
    acquisition_file = "/fake/acquisition.h5"

    def reader_holding(self, steps):
        reader = FakeHdf5StepReader()
        for name, (data, metadata) in steps.items():
            reader.add_step(self.acquisition_file, name, data, metadata)
        return reader
