"""
Arcus Motion Timing Characterizer — bench tool

Measures how long a move takes on the real Arcus bench, as a function of
displacement, per speed mode, and fits  t = t0 + max(|dx|, |dy|) / v
(axes move together, ramp negligible). Two levels:
- controller: driver command -> axes stopped AND at target
- port:       ArcusAdapter.move_to -> MotionCompleted event

Usage (from the repo root, app CLOSED, bench clear):
    uv run python src/infrastructure/hardware/arcus_performax_4EX/characterization/motion_timing_characterizer.py
    ... --dry-run          # FakeArcusPerformax4EXController, no hardware
    ... --modes medium --reps 1 --distances 5 50
"""
import argparse
import csv
import json
import logging
import queue
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

# Script entry point: make `src/` importable when run as a file.
_SRC = Path(__file__).resolve().parents[4]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain.shared_kernel.value_objects.geometric.position_2d import Position2D  # noqa: E402
from infrastructure.events.in_memory_event_bus import InMemoryEventBus  # noqa: E402
from infrastructure.hardware.arcus_performax_4EX.composition_root_arcus import ArcusCompositionRoot  # noqa: E402

logger = logging.getLogger(__name__)

DEFAULT_MODES = ("slow", "medium", "fast")
DEFAULT_DISTANCES_MM = (2.5, 10.0, 25.0, 50.0, 100.0)
DEFAULT_REPS = 3
DEFAULT_CENTER_MM = (600.0, 600.0)
DEFAULT_OUT_DIR = Path.home() / "Desktop" / "AEFI_Acquisition_Exports" / "motion_characterization"
LEVELS = ("controller", "port")
# Unit direction per move shape. 'diag' checks that a diagonal costs
# max(|dx|, |dy|) — i.e. that both axes move together.
CONFIGS = {"x": (1.0, 0.0), "diag": (1.0, 1.0)}
POLL_S = 0.01
MOVE_TIMEOUT_S = 60.0
HOMING_TIMEOUT_S = 120.0


@dataclass(frozen=True)
class Move:
    mode: str
    config: str
    dx_mm: float
    dy_mm: float

    @property
    def distance_mm(self) -> float:
        return max(abs(self.dx_mm), abs(self.dy_mm))


# ------------------------------------------------------------------------- #
# Pure parts (tested)
# ------------------------------------------------------------------------- #

def plan_moves(modes: Sequence[str], distances_mm: Sequence[float], reps: int, seed: int = 0) -> List[Move]:
    """Out-and-back moves around the center (both directions measured, bench
    always returns to center). One speed change per mode; order randomized
    inside a mode so drift doesn't correlate with distance."""
    rng = random.Random(seed)
    plan: List[Move] = []
    for mode in modes:
        block = [
            Move(mode, config, ux * d, uy * d)
            for config, (ux, uy) in CONFIGS.items()
            for d in distances_mm
            for _ in range(reps)
        ]
        rng.shuffle(block)
        for out in block:
            plan.append(out)
            plan.append(Move(mode, out.config, -out.dx_mm, -out.dy_mm))
    return plan


def fit(rows: List[dict]) -> Dict[str, Dict[str, dict]]:
    """Least-squares t = t0 + d/v per (level, mode). `mean_residual_by_config_s`
    ~0 for 'diag' confirms the max(|dx|, |dy|) cost (axes move together)."""
    result: Dict[str, Dict[str, dict]] = {}
    for level in sorted({r["level"] for r in rows}):
        for mode in sorted({r["mode"] for r in rows if r["level"] == level}):
            sel = [r for r in rows if r["level"] == level and r["mode"] == mode]
            d = np.array([r["distance_mm"] for r in sel], dtype=float)
            t = np.array([r["duration_s"] for r in sel], dtype=float)
            slope, t0 = np.polyfit(d, t, 1)
            residuals = t - (t0 + slope * d)
            configs = sorted({r["config"] for r in sel})
            result.setdefault(level, {})[mode] = {
                "speed_mm_s": float(1.0 / slope),
                "t0_s": float(t0),
                "residual_std_s": float(residuals.std(ddof=2)) if len(sel) > 2 else 0.0,
                "max_abs_residual_s": float(np.abs(residuals).max()),
                "n": len(sel),
                "mean_residual_by_config_s": {
                    c: float(residuals[[r["config"] == c for r in sel]].mean()) for c in configs
                },
            }
    return result


