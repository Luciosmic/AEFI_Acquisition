from pathlib import Path

from tool import runtime_data_guard as guard


def _runtime(tmp_path: Path) -> Path:
    runtime = tmp_path / ".aefi_acquisition"
    (runtime / "configs").mkdir(parents=True)
    (runtime / "calibrations").mkdir()
    (runtime / "logs").mkdir()
    (runtime / "configs" / "ad9106_last_config.json").write_text('{"gain": 12}', encoding="utf-8")
    (runtime / "calibrations" / "sensor_calibration.json").write_text('{"angles": [35.3, 45, 0]}', encoding="utf-8")
    (runtime / "logs" / "app.log").write_text("x" * 100, encoding="utf-8")
    return runtime


def test_untouched_runtime_data_reports_no_change(tmp_path):
    snapshot = guard.RuntimeDataSnapshot.take(_runtime(tmp_path))

    assert not snapshot.changes().any
    snapshot.discard()


def test_a_modified_file_is_seen_and_put_back(tmp_path):
    runtime = _runtime(tmp_path)
    snapshot = guard.RuntimeDataSnapshot.take(runtime)

    (runtime / "configs" / "ad9106_last_config.json").write_text('{"gain": 0}', encoding="utf-8")
    changes = snapshot.changes()
    snapshot.restore(changes)

    assert changes.modified == ["configs/ad9106_last_config.json"]
    assert (runtime / "configs" / "ad9106_last_config.json").read_text(encoding="utf-8") == '{"gain": 12}'


def test_a_deleted_calibration_is_seen_and_put_back(tmp_path):
    runtime = _runtime(tmp_path)
    snapshot = guard.RuntimeDataSnapshot.take(runtime)

    (runtime / "calibrations" / "sensor_calibration.json").unlink()
    changes = snapshot.changes()
    snapshot.restore(changes)

    assert changes.deleted == ["calibrations/sensor_calibration.json"]
    assert (runtime / "calibrations" / "sensor_calibration.json").exists()


def test_a_created_file_is_reported_not_deleted(tmp_path):
    runtime = _runtime(tmp_path)
    snapshot = guard.RuntimeDataSnapshot.take(runtime)

    (runtime / "configs" / "stray.json").write_text("{}", encoding="utf-8")
    changes = snapshot.changes()
    snapshot.restore(changes)

    assert changes.added == ["configs/stray.json"]
    assert (runtime / "configs" / "stray.json").exists()


def test_logs_are_neither_copied_nor_compared(tmp_path):
    runtime = _runtime(tmp_path)
    snapshot = guard.RuntimeDataSnapshot.take(runtime)

    (runtime / "logs" / "app.log").write_text("grown", encoding="utf-8")

    assert not snapshot.changes().any
    assert not (snapshot.backup_dir / ".aefi_acquisition" / "logs").exists()


def test_no_runtime_directory_means_no_snapshot(tmp_path):
    assert guard.RuntimeDataSnapshot.take(tmp_path / ".aefi_acquisition") is None


def test_the_report_names_the_files_and_where_the_copy_is(tmp_path):
    changes = guard.Changes(modified=["configs/motion_last_config.json"], added=["configs/stray.json"])

    text = "\n".join(guard.report(changes, tmp_path / ".aefi_acquisition", tmp_path / "backup"))

    assert "configs/motion_last_config.json" in text and "stray.json" in text and "backup" in text
    assert "remis à leur état d'avant" in text


def test_tests_are_refused_on_main_unless_explicitly_allowed(tmp_path, monkeypatch):
    monkeypatch.setattr(guard, "current_branch", lambda _root: "main")

    reason = guard.refusal_reason(tmp_path, {})

    assert reason is not None and "main" in reason and guard.OVERRIDE_ENV in reason
    assert guard.refusal_reason(tmp_path, {guard.OVERRIDE_ENV: "1"}) is None


def test_tests_are_allowed_on_develop_and_when_git_cannot_say(tmp_path, monkeypatch):
    monkeypatch.setattr(guard, "current_branch", lambda _root: "develop")
    assert guard.refusal_reason(tmp_path, {}) is None

    monkeypatch.setattr(guard, "current_branch", lambda _root: None)
    assert guard.refusal_reason(tmp_path, {}) is None


def test_the_real_branch_is_readable_in_a_git_checkout():
    branch = guard.current_branch(Path(__file__).resolve().parent)

    assert branch is None or isinstance(branch, str)
