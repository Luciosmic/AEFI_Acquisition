from ..._tests.scan_plan_reader_contract import ScanPlanReaderContract
from ..fake_acquisition_parameters_scan_plan_reader import FakeAcquisitionParametersScanPlanReader


class TestFakeAcquisitionParametersScanPlanReader(ScanPlanReaderContract):
    def path_of(self, name):
        return f"/fake/{name}"

    def reader_describing(self, name, plan):
        reader = FakeAcquisitionParametersScanPlanReader()
        reader.add_plan(self.path_of(name), plan)
        return reader

    def reader_describing_nothing(self):
        return FakeAcquisitionParametersScanPlanReader()
