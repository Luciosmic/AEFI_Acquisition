"""
Atomic Motion Entity

Represents a single atomic movement based on relative distance (dx, dy).
This is a domain entity that encapsulates the movement logic for scan trajectories.

Responsibility:
- Represent a single atomic movement in a scan trajectory
- Track execution state and motion profile
- Calculate estimated duration based on distance and profile
"""

from dataclasses import dataclass, field
from uuid import UUID, uuid4
from typing import Optional, List
import math

from domain.models.scan.value_objects.motion_state import MotionState
from domain.models.test_bench.value_objects.motion_profile import MotionProfile
from domain.shared.value_objects.position_2d import Position2D


@dataclass
class AtomicMotion:
    """
    Domain entity representing a single atomic movement.
    
    Attributes:
        id: UUID - Domain identity (persistent)
        dx: float - Relative displacement in X (mm)
        dy: float - Relative displacement in Y (mm)
        motion_profile: MotionProfile - Profile selected for this motion
        estimated_duration_seconds: float - Calculated duration
        execution_motion_id: Optional[str] - Execution identity (ephemeral, linked to events)
        execution_state: MotionState - Current execution state
    """
    
    dx: float
    dy: float
    motion_profile: MotionProfile
    id: UUID = field(default_factory=uuid4)
    estimated_duration_seconds: float = field(init=False)
    execution_motion_id: Optional[str] = None
    execution_state: MotionState = MotionState.PENDING
    
    def __post_init__(self):
        """Calculate estimated duration and validate."""
        self.estimated_duration_seconds = self.calculate_estimated_duration()
        self._validate()
    
    def _validate(self):
        """Validate motion parameters."""
        if math.isnan(self.dx) or math.isnan(self.dy):
            raise ValueError("Motion displacement cannot be NaN")
        if math.isinf(self.dx) or math.isinf(self.dy):
            raise ValueError("Motion displacement cannot be infinite")
    
    def calculate_estimated_duration(self) -> float:
        """
        Calculate estimated duration based on distance and motion profile.
        
        Uses trapezoidal velocity profile:
        - Acceleration phase: from min_speed to target_speed
        - Constant speed phase: if distance allows
        - Deceleration phase: from target_speed to min_speed
        
        Returns:
            Estimated duration in seconds
        """
        distance = self.get_distance()
        profile = self.motion_profile
        
        # Extract profile parameters
        min_speed = profile.min_speed
        target_speed = profile.target_speed
        acceleration = profile.acceleration
        deceleration = profile.deceleration
        
        # Time and distance for acceleration phase
        t_acc = (target_speed - min_speed) / acceleration if acceleration > 0 else 0
        d_acc = min_speed * t_acc + 0.5 * acceleration * t_acc ** 2
        
        # Time and distance for deceleration phase
        t_dec = (target_speed - min_speed) / deceleration if deceleration > 0 else 0
        d_dec = target_speed * t_dec - 0.5 * deceleration * t_dec ** 2
        
        # Check if we have enough distance for full profile
        if distance < d_acc + d_dec:
            # Not enough distance: triangular profile (no constant speed phase)
            # Solve: distance = d_acc + d_dec with adjusted speeds
            # Simplified: use average speed approximation
            avg_speed = (min_speed + target_speed) / 2
            return distance / avg_speed if avg_speed > 0 else 0
        else:
            # Full trapezoidal profile
            d_constant = distance - d_acc - d_dec
            t_constant = d_constant / target_speed if target_speed > 0 else 0
            return t_acc + t_constant + t_dec
    
    def get_distance(self) -> float:
        """Calculate total distance of the motion."""
        return math.sqrt(self.dx ** 2 + self.dy ** 2)
    
    def start(self, motion_id: str) -> None:
        """
        Start execution of this motion.
        
        Args:
            motion_id: Execution motion ID (from MotionStarted event)
        """
        if self.execution_state != MotionState.PENDING:
            raise ValueError(f"Cannot start motion in state {self.execution_state}")
        
        self.execution_motion_id = motion_id
        self.execution_state = MotionState.EXECUTING
    
    def complete(self) -> None:
        """Mark motion as completed."""
        if self.execution_state != MotionState.EXECUTING:
            raise ValueError(f"Cannot complete motion in state {self.execution_state}")
        
        self.execution_state = MotionState.COMPLETED
    
    def fail(self, error: str) -> None:
        """
        Mark motion as failed.

        Args:
            error: Error message describing the failure
        """
        if self.execution_state not in (MotionState.PENDING, MotionState.EXECUTING):
            raise ValueError(f"Cannot fail motion in state {self.execution_state}")

        self.execution_state = MotionState.FAILED

    def get_velocity_at_time(self, t: float) -> float:
        """
        Calculate instantaneous velocity at time t using trapezoidal profile.

        Velocity profile:
        - 0 <= t < t_acc: v(t) = min_speed + acceleration * t
        - t_acc <= t < t_acc + t_constant: v(t) = target_speed
        - t_acc + t_constant <= t <= total_duration: v(t) = target_speed - deceleration * (t - t_acc - t_constant)

        Args:
            t: Time since motion start (seconds)

        Returns:
            Instantaneous velocity (mm/s)
        """
        if t < 0:
            return 0.0

        profile = self.motion_profile
        distance = self.get_distance()

        # Calculate phase durations
        min_speed = profile.min_speed
        target_speed = profile.target_speed
        acceleration = profile.acceleration
        deceleration = profile.deceleration

        # Time for acceleration phase
        t_acc = (target_speed - min_speed) / acceleration if acceleration > 0 else 0

        # Distance for acceleration and deceleration
        d_acc = min_speed * t_acc + 0.5 * acceleration * t_acc ** 2
        t_dec = (target_speed - min_speed) / deceleration if deceleration > 0 else 0
        d_dec = target_speed * t_dec - 0.5 * deceleration * t_dec ** 2

        # Check if we have enough distance for full profile
        if distance < d_acc + d_dec:
            # Triangular profile - simplified constant average speed
            avg_speed = (min_speed + target_speed) / 2
            return avg_speed if t < self.estimated_duration_seconds else 0.0

        # Full trapezoidal profile
        d_constant = distance - d_acc - d_dec
        t_constant = d_constant / target_speed if target_speed > 0 else 0

        # Determine which phase we're in
        if t < t_acc:
            # Acceleration phase
            return min_speed + acceleration * t
        elif t < t_acc + t_constant:
            # Constant speed phase
            return target_speed
        elif t < t_acc + t_constant + t_dec:
            # Deceleration phase
            time_in_dec = t - t_acc - t_constant
            return target_speed - deceleration * time_in_dec
        else:
            # Motion complete
            return 0.0

    def calculate_acquisition_positions(
        self,
        start_position: Position2D,
        acquisition_rate_hz: float
    ) -> List[Position2D]:
        """
        Calculate discrete acquisition positions along the motion path.

        During constant velocity phase, samples are evenly spaced.
        During acceleration/deceleration, spacing adjusts based on velocity.

        This method uses the trapezoidal velocity profile to accurately
        predict where samples will be acquired during continuous motion.

        Args:
            start_position: Starting position of the motion
            acquisition_rate_hz: Acquisition sampling rate (Hz)

        Returns:
            List of positions where samples will be acquired
        """
        if acquisition_rate_hz <= 0:
            return []

        positions = []

        # Sample period
        dt = 1.0 / acquisition_rate_hz

        # Total duration
        total_duration = self.estimated_duration_seconds

        # Direction unit vector
        distance = self.get_distance()
        if distance == 0:
            return [start_position]  # No motion

        dx_unit = self.dx / distance
        dy_unit = self.dy / distance

        # Integrate position over time
        t = 0.0
        accumulated_distance = 0.0

        while t <= total_duration:
            # Get velocity at this time
            velocity = self.get_velocity_at_time(t)

            # Calculate distance traveled since start
            # (For accurate integration, we sample at discrete points)
            # Simplified: accumulated_distance += velocity * dt

            # Calculate current position
            current_x = start_position.x + dx_unit * accumulated_distance
            current_y = start_position.y + dy_unit * accumulated_distance

            positions.append(Position2D(x=current_x, y=current_y))

            # Advance time and distance
            t += dt
            accumulated_distance += velocity * dt

            # Safety check: don't overshoot
            if accumulated_distance >= distance:
                break

        # Ensure we include the final position
        if len(positions) == 0 or positions[-1] != Position2D(
            x=start_position.x + self.dx,
            y=start_position.y + self.dy
        ):
            final_pos = Position2D(
                x=start_position.x + self.dx,
                y=start_position.y + self.dy
            )
            # Only add if we haven't already added it
            if len(positions) == 0 or (
                abs(positions[-1].x - final_pos.x) > 1e-6 or
                abs(positions[-1].y - final_pos.y) > 1e-6
            ):
                positions.append(final_pos)

        return positions

