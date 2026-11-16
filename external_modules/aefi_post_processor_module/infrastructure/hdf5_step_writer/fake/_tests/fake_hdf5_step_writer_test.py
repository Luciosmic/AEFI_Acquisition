from ....hdf5_step_writer._tests.hdf5_step_writer_contract import StepWriterContract
from ..fake_hdf5_step_writer import FakeHdf5StepWriter


class TestFakeHdf5StepWriter(StepWriterContract):
    def make_writer(self):
        return FakeHdf5StepWriter()
