import json
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
        for path, _kind, csv_time, steps_time, holds_preprocessed in specs:
            folder = self.root / path
            folder.mkdir(parents=True)
            name = folder.name
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


def _write_parameters(folder, name, parameters):
    (folder / f"{name}_acquisition-parameters.json").write_text(json.dumps(parameters), encoding="utf-8")


class TestExportFolderRepositoryReadsTheContract:
    @pytest.fixture(autouse=True)
    def _export(self, tmp_path):
        self.root = tmp_path / "export"
        self.root.mkdir()

    def _acquisition(self, path, parameters=None):
        folder = self.root / path
        folder.mkdir(parents=True)
        (folder / f"{folder.name}_aefi.csv").write_text("x,y\n", encoding="utf-8")
        if parameters is not None:
            _write_parameters(folder, folder.name, parameters)
        return folder

    def _listed(self):
        return {r.name: r for r in ExportFolderRepository().list_acquisitions(str(self.root))}

    def test_date_object_and_lift_off_come_from_the_parameters_file_not_from_the_folder_name(self):
        self._acquisition("METALLIC/2026-11-12_205659_stepScan_nom_trompeur_liftoff-99mm", {
            "schema": {"version": "1.4"},
            "provenance": {"activity": {"kind": "step_scan", "started_at": "2026-11-12T20:57:00.050+01:00"}},
            "feature_of_interest": {"description": "cylindre_base_hexagonale_metallique",
                                    "d": {"value": 15.0, "unit": "mm", "alias": "lift_off"}},
        })

        record = self._listed()["2026-11-12_205659_stepScan_nom_trompeur_liftoff-99mm"]

        assert (record.group, record.kind, record.measured_object, record.lift_off_mm) == (
            "METALLIC", "stepScan", "cylindre_base_hexagonale_metallique", 15.0)
        assert record.acquired_at.isoformat() == "2026-11-12T20:57:00.050000+01:00"

    def test_a_fly_scan_is_recognised_by_its_activity_whatever_its_folder_name(self):
        self._acquisition("2026-11-14_100000_stepScan_x", {
            "schema": {"version": "1.4"}, "provenance": {"activity": {"kind": "fly_scan"}}})

        assert self._listed()["2026-11-14_100000_stepScan_x"].kind == "flyScan"

    def test_before_schema_1_4_or_without_parameters_the_kind_falls_back_on_the_folder_name(self):
        self._acquisition("2026-11-12_194400_flyScan_old", {
            "schema": {"version": "1.2"}, "provenance": {"activity": {"kind": "step_scan"}}})
        self._acquisition("WATER/2026-07-29_175721_stepScan_older")

        listed = self._listed()

        assert listed["2026-11-12_194400_flyScan_old"].kind == "flyScan"
        assert listed["2026-07-29_175721_stepScan_older"].kind == "stepScan"
        assert listed["2026-07-29_175721_stepScan_older"].measured_object is None

    def test_a_time_series_or_a_folder_the_contract_and_the_name_do_not_call_a_scan_is_not_listed(self):
        self._acquisition("2026-11-14_110000_timeSeries_plaque", {
            "schema": {"version": "1.4"}, "provenance": {"activity": {"kind": "time_series"}}})
        self._acquisition("BACKGROUND/sans_type_reconnu")

        assert self._listed() == {}

    def test_an_unreadable_parameters_file_leaves_the_acquisition_listed_with_unknown_details(self):
        folder = self._acquisition("2026-11-14_120000_stepScan_y")
        (folder / "2026-11-14_120000_stepScan_y_acquisition-parameters.json").write_text("{pas du json", encoding="utf-8")

        record = self._listed()["2026-11-14_120000_stepScan_y"]

        assert (record.kind, record.measured_object, record.acquired_at) == ("stepScan", None, None)

    def test_the_rotation_the_acquisition_applied_and_the_schema_come_from_its_parameters_file(self):
        self._acquisition("WATER/2026-11-13_103000_stepScan_bouteille", {
            "schema": {"version": "1.4"}, "provenance": {"activity": {"kind": "step_scan"}},
            "measurement_chain": {"sensor": {"deployment": {"rotation_applied": {
                "theta_x": {"value": 34.9, "unit": "deg"}, "theta_y": {"value": 45.7, "unit": "deg"},
                "theta_z": {"value": -5.3, "unit": "deg"},
                "convention": {"type": "extrinsic", "order": "ZYX", "direction": "sources_to_sensor"},
                "origin": "calibrated", "calibration_id": "cal-1", "applies_to_data": False}}}},
        })

        record = self._listed()["2026-11-13_103000_stepScan_bouteille"]

        assert record.applied_rotation.angles == (34.9, 45.7, -5.3) and record.applied_rotation.origin == "calibrated"
        assert record.rotation_problem is None and record.schema_version == "1.4"

    def test_a_rotation_that_cannot_be_used_is_kept_with_its_reason_and_logged(self, caplog):
        self._acquisition("2026-11-13_104000_stepScan_refusee", {
            "schema": {"version": "1.4"}, "provenance": {"activity": {"kind": "step_scan"}},
            "measurement_chain": {"sensor": {"deployment": {"rotation_applied": {
                "theta_x": {"value": 1.0, "unit": "deg"}, "theta_y": {"value": 2.0, "unit": "deg"},
                "theta_z": {"value": 3.0, "unit": "deg"},
                "convention": {"type": "intrinsic", "order": "ZYX", "direction": "sources_to_sensor"}}}}},
        })

        with caplog.at_level("WARNING"):
            record = self._listed()["2026-11-13_104000_stepScan_refusee"]

        assert record.applied_rotation is None and "intrinsic" in record.rotation_problem
        assert any("catalog.rotation_refused" in m and "2026-11-13_104000_stepScan_refusee" in m for m in caplog.messages)

    def test_without_parameters_the_acquisition_says_nothing_of_its_rotation(self):
        self._acquisition("2026-07-29_175721_stepScan_ancienne")

        record = self._listed()["2026-07-29_175721_stepScan_ancienne"]

        assert (record.applied_rotation, record.rotation_problem, record.schema_version) == (None, None, None)
