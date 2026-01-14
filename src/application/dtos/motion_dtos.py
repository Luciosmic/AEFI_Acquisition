"""
Motion DTOs - Application Layer

Data Transfer Objects for exposing AtomicMotion to UI/API.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AtomicMotionDTO:
    """
    DTO for exposing AtomicMotion to UI.
    
    Provides a user-friendly representation of atomic motion information.
    """
    id: str
    dx: float
    dy: float
    distance_mm: float
    estimated_duration_seconds: float
    profile_name: str  # "slow" | "fast" | "custom"
    state: str  # "pending" | "executing" | "completed" | "failed"
    execution_motion_id: Optional[str] = None
    actual_duration_seconds: Optional[float] = None  # Filled after completion


@dataclass
class MotionProfileDTO:
    """
    DTO for exposing MotionProfile to UI.
    """
    min_speed_mm_s: float
    target_speed_mm_s: float
    acceleration_mm_s2: float
    deceleration_mm_s2: float
    name: str = "custom"  # "slow" | "fast" | "custom"


@dataclass
class TrajectoryPreviewDTO:
    """
    DTO for trajectory preview with motion information.
    """
    total_motions: int
    total_estimated_duration_seconds: float
    slow_motions_count: int
    fast_motions_count: int
    motions: list[AtomicMotionDTO]

