"""
Dev-time bridge: call individual domain/infrastructure blocks (mocks only,
never real hardware) from an n8n "Execute Command" node, for interactive
exploration of the application layer while developing it.

Usage:
    uv run python tools/n8n_workflow_poc/dev_bridge.py <block> [key=value ...]
    uv run python tools/n8n_workflow_poc/dev_bridge.py            # list blocks + self-check

Args are plain key=value tokens (not JSON) so the command drops straight into
an n8n "Execute Command" node without fighting cmd.exe's quoting:
    uv run python tools/n8n_workflow_poc/dev_bridge.py trajectory.create x_nb_points=3 pattern=RASTER
then parse the `stdout` field (one JSON line) downstream.
"""
import contextlib
import io
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.shared_kernel.value_objects.measurement_uncertainty.measurement_uncertainty import MeasurementUncertainty
from domain.step_scan.services.scan_trajectory_factory.scan_trajectory_factory import ScanTrajectoryFactory
from domain.step_scan.value_objects.scan_pattern.scan_pattern import ScanPattern
from domain.step_scan.value_objects.scan_zone.scan_zone import ScanZone
from domain.step_scan.value_objects.step_scan_config.step_scan_config import StepScanConfig
from infrastructure.mocks.adapter_mock_i_acquisition_port import MockAcquisitionPort
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort


def block_trajectory_create(args: dict) -> dict:
    """Domain block — pure logic, no port involved."""
    config = StepScanConfig(
        scan_zone=ScanZone(
            x_min=args.get("x_min", 0.0), x_max=args.get("x_max", 1.0),
            y_min=args.get("y_min", 0.0), y_max=args.get("y_max", 1.0),
        ),
        x_nb_points=args.get("x_nb_points", 3),
        y_nb_points=args.get("y_nb_points", 3),
        scan_pattern=ScanPattern[args.get("pattern", "RASTER")],
        stabilization_delay_ms=0,
        averaging_per_position=1,
        measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=1e-6),
    )
    trajectory = ScanTrajectoryFactory.create_trajectory(config)
    return {
        "points": [{"x": p.x, "y": p.y} for p in trajectory.points],
        "total": len(trajectory.points),
    }


def block_motion_move_to(args: dict) -> dict:
    """Infra block — mock port only, event_bus=None keeps the move synchronous."""
    port = MockMotionPort(event_bus=None, motion_delay_ms=0)
    motion_id = port.move_to(Position2D(x=args.get("x", 0.0), y=args.get("y", 0.0)))
    pos = port.get_current_position()
    return {
        "motion_id": motion_id,
        "current_position": {"x": pos.x, "y": pos.y},
        "move_history": [{"x": p.x, "y": p.y} for p in port.move_history],
    }


def block_acquisition_sample(args: dict) -> dict:
    """Infra block — mock port only, never the real ADS131A04 driver."""
    port = MockAcquisitionPort()
    samples = []
    for _ in range(args.get("count", 1)):
        m = port.acquire_sample()
        samples.append({
            "x_in_phase": m.voltage_x_in_phase, "x_quadrature": m.voltage_x_quadrature,
            "y_in_phase": m.voltage_y_in_phase, "y_quadrature": m.voltage_y_quadrature,
            "z_in_phase": m.voltage_z_in_phase, "z_quadrature": m.voltage_z_quadrature,
        })
    return {"samples": samples, "acquire_count": port.acquire_count}


BLOCKS = {
    "trajectory.create": block_trajectory_create,
    "motion.move_to": block_motion_move_to,
    "acquisition.sample": block_acquisition_sample,
}


def coerce_value(value: str):
    """Numeric-looking string -> int/float, else left as string."""
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def parse_kv_args(tokens: list) -> dict:
    """key=value tokens -> dict, numeric-looking values coerced to int/float."""
    args = {}
    for token in tokens:
        key, _, value = token.partition("=")
        args[key] = coerce_value(value)
    return args


def call_block(block_name: str, args: dict) -> dict:
    """Run a block, swallowing the mocks' stdout chatter (only the JSON
    result should reach whoever is parsing our output — CLI or HTTP)."""
    with contextlib.redirect_stdout(io.StringIO()):
        return BLOCKS[block_name](args)


def _self_check():
    """ponytail: smallest thing that fails if a block's wiring breaks."""
    r = block_trajectory_create({"x_nb_points": 2, "y_nb_points": 2, "pattern": "RASTER"})
    assert r["total"] == 4

    r2 = block_motion_move_to({"x": 1.0, "y": 2.0})
    assert r2["current_position"] == {"x": 1.0, "y": 2.0}

    r3 = block_acquisition_sample({"count": 2})
    assert len(r3["samples"]) == 2

    print("self-check OK", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        _self_check()
        print(json.dumps({"available_blocks": list(BLOCKS)}))
        sys.exit(0)

    block_name = sys.argv[1]
    if block_name not in BLOCKS:
        print(json.dumps({"error": f"unknown block '{block_name}'", "available_blocks": list(BLOCKS)}))
        sys.exit(1)

    block_args = parse_kv_args(sys.argv[2:])
    print(json.dumps(call_block(block_name, block_args), ensure_ascii=False))
