"""
Mock FlyScan Executor - Infrastructure Layer

Responsibility:
- Simulate fly scan execution for testing
- Generate realistic acquisition data during continuous motion
- Simulate load conditions and race conditions for exhaustive testing
"""

import threading
import time
import queue
import random
import math
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field

from src.application.services.scan_application_service.ports.i_fly_scan_executor import IFlyScanExecutor
from application.services.motion_control_service.i_motion_port import IMotionPort
from src.application.services.scan_application_service.ports.i_acquisition_port import IAcquisitionPort
from domain.models.scan.aggregates.fly_scan import FlyScan
from domain.models.scan.entities.atomic_motion import AtomicMotion
from domain.models.scan.value_objects.fly_scan_config import FlyScanConfig
from domain.models.scan.value_objects.scan_point_result import ScanPointResult
from domain.shared.value_objects.position_2d import Position2D


@dataclass
class MockFlyScanExecutorConfig:
    """
    Configuration for MockFlyScanExecutor to control load simulation.
    
    Attributes:
        jitter_percent: Percentage of jitter in acquisition delays (0.0-1.0)
                       Adds random variation: delay * (1 ± jitter_percent)
        cpu_load_probability: Probability (0.0-1.0) of adding CPU load per acquisition
        cpu_load_duration_ms: Duration of CPU load spikes in milliseconds
        acquisition_rate_multiplier: Multiplier for acquisition rate (1.0 = normal, >1.0 = faster)
                                     Can be used to force race conditions by generating more points
        system_latency_ms: Base system latency (network/IO) in milliseconds (0.0 = no latency)
        system_latency_jitter_ms: Random variation in system latency (0.0 = constant latency)
        acquisition_latency_ms: Base acquisition latency (microcontroller request/response) in milliseconds
                                Default: 15.0ms (realistic MCU communication delay)
        acquisition_latency_jitter_ms: Random variation in acquisition latency (0.0 = constant latency)
                                      Default: 5.0ms (simulates communication variability)
        force_points_override: If > 0, override calculated positions to generate exactly this many points
                              Useful for forcing race conditions (generate more than expected_points)
        acquisition_rate_variation_percent: Variation in acquisition rate over time (0.0-1.0)
                                           Simulates real hardware rate fluctuations
        enable_statistics: Whether to track execution statistics
    """
    jitter_percent: float = 0.0  # No jitter by default
    cpu_load_probability: float = 0.0  # No CPU load by default
    cpu_load_duration_ms: float = 0.0
    acquisition_rate_multiplier: float = 1.0  # Normal rate by default
    system_latency_ms: float = 0.0  # No system latency by default
    system_latency_jitter_ms: float = 0.0  # No latency jitter by default
    acquisition_latency_ms: float = 15.0  # Realistic MCU communication delay (15ms)
    acquisition_latency_jitter_ms: float = 5.0  # Communication variability (5ms)
    force_points_override: int = 0  # 0 = use calculated positions, >0 = force exact count
    acquisition_rate_variation_percent: float = 0.0  # No rate variation by default
    enable_statistics: bool = False


