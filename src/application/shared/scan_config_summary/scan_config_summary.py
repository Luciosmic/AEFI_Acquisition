"""Plain-dict summary of a scan configuration (step or line).

Single source of the config-to-facts mapping, shared by the export metadata
(ScanExportService) and the live configuration query (ScanApplicationService),
so the two cannot drift apart.
"""

from typing import Any, Dict, Union

from domain.step_scan.value_objects.line_scan_config.line_scan_config import LineScanConfig
from domain.step_scan.value_objects.step_scan_config.step_scan_config import StepScanConfig


def summarize_scan_config(cfg: Union[StepScanConfig, LineScanConfig]) -> Dict[str, Any]:
    """Facts of a scan configuration. Line scans carry `scan_kind: "line"`;
    the step-scan shape has no `scan_kind` key (kept as exported historically)."""
    if isinstance(cfg, LineScanConfig):
        start, end = cfg.endpoints()
        return {
            "scan_kind": "line",
            "center_x": cfg.center.x,
            "center_y": cfg.center.y,
            "length_mm": cfg.length_mm,
            "theta_deg": cfg.theta_deg,
            "start_x": start.x,
            "start_y": start.y,
            "end_x": end.x,
            "end_y": end.y,
            "stabilization_delay_ms": cfg.stabilization_delay_ms,
            "averaging_per_position": cfg.averaging_per_position,
            "total_points": cfg.total_points(),
        }

    zone = cfg.scan_zone
    return {
        "pattern": cfg.scan_pattern.name,
        "scan_axis": cfg.scan_axis.name,
        # True = exploration map (positions interpolated at constant
        # speed, no averaging) — not to be read as a measurement.
        "fly_scan": cfg.fly_scan,
        "x_min": zone.x_min,
        "x_max": zone.x_max,
        "x_nb_points": cfg.x_nb_points,
        "y_min": zone.y_min,
        "y_max": zone.y_max,
        "y_nb_points": cfg.y_nb_points,
        "stabilization_delay_ms": cfg.stabilization_delay_ms,
        "averaging_per_position": cfg.averaging_per_position,
        "total_points": cfg.total_points(),
        "estimated_duration_s": cfg.estimated_duration_seconds(),
    }
