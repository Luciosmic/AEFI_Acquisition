import os

import h5py
import pytest

from ..export_folder_repository import ExportFolderRepository
from .export_folder_repository_contract import AcquisitionRepositoryContract


class TestExportFolderRepository(AcquisitionRepositoryContract):
    @pytest.fixture(autouse=True)
    def _export(self, tmp_path):
        self.root = tmp_path / "export"
        self.root.mkdir()
        self.export_folder = str(self.root)

    def repository_holding(self, specs):
        for name, _kind, csv_time, steps_time, holds_preprocessed in specs:
            folder = self.root / name
            folder.mkdir()
            csv = folder / f"{name}_aefi.csv"
            csv.write_text("x,y\n", encoding="utf-8")
            os.utime(csv, (csv_time, csv_time))
            if steps_time is not None:
                steps = folder / f"{name}.h5"
                with h5py.File(steps, "w") as h5:
                    if holds_preprocessed:
                        h5.create_group("preprocessed")
                os.utime(steps, (steps_time, steps_time))
        return ExportFolderRepository()

    def test_a_folder_without_scan_file_or_of_another_kind_is_not_an_acquisition(self):
        (self.root / "20261112_stepScan_empty").mkdir()
        (self.root / "20261112_somethingElse_x").mkdir()
        (self.root / "20261112_somethingElse_x" / "x_aefi.csv").write_text("x,y\n", encoding="utf-8")

        assert ExportFolderRepository().list_acquisitions(self.export_folder) == []

    def test_listing_creates_and_modifies_nothing(self):
        repository = self.repository_holding([("20261112_stepScan_a", "stepScan", 1000.0, 2000.0, True)])
        before = sorted((str(p), p.stat().st_mtime) for p in self.root.rglob("*"))

        repository.list_acquisitions(self.export_folder)

        assert sorted((str(p), p.stat().st_mtime) for p in self.root.rglob("*")) == before

    def test_a_steps_file_that_is_not_a_readable_hdf5_holds_no_first_step(self):
        repository = self.repository_holding([("20261112_stepScan_a", "stepScan", 1000.0, None, False)])
        (self.root / "20261112_stepScan_a" / "20261112_stepScan_a.h5").write_text("not hdf5", encoding="utf-8")

        record = repository.list_acquisitions(self.export_folder)[0]

        assert record.steps_modified_at is not None and record.steps_hold_preprocessed is False
