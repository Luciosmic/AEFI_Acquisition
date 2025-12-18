"""
Motion State Tracker - Domain Service

Responsibility:
- Track AtomicMotion states during execution
- Map motion_id (from events) to AtomicMotion entities
- Provide statistics (actual vs estimated duration)

Rationale:
- Centralizes state tracking logic
- Enables reporting of motion progress
- Supports comparison of estimated vs actual durations
"""

from typing import Dict, Optional
from domain.models.scan.entities.atomic_motion import AtomicMotion
from domain.models.scan.value_objects.motion_state import MotionState


class MotionStateTracker:
    """
    Tracks the execution state of AtomicMotions.
    
    Maps execution motion IDs (from hardware events) to domain AtomicMotion entities.
    """
    
    def __init__(self):
        """Initialize the tracker."""
        self._motion_by_execution_id: Dict[str, AtomicMotion] = {}
        self._actual_durations: Dict[str, float] = {}  # execution_id -> duration_seconds
    
    def register_motion(self, atomic_motion: AtomicMotion) -> None:
        """
        Register an AtomicMotion for tracking.
        
        Args:
            atomic_motion: The AtomicMotion to track
        """
        # Motion will be associated with execution_id when started
        pass
    
    def track_motion_started(self, motion_id: str, atomic_motion: AtomicMotion) -> None:
        """
        Associate motion_id with AtomicMotion and update state.
        
        Args:
            motion_id: Execution motion ID from MotionStarted event
            atomic_motion: The AtomicMotion entity
        """
        atomic_motion.start(motion_id)
        self._motion_by_execution_id[motion_id] = atomic_motion
    
    def track_motion_completed(
        self,
        motion_id: str,
        duration_seconds: float
    ) -> Optional[AtomicMotion]:
        """
        Update motion state and record actual duration.
        
        Args:
            motion_id: Execution motion ID from MotionCompleted event
            duration_seconds: Actual duration in seconds
            
        Returns:
            AtomicMotion if found, None otherwise
        """
        atomic_motion = self._motion_by_execution_id.get(motion_id)
        if atomic_motion:
            atomic_motion.complete()
            self._actual_durations[motion_id] = duration_seconds
            
            # Log completion with comparison
            estimated_ms = atomic_motion.estimated_duration_seconds * 1000
            actual_ms = duration_seconds * 1000
            diff_ms = actual_ms - estimated_ms
            diff_pct = (diff_ms / estimated_ms * 100) if estimated_ms > 0 else 0
            print(f"[AtomicMotion] Motion ID={str(atomic_motion.id)[:8]}... COMPLETED | "
                  f"duration: estimated={estimated_ms:.1f}ms, actual={actual_ms:.1f}ms "
                  f"(diff={diff_ms:+.1f}ms, {diff_pct:+.1f}%)")
        return atomic_motion
    
    def track_motion_failed(self, motion_id: str, error: str) -> Optional[AtomicMotion]:
        """
        Update motion state to failed.
        
        Args:
            motion_id: Execution motion ID from MotionFailed event
            error: Error message
            
        Returns:
            AtomicMotion if found, None otherwise
        """
        atomic_motion = self._motion_by_execution_id.get(motion_id)
        if atomic_motion:
            atomic_motion.fail(error)
            print(f"[AtomicMotion] Motion ID={str(atomic_motion.id)[:8]}... FAILED | error: {error}")
        return atomic_motion
    
    def get_motion_by_execution_id(self, motion_id: str) -> Optional[AtomicMotion]:
        """
        Get AtomicMotion by execution motion ID.
        
        Args:
            motion_id: Execution motion ID
            
        Returns:
            AtomicMotion if found, None otherwise
        """
        return self._motion_by_execution_id.get(motion_id)
    
    def get_actual_duration(self, motion_id: str) -> Optional[float]:
        """
        Get actual duration for a motion.
        
        Args:
            motion_id: Execution motion ID
            
        Returns:
            Actual duration in seconds, or None if not completed
        """
        return self._actual_durations.get(motion_id)
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Get statistics about tracked motions.
        
        Returns:
            Dictionary with statistics:
            - total_motions: Total number of tracked motions
            - completed_count: Number of completed motions
            - failed_count: Number of failed motions
            - pending_count: Number of pending motions
            - executing_count: Number of executing motions
        """
        total = len(self._motion_by_execution_id)
        completed = sum(
            1 for m in self._motion_by_execution_id.values()
            if m.execution_state == MotionState.COMPLETED
        )
        failed = sum(
            1 for m in self._motion_by_execution_id.values()
            if m.execution_state == MotionState.FAILED
        )
        pending = sum(
            1 for m in self._motion_by_execution_id.values()
            if m.execution_state == MotionState.PENDING
        )
        executing = sum(
            1 for m in self._motion_by_execution_id.values()
            if m.execution_state == MotionState.EXECUTING
        )
        
        return {
            "total_motions": total,
            "completed_count": completed,
            "failed_count": failed,
            "pending_count": pending,
            "executing_count": executing
        }

