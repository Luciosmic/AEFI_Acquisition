"""Suite de contrat du port IAcquisitionRepository : passée par l'adaptateur réel et par son Fake."""

import pytest


class AcquisitionRepositoryContract:
    """
    Hérité par une classe de test qui fournit :
    - `export_folder` : la chaîne du dossier d'export de la scène ;
    - `repository_holding(specs)` : un dépôt dont l'export contient une acquisition par spécification
      `(name, kind, csv_modified_at, steps_modified_at, holds_preprocessed)` (steps_modified_at None : pas de fichier d'étapes ;
      holds_preprocessed : le fichier d'étapes contient l'étape `preprocessed`).
    """

    export_folder: str

    def repository_holding(self, specs):
        raise NotImplementedError

    def test_each_acquisition_is_listed_with_its_kind_and_the_dates_of_its_files(self):
        repository = self.repository_holding([
            ("20261112_stepScan_a", "stepScan", 1000.0, 2000.0, True),
            ("20261113_flyScan_b", "flyScan", 3000.0, None, False),
        ])

        records = repository.list_acquisitions(self.export_folder)

        assert [(r.name, r.kind) for r in records] == [("20261112_stepScan_a", "stepScan"), ("20261113_flyScan_b", "flyScan")]
        assert records[0].csv_modified_at == pytest.approx(1000.0) and records[0].steps_modified_at == pytest.approx(2000.0)
        assert records[1].csv_modified_at == pytest.approx(3000.0) and records[1].steps_modified_at is None

    def test_records_name_the_scan_file_and_the_acquisition_file_of_their_folder(self):
        repository = self.repository_holding([("20261112_stepScan_a", "stepScan", 1000.0, None, False)])

        record = repository.list_acquisitions(self.export_folder)[0]

        assert record.folder.endswith("20261112_stepScan_a")
        assert record.csv_file.startswith(record.folder) and record.csv_file.endswith("_aefi.csv")
        assert record.acquisition_file.startswith(record.folder) and record.acquisition_file.endswith("20261112_stepScan_a.h5")

    def test_acquisitions_come_sorted_by_folder_name_whatever_their_kind(self):
        repository = self.repository_holding([
            ("20261114_flyScan_c", "flyScan", 1.0, None, False),
            ("20261112_stepScan_a", "stepScan", 1.0, None, False),
            ("20261113_flyScan_b", "flyScan", 1.0, None, False),
        ])

        names = [r.name for r in repository.list_acquisitions(self.export_folder)]

        assert names == ["20261112_stepScan_a", "20261113_flyScan_b", "20261114_flyScan_c"]

    def test_a_folder_that_does_not_exist_holds_no_acquisition(self):
        repository = self.repository_holding([])

        assert repository.list_acquisitions(self.export_folder + "_absent") == []

    def test_a_steps_file_is_said_to_hold_the_first_step_or_not(self):
        repository = self.repository_holding([
            ("20261112_stepScan_a", "stepScan", 1000.0, 2000.0, True),
            ("20261113_stepScan_b", "stepScan", 1000.0, 2000.0, False),
            ("20261114_stepScan_c", "stepScan", 1000.0, None, False),
        ])

        records = repository.list_acquisitions(self.export_folder)

        assert [r.steps_hold_preprocessed for r in records] == [True, False, False]