class MockFlyScanExecutor(IFlyScanExecutor):
    """
    Mock implementation of fly scan executor for testing.

    Simulates continuous motion and acquisition without real hardware.
    Can simulate load conditions and race conditions for exhaustive testing.
    
    Thread Safety:
    - Captures exceptions from daemon threads for test verification
    - Uses error queue to expose thread exceptions to test code
    - Supports synchronization events for test coordination
    
    Load Simulation:
    - Jitter in acquisition delays (realistic timing variations)
    - CPU load spikes (simulates system load with configurable probability)
    - System latency simulation (network/IO delays)
    - Acquisition latency simulation (MCU request/response: 15ms ± 5ms by default)
    - Acquisition rate variation (simulates hardware rate fluctuations)
    - Configurable acquisition rate multiplier (force race conditions)
    - Force points override (generate exact number of points for race condition testing)
    
    Statistics:
    - Tracks points generated vs added (race condition detection)
    - Monitors timing variations (jitter, delays)
    - Records CPU load events
    - Tracks acquisition rate variations
    """

    def __init__(self, config: Optional[MockFlyScanExecutorConfig] = None, event_bus=None):
        self._config = config or MockFlyScanExecutorConfig()
        self._event_bus = event_bus  # Event bus for publishing domain events
        self._worker_thread: threading.Thread = None
        self._stop_flag = threading.Event()
        # Queue to capture exceptions from daemon thread (for test verification)
        self._error_queue: queue.Queue = queue.Queue()
        # Statistics tracking
        self._stats: Dict[str, Any] = {
            "total_points_generated": 0,
            "total_points_added": 0,
            "points_rejected_race_condition": 0,
            "cpu_load_spikes": 0,
            "jitter_applied_count": 0,
                "system_latency_applied_count": 0,
                "acquisition_latency_applied_count": 0,
                "min_delay_ms": float('inf'),
                "max_delay_ms": 0.0,
                "min_actual_rate_hz": float('inf'),
                "max_actual_rate_hz": 0.0,
                "acquisition_rate_variations": 0,
            } if self._config.enable_statistics else None
        # Synchronization event for tests (optional)
        self._sync_event: Optional[threading.Event] = None

    def execute(
        self,
        fly_scan: FlyScan,
        motions: List[AtomicMotion],
        config: FlyScanConfig,
        motion_port: IMotionPort,
        acquisition_port: IAcquisitionPort
    ) -> bool:
        """Execute mock fly scan in background thread."""
        # #region agent log
        try:
            with open('/Users/luis/Library/CloudStorage/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/AEFI_Acquisition/.cursor/debug.log', 'a') as f:
                import json
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H1","location":"adapter_mock_fly_scan_executor.py:execute","message":"execute() called","data":{"motions_count":len(motions) if motions else 0,"acquisition_rate_hz":config.desired_acquisition_rate_hz},"timestamp":__import__('time').time()*1000}) + '\n')
        except (PermissionError, OSError):
            pass
        # #endregion
        # Check if thread is already running
        if self._worker_thread and self._worker_thread.is_alive():
            print(f"[MockFlyScanExecutor] Thread already running, cannot start new execution")
            # #region agent log
            try:
                with open('/Users/luis/Library/CloudStorage/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/AEFI_Acquisition/.cursor/debug.log', 'a') as f:
                    import json
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H1","location":"adapter_mock_fly_scan_executor.py:execute","message":"Thread already running - REJECTED","data":{},"timestamp":__import__('time').time()*1000}) + '\n')
            except (PermissionError, OSError):
                pass
            # #endregion
            return False

        # Validate inputs
        if not motions:
            print(f"[MockFlyScanExecutor] No motions provided")
            # #region agent log
            try:
                with open('/Users/luis/Library/CloudStorage/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/AEFI_Acquisition/.cursor/debug.log', 'a') as f:
                    import json
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H1","location":"adapter_mock_fly_scan_executor.py:execute","message":"No motions - REJECTED","data":{},"timestamp":__import__('time').time()*1000}) + '\n')
            except (PermissionError, OSError):
                pass
            # #endregion
            return False

        self._stop_flag.clear()
        self._error_queue = queue.Queue()  # Clear previous errors
        self._worker_thread = threading.Thread(
            target=self._worker,
            args=(fly_scan, motions, config, acquisition_port),
            daemon=True
        )
        self._worker_thread.start()
        # #region agent log
        try:
            with open('/Users/luis/Library/CloudStorage/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/AEFI_Acquisition/.cursor/debug.log', 'a') as f:
                import json
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H1","location":"adapter_mock_fly_scan_executor.py:execute","message":"Worker thread started","data":{"thread_id":self._worker_thread.ident},"timestamp":__import__('time').time()*1000}) + '\n')
        except (PermissionError, OSError):
            pass
        # #endregion
        return True

    def stop(self) -> None:
        """Stop the running fly scan."""
        self._stop_flag.set()
        if self._worker_thread:
            self._worker_thread.join(timeout=2.0)

    def get_thread_errors(self) -> List[Exception]:
        """
        Get all exceptions that occurred in the worker thread.
        
        Returns:
            List of exceptions captured from daemon thread
        """
        errors = []
        while not self._error_queue.empty():
            try:
                errors.append(self._error_queue.get_nowait())
            except queue.Empty:
                break
        return errors

    def get_statistics(self) -> Optional[Dict[str, Any]]:
        """
        Get execution statistics if enabled.
        
        Returns:
            Dictionary with statistics or None if disabled
        """
        return self._stats.copy() if self._stats else None

    def reset_statistics(self) -> None:
        """Reset statistics counters."""
        if self._stats:
            self._stats = {
                "total_points_generated": 0,
                "total_points_added": 0,
                "points_rejected_race_condition": 0,
                "cpu_load_spikes": 0,
                "jitter_applied_count": 0,
                "system_latency_applied_count": 0,
                "acquisition_latency_applied_count": 0,
                "min_delay_ms": float('inf'),
                "max_delay_ms": 0.0,
                "min_actual_rate_hz": float('inf'),
                "max_actual_rate_hz": 0.0,
                "acquisition_rate_variations": 0,
            }

    def set_sync_event(self, event: threading.Event) -> None:
        """
        Set a synchronization event for tests.
        
        The event will be set when the first point is acquired.
        Useful for test synchronization.
        """
        self._sync_event = event

    def _simulate_cpu_load(self) -> None:
        """Simulate CPU load by doing busy work."""
        if self._config.cpu_load_probability > 0 and random.random() < self._config.cpu_load_probability:
            if self._config.cpu_load_duration_ms > 0:
                # Busy wait to simulate CPU load
                end_time = time.time() + (self._config.cpu_load_duration_ms / 1000.0)
                iterations = 0
                while time.time() < end_time:
                    # Do some computation to consume CPU
                    math.sqrt(iterations)
                    iterations += 1
                if self._stats:
                    self._stats["cpu_load_spikes"] += 1

    def _simulate_system_latency(self) -> None:
        """Simulate system latency (network/IO delays)."""
        if self._config.system_latency_ms > 0:
            latency = self._config.system_latency_ms
            if self._config.system_latency_jitter_ms > 0:
                latency += random.uniform(
                    -self._config.system_latency_jitter_ms,
                    self._config.system_latency_jitter_ms
                )
            latency = max(0.0, latency)  # Ensure non-negative
            time.sleep(latency / 1000.0)
            if self._stats:
                self._stats["system_latency_applied_count"] += 1

    def _simulate_acquisition_latency(self) -> None:
        """
        Simulate acquisition latency (microcontroller request/response delay).
        
        Simulates realistic MCU communication:
        - Request sent to microcontroller
        - Processing time on MCU
        - Response received
        Default: 15ms ± 5ms (10-20ms range)
        """
        if self._config.acquisition_latency_ms > 0:
            latency = self._config.acquisition_latency_ms
            if self._config.acquisition_latency_jitter_ms > 0:
                latency += random.uniform(
                    -self._config.acquisition_latency_jitter_ms,
                    self._config.acquisition_latency_jitter_ms
                )
            latency = max(0.0, latency)  # Ensure non-negative
            time.sleep(latency / 1000.0)
            if self._stats:
                self._stats["acquisition_latency_applied_count"] += 1

    def _calculate_acquisition_delay(
        self,
        base_delay_seconds: float,
        current_rate_hz: float
    ) -> float:
        """
        Calculate acquisition delay with jitter, rate variation, and load simulation.
        
        Args:
            base_delay_seconds: Base delay from acquisition rate
            current_rate_hz: Current acquisition rate (may vary)
            
        Returns:
            Actual delay to use (with jitter and rate variation applied)
        """
        # Apply rate variation (simulates hardware rate fluctuations)
        effective_rate_hz = current_rate_hz
        if self._config.acquisition_rate_variation_percent > 0:
            variation_factor = 1.0 + random.uniform(
                -self._config.acquisition_rate_variation_percent,
                self._config.acquisition_rate_variation_percent
            )
            effective_rate_hz = current_rate_hz * variation_factor
            if self._stats:
                self._stats["acquisition_rate_variations"] += 1
                self._stats["min_actual_rate_hz"] = min(
                    self._stats["min_actual_rate_hz"],
                    effective_rate_hz
                )
                self._stats["max_actual_rate_hz"] = max(
                    self._stats["max_actual_rate_hz"],
                    effective_rate_hz
                )
        
        # Calculate delay from effective rate
        delay = 1.0 / effective_rate_hz if effective_rate_hz > 0 else base_delay_seconds
        
        # Apply jitter (random variation in timing)
        if self._config.jitter_percent > 0:
            jitter_factor = 1.0 + random.uniform(
                -self._config.jitter_percent,
                self._config.jitter_percent
            )
            delay = delay * jitter_factor
            if self._stats:
                self._stats["jitter_applied_count"] += 1
                delay_ms = delay * 1000.0
                self._stats["min_delay_ms"] = min(self._stats["min_delay_ms"], delay_ms)
                self._stats["max_delay_ms"] = max(self._stats["max_delay_ms"], delay_ms)
        
        return max(0.0, delay)  # Ensure non-negative

    def _worker(
        self,
        fly_scan: FlyScan,
        motions: List[AtomicMotion],
        config: FlyScanConfig,
        acquisition_port: IAcquisitionPort
    ) -> None:
        """Background worker simulating fly scan execution."""
        # #region agent log
        try:
            with open('/Users/luis/Library/CloudStorage/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/AEFI_Acquisition/.cursor/debug.log', 'a') as f:
                import json
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H2","location":"adapter_mock_fly_scan_executor.py:_worker","message":"Worker thread started","data":{"motions_count":len(motions),"acquisition_rate_hz":config.desired_acquisition_rate_hz,"acquisition_latency_ms":self._config.acquisition_latency_ms},"timestamp":__import__('time').time()*1000}) + '\n')
        except (PermissionError, OSError):
            pass
        # #endregion
        try:
            current_position = Position2D(
                x=config.scan_zone.x_min,
                y=config.scan_zone.y_min
            )
            point_index = 0
            
            # Calculate effective acquisition rate (with multiplier)
            effective_rate_hz = config.desired_acquisition_rate_hz * self._config.acquisition_rate_multiplier
            base_delay = 1.0 / effective_rate_hz if effective_rate_hz > 0 else 0.0

            # Collect all positions if we need to override
            all_positions: List[Position2D] = []
            
            # Execute each motion
            for motion_idx, motion in enumerate(motions):
                if self._stop_flag.is_set():
                    fly_scan.cancel()
                    return

                # Calculate acquisition positions along this motion
                motion_positions = motion.calculate_acquisition_positions(
                    start_position=current_position,
                    acquisition_rate_hz=effective_rate_hz  # Use effective rate
                )
                all_positions.extend(motion_positions)

                # Simulate motion execution
                motion.start(f"mock_motion_{motion_idx}")

                # Update current position
                current_position = Position2D(
                    x=current_position.x + motion.dx,
                    y=current_position.y + motion.dy
                )
                
                # Complete motion
                motion.complete()

            # Override positions if configured (for forcing race conditions)
            if self._config.force_points_override > 0:
                # Generate evenly spaced positions across the scan zone
                # This allows forcing exact number of points regardless of motion calculation
                all_positions = self._generate_forced_positions(
                    config,
                    self._config.force_points_override
                )

            # #region agent log
            try:
                with open('/Users/luis/Library/CloudStorage/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/AEFI_Acquisition/.cursor/debug.log', 'a') as f:
                    import json
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H3","location":"adapter_mock_fly_scan_executor.py:_worker","message":"Starting acquisition loop","data":{"total_positions":len(all_positions),"base_delay":base_delay,"effective_rate_hz":effective_rate_hz},"timestamp":__import__('time').time()*1000}) + '\n')
            except (PermissionError, OSError):
                pass
            # #endregion

            # Acquire samples at all positions
            first_point = True
            print(f"[MockFlyScanExecutor] DEBUG: Starting acquisition loop with {len(all_positions)} positions")
            for idx, position in enumerate(all_positions):
                if self._stop_flag.is_set():
                    print(f"[MockFlyScanExecutor] DEBUG: Stop flag set at position {idx}")
                    fly_scan.cancel()
                    return

                # Check if scan is still active before adding points
                # (scan may have auto-completed when expected_points was reached)
                if not fly_scan.status.is_active():
                    print(f"[MockFlyScanExecutor] DEBUG: Scan no longer active at position {idx}, status={fly_scan.status}")
                    if self._stats:
                        self._stats["points_rejected_race_condition"] += (
                            len(all_positions) - point_index
                        )
                    return
                
                # Debug print every 100 points
                if idx % 100 == 0:
                    print(f"[MockFlyScanExecutor] DEBUG: Processing position {idx}/{len(all_positions)}, point_index={point_index}, scan_status={fly_scan.status}")

                # Simulate system latency (network/IO delays)
                self._simulate_system_latency()

                # Calculate actual delay with jitter and rate variation
                actual_delay = self._calculate_acquisition_delay(
                    base_delay_seconds=base_delay,
                    current_rate_hz=effective_rate_hz
                )
                
                # Apply delay
                time.sleep(actual_delay)

                # Simulate CPU load (random spikes)
                self._simulate_cpu_load()

                # Simulate acquisition latency (MCU request/response delay)
                # This simulates realistic microcontroller communication (15ms ± 5ms)
                # #region agent log
                try:
                    with open('/Users/luis/Library/CloudStorage/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/AEFI_Acquisition/.cursor/debug.log', 'a') as f:
                        import json
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H2","location":"adapter_mock_fly_scan_executor.py:_worker","message":"Before acquisition latency","data":{"point_index":point_index,"position":f"{position.x:.2f},{position.y:.2f}"},"timestamp":__import__('time').time()*1000}) + '\n')
                except (PermissionError, OSError):
                    pass
                # #endregion
                self._simulate_acquisition_latency()

                # Acquire sample
                measurement = acquisition_port.acquire_sample()
                # #region agent log
                try:
                    with open('/Users/luis/Library/CloudStorage/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/AEFI_Acquisition/.cursor/debug.log', 'a') as f:
                        import json
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H2","location":"adapter_mock_fly_scan_executor.py:_worker","message":"After acquisition","data":{"point_index":point_index,"measurement":float(measurement) if hasattr(measurement, '__float__') else str(measurement)},"timestamp":__import__('time').time()*1000}) + '\n')
                except (PermissionError, OSError):
                    pass
                # #endregion

                # Create point result
                point_result = ScanPointResult(
                    point_index=point_index,
                    position=position,
                    measurement=measurement
                )

                # Track statistics
                if self._stats:
                    self._stats["total_points_generated"] += 1

                # Signal first point (for test synchronization)
                if first_point and self._sync_event:
                    self._sync_event.set()
                    first_point = False

                # Add to fly scan (may raise ValueError if scan completed concurrently)
                try:
                    fly_scan.add_point_result(point_result)
                    point_index += 1
                    if self._stats:
                        self._stats["total_points_added"] += 1
                    # #region agent log
                    try:
                        with open('/Users/luis/Library/CloudStorage/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/AEFI_Acquisition/.cursor/debug.log', 'a') as f:
                            import json
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H4","location":"adapter_mock_fly_scan_executor.py:_worker","message":"Point added successfully","data":{"point_index":point_index,"scan_status":str(fly_scan.status),"is_active":fly_scan.status.is_active()},"timestamp":__import__('time').time()*1000}) + '\n')
                    except (PermissionError, OSError):
                        pass
                    # #endregion
                except ValueError as e:
                    # Scan was completed (likely auto-completed when expected_points reached)
                    # This is normal and expected, just stop processing
                    print(f"[MockFlyScanExecutor] DEBUG: ValueError on add_point_result at point_index={point_index}: {e}")
                    print(f"[MockFlyScanExecutor] DEBUG: Scan status={fly_scan.status}, remaining positions={len(all_positions)-point_index}")
                    
                    # Publish any remaining domain events (including ScanCompleted if auto-completed)
                    if self._event_bus:
                        events = fly_scan.domain_events
                        for event in events:
                            event_type = type(event).__name__.lower()
                            self._event_bus.publish(event_type, event)
                    
                    # #region agent log
                    try:
                        with open('/Users/luis/Library/CloudStorage/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/AEFI_Acquisition/.cursor/debug.log', 'a') as f:
                            import json
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H4","location":"adapter_mock_fly_scan_executor.py:_worker","message":"ValueError on add_point_result - scan completed","data":{"point_index":point_index,"error":str(e),"scan_status":str(fly_scan.status),"remaining_positions":len(all_positions)-point_index},"timestamp":__import__('time').time()*1000}) + '\n')
                    except (PermissionError, OSError):
                        pass
                    # #endregion
                    # Track rejected points
                    if self._stats:
                        self._stats["points_rejected_race_condition"] += (
                            len(all_positions) - point_index
                        )
                    print(f"[MockFlyScanExecutor] DEBUG: Returning early due to ValueError - scan already completed")
                    return

            print(f"[MockFlyScanExecutor] DEBUG: Finished acquisition loop! points_added={point_index}, total_positions={len(all_positions)}")
            print(f"[MockFlyScanExecutor] DEBUG: Scan status={fly_scan.status}, is_active={fly_scan.status.is_active()}")
            # #region agent log
            try:
                with open('/Users/luis/Library/CloudStorage/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/AEFI_Acquisition/.cursor/debug.log', 'a') as f:
                    import json
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H4","location":"adapter_mock_fly_scan_executor.py:_worker","message":"Finished acquisition loop","data":{"points_added":point_index,"total_positions":len(all_positions),"scan_status":str(fly_scan.status),"is_active":fly_scan.status.is_active()},"timestamp":__import__('time').time()*1000}) + '\n')
            except (PermissionError, OSError):
                pass
            # #endregion

            # Complete scan
            if fly_scan.status.is_active():
                print(f"[MockFlyScanExecutor] DEBUG: Calling fly_scan.complete()")
                # #region agent log
                try:
                    with open('/Users/luis/Library/CloudStorage/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/AEFI_Acquisition/.cursor/debug.log', 'a') as f:
                        import json
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H4","location":"adapter_mock_fly_scan_executor.py:_worker","message":"Completing scan","data":{"points_added":point_index,"total_positions":len(all_positions)},"timestamp":__import__('time').time()*1000}) + '\n')
                except (PermissionError, OSError):
                    pass
                # #endregion
                fly_scan.complete()
                
                # Publish completion event
                if self._event_bus:
                    events = fly_scan.domain_events
                    for event in events:
                        event_type = type(event).__name__.lower()
                        self._event_bus.publish(event_type, event)
                
                print(f"[MockFlyScanExecutor] DEBUG: fly_scan.complete() called successfully")
            else:
                print(f"[MockFlyScanExecutor] DEBUG: Scan already completed/cancelled, status={fly_scan.status}")
                # #region agent log
                try:
                    with open('/Users/luis/Library/CloudStorage/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/AEFI_Acquisition/.cursor/debug.log', 'a') as f:
                        import json
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H4","location":"adapter_mock_fly_scan_executor.py:_worker","message":"Scan already completed/cancelled","data":{"status":str(fly_scan.status),"points_added":point_index},"timestamp":__import__('time').time()*1000}) + '\n')
                except (PermissionError, OSError):
                    pass
                # #endregion

        except Exception as e:
            print(f"[MockFlyScanExecutor] DEBUG: EXCEPTION in worker: {type(e).__name__}: {e}")
            import traceback
            print(f"[MockFlyScanExecutor] DEBUG: Traceback:\n{traceback.format_exc()}")
            # #region agent log
            try:
                with open('/Users/luis/Library/CloudStorage/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/AEFI_Acquisition/.cursor/debug.log', 'a') as f:
                    import json
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H5","location":"adapter_mock_fly_scan_executor.py:_worker","message":"Exception in worker","data":{"error":str(e),"error_type":type(e).__name__},"timestamp":__import__('time').time()*1000}) + '\n')
            except (PermissionError, OSError):
                pass
            # #endregion
            # Capture exception for test verification
            self._error_queue.put(e)
            # Only fail if scan is still active (not already completed/cancelled)
            if fly_scan.status.is_active():
                try:
                    fly_scan.fail(str(e))
                    print(f"[MockFlyScanExecutor] DEBUG: Called fly_scan.fail()")
                except ValueError as ve:
                    # Scan was already completed/cancelled, ignore
                    print(f"[MockFlyScanExecutor] DEBUG: ValueError on fail() - scan already completed: {ve}")
                    pass
        finally:
            print(f"[MockFlyScanExecutor] DEBUG: Worker thread EXITING, final scan status={fly_scan.status if 'fly_scan' in locals() else 'N/A'}")

    def _generate_forced_positions(
        self,
        config: FlyScanConfig,
        num_points: int
    ) -> List[Position2D]:
        """
        Generate forced positions for race condition testing.
        
        Creates evenly spaced positions across the scan zone.
        """
        positions = []
        width = config.scan_zone.x_max - config.scan_zone.x_min
        height = config.scan_zone.y_max - config.scan_zone.y_min
        
        # Calculate grid dimensions (approximate square grid)
        grid_size = int(math.sqrt(num_points))
        if grid_size * grid_size < num_points:
            grid_size += 1
        
        dx = width / grid_size if grid_size > 1 else 0.0
        dy = height / grid_size if grid_size > 1 else 0.0
        
        for i in range(num_points):
            row = i // grid_size
            col = i % grid_size
            x = config.scan_zone.x_min + col * dx
            y = config.scan_zone.y_min + row * dy
            positions.append(Position2D(x=x, y=y))
        
        return positions
