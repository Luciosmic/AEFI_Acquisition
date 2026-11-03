"""
Line Scan Trajectory Factory - Domain Service

Responsibility:
- Sample a LineScanConfig into an ordered ScanTrajectory.
- n_points equally spaced from s=-length/2 to s=+length/2.
- n_points=1 -> single point at the line start (same convention as
  ScanTrajectoryFactory's step=0), not the center.
"""

from domain.step_scan.value_objects.line_scan_config.line_scan_config import LineScanConfig
from domain.step_scan.value_objects.scan_trajectory.scan_trajectory import ScanTrajectory


class LineScanTrajectoryFactory:

    @staticmethod
    def create_trajectory(config: LineScanConfig) -> ScanTrajectory:
        start = -config.length_mm / 2
        step = config.length_mm / (config.n_points - 1) if config.n_points > 1 else 0
        return ScanTrajectory(points=[config.point_at(start + i * step) for i in range(config.n_points)])