# ------------------------------------------------------------------------- #
# Measurement (hardware)
# ------------------------------------------------------------------------- #

def _measure_controller(controller, target_steps: Dict[str, int]) -> float:
    """Driver command -> both axes stopped AND at target. is_moving alone can
    still read False right after the command (status register lag)."""
    start = time.perf_counter()
    for axis, steps in target_steps.items():
        controller.move_to(axis, steps)
    while controller.is_moving() or any(
        round(controller.get_position(axis)) != steps for axis, steps in target_steps.items()
    ):
        if time.perf_counter() - start > MOVE_TIMEOUT_S:
            raise TimeoutError(f"controller move to {target_steps} not done after {MOVE_TIMEOUT_S}s")
        time.sleep(POLL_S)
    return time.perf_counter() - start


def _measure_port(adapter, events: "queue.Queue", target: Position2D) -> float:
    """ArcusAdapter.move_to -> MotionCompleted for that motion_id."""
    start = time.perf_counter()
    motion_id = adapter.move_to(target)
    while True:
        remaining = MOVE_TIMEOUT_S - (time.perf_counter() - start)
        if remaining <= 0:
            raise TimeoutError(f"no MotionCompleted for {target} after {MOVE_TIMEOUT_S}s")
        topic, event = events.get(timeout=remaining)
        if event.motion_id != motion_id:
            continue
        if topic == "motionfailed":
            raise RuntimeError(f"motion to {target} failed: {event.error}")
        return time.perf_counter() - start


def _confirm(assume_yes: bool) -> bool:
    if assume_yes:
        return True
    answer = input("Le banc va bouger (homing si nécessaire, puis allers-retours autour du centre). "
                   "App fermée, zone dégagée ? [o/N] ")
    return answer.strip().lower() in ("o", "oui", "y", "yes")


