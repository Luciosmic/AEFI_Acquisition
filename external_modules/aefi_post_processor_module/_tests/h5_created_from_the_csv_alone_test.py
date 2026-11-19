"""Le .h5 naît du seul CSV (test d'acceptation de 2.9) : l'acquisition n'exporte plus de .h5, le traitement crée le sien,
avec les données brutes relues du CSV, ses cinq étapes et la provenance (CSV source, son SHA-256, activité)."""

import hashlib
import json
import shutil
from pathlib import Path

import h5py
import numpy as np
import pytest

from aefi_post_processor_module.application.field_map_service.dtos.steps_request_dto import StepsRequestDTO
from aefi_post_processor_module.application.post_processing_service.dtos.process_scan_dto import ProcessScanDTO
from aefi_post_processor_module.domain.processing.processing_steps.processing_steps import STEP_NAMES, ProcessingParameters
from aefi_post_processor_module.interface.shell.headless_wiring import (
    build_field_map_service,
    build_post_processing_service,
)

BATCH = Path(__file__).resolve().parent / "synthetic_scans_data_repository" / "batch_20260123_201635"
NAME = "2026-11-19_101500_stepScan_plaque"
ACTIVITY_ID = "5c2b7d3e-0f4a-4e57-8d58-1a6b2c9e4f10"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def acquisition(tmp_path):
    """A folder as the acquisition leaves it now: the CSV and its parameters file, no .h5."""
    folder = tmp_path / NAME
    folder.mkdir()
    csv = folder / f"{NAME}_aefi.csv"
    shutil.copy(BATCH / "scan_001_baseline.csv", csv)
    (folder / f"{NAME}_acquisition-parameters.json").write_text(json.dumps({
        "schema": {"name": "aefi-acquisition-parameters", "version": "1.6"},
        "provenance": {"activity": {"id": ACTIVITY_ID, "kind": "step_scan", "status": "completed"}},
        "data": {"files": [{"name": csv.name, "format": "CSV", "sha256": _sha256(csv)}]},
    }), encoding="utf-8")
    return folder


def _process(folder: Path):
    h5 = folder / f"{NAME}.h5"
    service, writer = build_post_processing_service(str(h5))
    try:
        service.process_scan(ProcessScanDTO(
            str(folder / f"{NAME}_aefi.csv"), str(h5), ProcessingParameters(rotation_angles=(0.0, 0.0, 45.0))))
    finally:
        writer.close()
    return h5


def test_the_h5_is_created_by_the_processing_from_the_csv_alone(acquisition):
    assert list(acquisition.glob("*.h5")) == []

    h5 = _process(acquisition)

    assert h5.exists()
    steps = build_field_map_service().list_steps(StepsRequestDTO(str(h5)))
    assert steps == tuple(STEP_NAMES)


def test_the_raw_points_are_re_read_from_the_csv(acquisition):
    h5 = _process(acquisition)

    with h5py.File(h5, "r") as f:
        raw = f["raw_scan"]
        assert raw["positions"].shape[1] == 2 and raw["values"].shape[0] == raw["positions"].shape[0] > 0
        assert not np.isnan(raw["positions"][...]).any()


def test_the_provenance_names_the_csv_its_hash_equal_to_the_acquisitions_and_the_activity(acquisition):
    csv = acquisition / f"{NAME}_aefi.csv"
    h5 = _process(acquisition)

    with h5py.File(h5, "r") as f:
        assert f.attrs["source_csv"] == str(csv)
        assert f.attrs["source_sha256"] == _sha256(csv)
        assert f.attrs["source_activity_id"] == ACTIVITY_ID
        assert f.attrs["source_declared_sha256"] == _sha256(csv)
        assert bool(f.attrs["source_sha256_matches"]) is True


def test_the_csv_is_not_touched_by_the_processing(acquisition):
    csv = acquisition / f"{NAME}_aefi.csv"
    before = (_sha256(csv), csv.stat().st_mtime)

    _process(acquisition)

    assert (_sha256(csv), csv.stat().st_mtime) == before
