"""Tests for the Arcus motion timing characterizer (pure parts + dry run)."""
import json

import pytest

from infrastructure.hardware.arcus_performax_4EX.characterization.motion_timing_characterizer import (
    Move, fit, main, plan_moves,
)


def test_plan_is_out_and_back_so_the_bench_returns_to_center():
    plan = plan_moves(modes=("slow", "fast"), distances_mm=(2.5, 10.0), reps=2, seed=1)
    assert len(plan) == 2 * 2 * 2 * 2 * 2  # modes x configs x distances x reps x (out, back)
    for out, back in zip(plan[0::2], plan[1::2]):
        assert (back.dx_mm, back.dy_mm) == (-out.dx_mm, -out.dy_mm)
        assert back.mode == out.mode


def test_plan_changes_speed_once_per_mode():
    plan = plan_moves(modes=("slow", "medium", "fast"), distances_mm=(5.0,), reps=3, seed=0)
    modes_in_order = [m.mode for i, m in enumerate(plan) if i == 0 or plan[i - 1].mode != m.mode]
    assert modes_in_order == ["slow", "medium", "fast"]


def test_diagonal_move_costs_its_largest_axis():
    assert Move("fast", "diag", 10.0, -10.0).distance_mm == 10.0


def _rows(level, mode, speed, t0, distances, config="x"):
    return [
        {"level": level, "mode": mode, "config": config, "distance_mm": d, "duration_s": t0 + d / speed}
        for d in distances
    ]


def test_fit_recovers_speed_and_t0():
    rows = _rows("port", "medium", speed=32.7, t0=0.42, distances=(2.5, 10, 25, 50, 100))
    rows += _rows("port", "medium", speed=32.7, t0=0.42, distances=(5, 50), config="diag")
    result = fit(rows)["port"]["medium"]
    assert result["speed_mm_s"] == pytest.approx(32.7)
    assert result["t0_s"] == pytest.approx(0.42)
    assert result["n"] == 7
    assert result["mean_residual_by_config_s"]["diag"] == pytest.approx(0.0, abs=1e-9)


def test_fit_is_per_level_and_mode():
    rows = _rows("port", "slow", 17.4, 0.4, (10, 50)) + _rows("controller", "slow", 17.4, 0.05, (10, 50))
    result = fit(rows)
    assert result["port"]["slow"]["t0_s"] == pytest.approx(0.4)
    assert result["controller"]["slow"]["t0_s"] == pytest.approx(0.05)


def test_dry_run_writes_csv_and_summary(tmp_path):
    summary_path = main([
        "--dry-run", "--yes", "--modes", "fast", "--distances", "1", "2", "--reps", "1",
        "--out-dir", str(tmp_path),
    ])
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["dry_run"] is True
    assert set(summary["fit"]) == {"controller", "port"}
    assert summary["fit"]["port"]["fast"]["n"] == 8  # 2 configs x 2 distances x (out, back)
    assert len(list(tmp_path.glob("*.csv"))) == 1


def test_single_distance_is_rejected_before_anything_moves(tmp_path):
    with pytest.raises(SystemExit):
        main(["--dry-run", "--yes", "--distances", "5", "--out-dir", str(tmp_path)])
    assert not list(tmp_path.iterdir())
