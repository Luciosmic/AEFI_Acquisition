"""
Z Axis Scan Trajectory Factory - Domain Service

Responsibility:
- Sample a ZAxisScanConfig into an ordered ZAxisTrajectory.
- n_points equally spaced heights from z_min to z_max (ascending).
- n_points=1 -> single point at z_min (same convention as ScanTrajectoryFactory).
"""

from domain.step_scan.value_objects.z_axis_scan_config.z_axis_scan_config import ZAxisScanConfig
from domain.step_scan.value_objects.z_axis_trajectory.z_axis_trajectory import ZAxisTrajectory


class ZAxisScanTrajectoryFactory:

    @staticmethod
    def create_trajectory(config: ZAxisScanConfig) -> ZAxisTrajectory:
        span = config.z_max_mm - config.z_min_mm
        step = span / (config.n_points - 1) if config.n_points > 1 else 0
        return ZAxisTrajectory(
            xy_position=config.xy_position,
            z_values=[config.z_min_mm + i * step for i in range(config.n_points)],
        )
