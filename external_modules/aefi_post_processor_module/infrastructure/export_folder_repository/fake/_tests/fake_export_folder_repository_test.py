from .....domain.acquisition_record.acquisition_record import AcquisitionRecord
from ....export_folder_repository._tests.export_folder_repository_contract import AcquisitionRepositoryContract
from ..fake_export_folder_repository import FakeExportFolderRepository


class TestFakeExportFolderRepository(AcquisitionRepositoryContract):
    export_folder = "/fake/export"

    def repository_holding(self, specs):
        repository = FakeExportFolderRepository()
        for name, kind, csv_time, steps_time, holds_preprocessed in specs:
            folder = f"{self.export_folder}/{name}"
            repository.add(self.export_folder, AcquisitionRecord(
                name=name, kind=kind, folder=folder, csv_file=f"{folder}/{name}_aefi.csv",
                acquisition_file=f"{folder}/{name}.h5", csv_modified_at=csv_time, steps_modified_at=steps_time,
                steps_hold_preprocessed=holds_preprocessed,
            ))
        return repository
