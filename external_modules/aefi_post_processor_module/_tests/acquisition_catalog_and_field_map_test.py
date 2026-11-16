"""Catalogue et carte avec les adaptateurs réels sur un dossier d'export synthétique (test d'acceptation de 1.5)."""

import os
import shutil
import time
from pathlib import Path

import numpy as np
import pytest

from aefi_post_processor_module.application.acquisition_catalog_service.dtos.acquisition_outcome_dto import AcquisitionOutcomeDTO
from aefi_post_processor_module.application.acquisition_catalog_service.dtos.acquisition_status_dto import FAILED, PROCESSED, TO_RECOMPUTE
from aefi_post_processor_module.application.acquisition_catalog_service.dtos.list_acquisitions_dto import ListAcquisitionsDTO
from aefi_post_processor_module.application.field_map_service.dtos.load_step_dto import LoadStepDTO
from aefi_post_processor_module.application.field_map_service.dtos.steps_request_dto import StepsRequestDTO
from aefi_post_processor_module.application.post_processing_service.dtos.process_scan_dto import ProcessScanDTO
from aefi_post_processor_module.domain.processing.processing_steps.processing_steps import STEP_NAMES, ProcessingParameters
from aefi_post_processor_module.interface.shell.headless_wiring import (
    build_acquisition_catalog_service,
    build_field_map_service,
    build_post_processing_service,
)
from aefi_post_processor_module.visualisation.model import VisualisationModel

BATCH = Path(__file__).resolve().parent / "synthetic_scans_data_repository" / "batch_20260123_201635"
BASELINE, ROTATED, TRUNCATED = "20261112_stepScan_baseline", "20261113_stepScan_rotated", "20261114_flyScan_truncated"


@pytest.fixture
def export(tmp_path):
    root = tmp_path / "export"
    old = time.time() - 1000
    for name, source in ((BASELINE, "scan_001_baseline"), (ROTATED, "scan_004_rotation_z45")):
        folder = root / name
        folder.mkdir(parents=True)
        shutil.copy(BATCH / f"{source}.csv", folder / f"{name}_aefi.csv")
        os.utime(folder / f"{name}_aefi.csv", (old, old))
    truncated = root / TRUNCATED
    truncated.mkdir()
    csv = truncated / f"{TRUNCATED}_aefi.csv"
    csv.write_text("x,y,voltage_x_i", encoding="utf-8")  # cut inside the header
    os.utime(csv, (old, old))
    return root


def _files_with_dates(root):
    return sorted((str(p), p.stat().st_mtime) for p in root.rglob("*"))


def _by_name(catalog, root, force=False):
    return {s.name: s for s in catalog.list_acquisitions(ListAcquisitionsDTO(str(root), force))}


def _process(root, name, angles=(0.0, 0.0, 45.0)):
    acquisition = str(root / name / f"{name}.h5")
    service, writer = build_post_processing_service(acquisition)
    try:
        return service.process_scan(ProcessScanDTO(
            str(root / name / f"{name}_aefi.csv"), acquisition, ProcessingParameters(rotation_angles=angles)
        ))
    finally:
        writer.close()


def test_the_catalog_follows_an_acquisition_from_to_recompute_to_processed_back_to_stale_and_failed(export):
    catalog = build_acquisition_catalog_service()

    first = _by_name(catalog, export)
    assert {n: (s.state, s.reason) for n, s in first.items()} == {
        BASELINE: (TO_RECOMPUTE, "new"), ROTATED: (TO_RECOMPUTE, "new"), TRUNCATED: (TO_RECOMPUTE, "new"),
    }

    _process(export, BASELINE)
    assert _by_name(catalog, export)[BASELINE].state == PROCESSED

    csv = export / BASELINE / f"{BASELINE}_aefi.csv"
    later = time.time() + 100
    os.utime(csv, (later, later))
    stale = _by_name(catalog, export)[BASELINE]
    assert (stale.state, stale.reason) == (TO_RECOMPUTE, "source_newer")

    with pytest.raises(ValueError) as failure:
        _process(export, TRUNCATED)
    catalog.report_outcome(AcquisitionOutcomeDTO(TRUNCATED, False, str(failure.value)))
    failed = _by_name(catalog, export)[TRUNCATED]
    assert failed.state == FAILED and "No voltage columns found" in failed.failure_message


def test_listing_the_catalog_creates_and_modifies_no_file(export):
    catalog = build_acquisition_catalog_service()
    _process(export, ROTATED)
    before = _files_with_dates(export)

    _by_name(catalog, export)
    _by_name(catalog, export, force=True)

    assert _files_with_dates(export) == before


def test_the_map_of_a_processed_step_is_the_one_the_old_window_drew(export):
    _process(export, ROTATED)
    acquisition = export / ROTATED / f"{ROTATED}.h5"
    field_map_service = build_field_map_service()
    old_model = VisualisationModel(export)

    steps = field_map_service.list_steps(StepsRequestDTO(str(acquisition)))
    assert steps == STEP_NAMES

    for step in steps:
        new = field_map_service.load_step(LoadStepDTO(str(acquisition), step))
        old_grids, old_extent, _ = old_model.get_step_data(acquisition, step)
        assert list(new.grids) == list(old_grids)
        for channel in old_grids:
            assert np.array_equal(new.grids[channel], old_grids[channel], equal_nan=True), f"{step}/{channel}"
        assert list(new.extent) == [float(v) for v in old_extent], step
