"""Observability of the post-processor: batch sync outcome."""

import logging
import os

from aefi_post_processor_module import composition_root


class _FakePipeline:
    """Fails on any CSV whose folder name contains 'broken', succeeds otherwise."""

    def __init__(self, output_path):
        self.output_path = output_path

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def run_full_pipeline(self, csv_path, rotation_angles=None, reference_point=(0, 0)):
        if "broken" in csv_path.parent.name:
            raise ValueError("malformed CSV")
        self.output_path.write_text("h5", encoding="utf-8")


def _make_scan(raw_dir, name, with_h5=False):
    folder = raw_dir / name
    folder.mkdir()
    csv = folder / f"{name}_aefi.csv"
    csv.write_text("x,y\n", encoding="utf-8")
    if with_h5:
        h5 = folder / f"{name}.h5"
        h5.write_text("h5", encoding="utf-8")
        stamp = csv.stat().st_mtime
        os.utime(h5, (stamp + 10, stamp + 10))
    return folder


def test_sync_reports_each_scan_outcome_and_names_failures(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(composition_root, "ProcessingPipeline", _FakePipeline)
    monkeypatch.setattr(composition_root, "_ideal_rotation_angles", lambda: (35.3, 45.0, 0.0))
    _make_scan(tmp_path, "20261112_stepScan_ok")
    _make_scan(tmp_path, "20261112_stepScan_broken")
    _make_scan(tmp_path, "20261112_flyScan_done", with_h5=True)

    with caplog.at_level(logging.DEBUG):
        summary = composition_root.sync_scans(tmp_path)

    assert summary.processed == ["20261112_stepScan_ok"]
    assert summary.failed == ["20261112_stepScan_broken"]
    assert summary.skipped == ["20261112_flyScan_done"]

    messages = [r.getMessage() for r in caplog.records]
    assert any(
        m.startswith("scan.failed scan=20261112_stepScan_broken error_type=ValueError") for m in messages
    )
    assert any("rotation_origin=ideal_template" in m and "20261112_stepScan_ok" in m for m in messages)
    assert "scan.up_to_date scan=20261112_flyScan_done action=none" in messages
    finished = [r for r in caplog.records if r.getMessage().startswith("sync.finished")]
    assert finished[0].levelno == logging.WARNING
    assert "processed=1 skipped=1 failed=1" in finished[0].getMessage()


def test_sync_on_missing_directory_logs_an_error(tmp_path, caplog):
    summary = composition_root.sync_scans(tmp_path / "absent")

    assert summary.processed == summary.failed == summary.skipped == []
    assert any(r.levelno == logging.ERROR and "raw_dir_not_found" in r.getMessage() for r in caplog.records)