def main(argv: Optional[Sequence[str]] = None) -> Optional[Path]:
    parser = argparse.ArgumentParser(description="Characterize Arcus move duration vs displacement.")
    parser.add_argument("--modes", nargs="+", default=list(DEFAULT_MODES))
    parser.add_argument("--distances", nargs="+", type=float, default=list(DEFAULT_DISTANCES_MM))
    parser.add_argument("--reps", type=int, default=DEFAULT_REPS)
    parser.add_argument("--center", nargs=2, type=float, default=list(DEFAULT_CENTER_MM), metavar=("X_MM", "Y_MM"))
    parser.add_argument("--levels", nargs="+", default=list(LEVELS), choices=LEVELS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--dry-run", action="store_true", help="FakeArcus controller, no hardware")
    parser.add_argument("--yes", action="store_true", help="skip the operator confirmation")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)
    if len(set(args.distances)) < 2:
        parser.error("--distances needs at least 2 distinct values to fit t0 and v")

    if not _confirm(args.yes or args.dry_run):
        logger.info("Characterization: operator declined. Nothing moved.")
        return None

    bus = InMemoryEventBus()
    events: "queue.Queue" = queue.Queue()
    bus.subscribe("motioncompleted", lambda e: events.put(("motioncompleted", e)))
    bus.subscribe("motionfailed", lambda e: events.put(("motionfailed", e)))

    controller = None
    if args.dry_run:
        from infrastructure.hardware.arcus_performax_4EX.fake.fake_arcus_performax4ex_controller import (
            FakeArcusPerformax4EXController,
        )
        controller = FakeArcusPerformax4EXController()
    root = ArcusCompositionRoot(event_bus=bus, controller=controller)
    driver, adapter = root._driver, root.motion

    plan = plan_moves(args.modes, args.distances, args.reps, seed=args.seed)
    center = Position2D(*args.center)
    logger.info("Characterization: Command run - %d moves x %s, center=%s, dry_run=%s",
                len(plan), args.levels, center, args.dry_run)

    rows: List[dict] = []
    axis_params: Dict[str, dict] = {}
    root.lifecycle.initialize_all()
    try:
        if args.dry_run:
            driver.set_homed("x")
            driver.set_homed("y")
        if not (driver.is_homed("x") and driver.is_homed("y")):
            logger.info("Characterization: axes not homed - homing both.")
            adapter.home()
            adapter.wait_until_stopped(timeout=HOMING_TIMEOUT_S)
        else:
            logger.info("Characterization: axes already homed. Skipping homing.")

        adapter.set_speed_mode("fast")
        adapter.move_to(center)
        adapter.wait_until_stopped(timeout=MOVE_TIMEOUT_S)

        steps_per_mm = adapter.STEPS_PER_MM
        for level in args.levels:
            # controller level: adapter threads off (no monitor contention);
            # port level: adapter on, as the app runs it.
            adapter.disable() if level == "controller" else adapter.enable()
            position = center
            current_mode = None
            for i, move in enumerate(plan, start=1):
                if move.mode != current_mode:
                    adapter.set_speed_mode(move.mode)
                    current_mode = move.mode
                    axis_params[move.mode] = driver.get_axis_params_dict("x")
                    logger.info("Characterization: level=%s mode=%s axis_params=%s",
                                level, move.mode, axis_params[move.mode])
                target = Position2D(position.x + move.dx_mm, position.y + move.dy_mm)
                if level == "controller":
                    duration = _measure_controller(driver, {
                        "x": int(round(target.x * steps_per_mm)),
                        "y": int(round(target.y * steps_per_mm)),
                    })
                else:
                    duration = _measure_port(adapter, events, target)
                position = target
                rows.append({
                    "timestamp": datetime.now().isoformat(timespec="milliseconds"),
                    "level": level, "mode": move.mode, "config": move.config,
                    "dx_mm": move.dx_mm, "dy_mm": move.dy_mm, "distance_mm": move.distance_mm,
                    "duration_s": duration,
                    "hs_hz": axis_params[move.mode]["hs"], "acc_ms": axis_params[move.mode]["acc"],
                })
                logger.info("Characterization: [%s %d/%d] %s %s d=%.1fmm -> %.3fs",
                            level, i, len(plan), move.mode, move.config, move.distance_mm, duration)
        adapter.enable()
    finally:
        root.lifecycle.close_all()

    fitted = fit(rows)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S") + ("_dryrun" if args.dry_run else "")
    csv_path = args.out_dir / f"{stamp}_arcus_motion_timing.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary_path = args.out_dir / f"{stamp}_arcus_motion_timing.json"
    summary = {
        "date": datetime.now().isoformat(timespec="seconds"),
        "dry_run": args.dry_run,
        "model": "t = t0 + max(|dx|,|dy|) / v",
        "microns_per_step": adapter.MICRONS_PER_STEP,
        "center_mm": list(args.center),
        "distances_mm": args.distances,
        "reps": args.reps,
        "axis_params_by_mode": axis_params,
        "theoretical_speed_mm_s": {m: p["hs"] / adapter.STEPS_PER_MM for m, p in axis_params.items()},
        "fit": fitted,
        "raw_csv": csv_path.name,
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("Characterization: done - %d rows, csv=%s, summary=%s", len(rows), csv_path, summary_path)

    for level, modes in fitted.items():
        for mode, r in modes.items():
            print(f"{level:10s} {mode:6s}  v={r['speed_mm_s']:7.2f} mm/s  t0={r['t0_s']:.3f} s  "
                  f"resid_std={r['residual_std_s']:.3f} s  diag_resid={r['mean_residual_by_config_s'].get('diag', 0):+.3f} s")
    return summary_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    main()
