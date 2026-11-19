from ..._tests.acquisition_provenance_reader_contract import AcquisitionProvenanceReaderContract
from ..fake_acquisition_provenance_reader import FakeAcquisitionProvenanceReader


class TestFakeAcquisitionProvenanceReader(AcquisitionProvenanceReaderContract):
    def path_of(self, name):
        return f"/fake/{name}"

    def reader_describing(self, name, provenance):
        reader = FakeAcquisitionProvenanceReader()
        reader.add_provenance(self.path_of(name), provenance)
        return reader

    def reader_describing_nothing(self):
        return FakeAcquisitionProvenanceReader()
