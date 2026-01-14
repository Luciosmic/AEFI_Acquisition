"""
Arcus Performax 4EX Controller - Infrastructure Layer

Responsibility:
- Low-level hardware communication with Arcus Performax 4EX motor controller
- Direct interface to pylablib Arcus device
- Hardware-specific operations (homing, position, speed)

Rationale:
- Encapsulates pylablib dependency
- Provides clean API for adapter layer
- Handles hardware initialization and configuration

Design:
- Single Responsibility: Hardware communication only
- No domain logic
- Used by ArcusAdapter to implement IMotionPort
- QCS organization: Setup / Commands / Queries
"""

import os
import time
import threading
from typing import Optional, List, Dict
from dataclasses import dataclass


@dataclass
class AxisParams:
    """Hardware parameters for a single axis."""
    ls: int  # Low speed (Hz)
    hs: int  # High speed (Hz)
    acc: int  # Acceleration (ms)
    dec: int  # Deceleration (ms)


class ArcusPerformax4EXController:
    """
    Low-level controller for Arcus Performax 4EX motor controller.
    Wraps pylablib Arcus device with clean API.
    
    Organization: QCS (Query-Command-Setup)
    - Setup: Connection, initialization
    - Commands: Actions that change state (move, home, stop)
    - Queries: Read-only operations (position, status, is_moving)
    
    Thread Safety:
    - Uses RLock to protect access to the underlying _stage object.
    """
    
    # Default parameters
    DEFAULT_PARAMS = {
        "X": AxisParams(ls=10, hs=1500, acc=300, dec=300),
        "Y": AxisParams(ls=10, hs=1500, acc=300, dec=300)
    }
    
    # ============================================================================
    # SETUP - Initialization & Configuration
    # ============================================================================
    
    def __init__(self, dll_path: Optional[str] = None):
        """
        Initialize controller.
        
        Args:
            dll_path: Path to Arcus DLL folder. If None, auto-detect.
        """
        self._stage = None
        self._dll_path = dll_path
        self._axis_mapping = {"x": 0, "y": 1, "z": 2, "u": 3}
        self._is_homed = {"x": False, "y": False}
        self._lock = threading.RLock()
        
    def connect(self, port: Optional[str] = None) -> bool:
        """
        Connect to Arcus controller.
        
        Args:
            port: Serial port (e.g., 'COM3'). If None, auto-detect.
            
        Returns:
            True if connection successful
        """
        with self._lock:
            try:
                import pylablib as pll
                from pylablib.devices import Arcus
                
                # Set DLL path if provided
                if self._dll_path and os.path.isdir(self._dll_path):
                    pll.par["devices/dlls/arcus_performax"] = self._dll_path
                
                # Connect to stage
                if port:
                    self._stage = Arcus.Performax4EXStage(conn=port)
                else:
                    self._stage = Arcus.Performax4EXStage()
                
                # Enable axes
                self._stage.enable_axis("x")
                self._stage.enable_axis("y")
                
                # Apply default parameters
                self._apply_default_params()
                
                # Check homing status from hardware
                self._initialize_homing_status()
                
                return True
            except Exception as e:
                print(f"[ArcusController] Connection failed: {e}")
                return False
    
    def disconnect(self) -> None:
        """Close connection to controller."""
        with self._lock:
            if self._stage:
                self._stage.close()
                self._stage = None
    
    def _apply_default_params(self) -> None:
        """
        Apply default speed parameters.

        Simplified: we only apply the default high speed (HS) on all axes,
        and leave LS/ACC/DEC to their controller defaults for now.
        """
        default_hs = self.DEFAULT_PARAMS["X"].hs
        self.set_speed(default_hs)
    
    def _initialize_homing_status(self) -> None:
        """Initialize homing status from hardware limit switches."""
        for axis in ["x", "y"]:
            try:
                status = self._stage.get_status(axis)
                # If at negative limit switch, consider as homed
                if 'sw_minus_lim' in status:
                    self._is_homed[axis] = True
            except:
                pass
        print(f"[ArcusController] Homing status initialized: {self._is_homed}")
    
    def set_axis_params(self, axis: str, ls: Optional[int] = None, hs: Optional[int] = None, 
                       acc: Optional[int] = None, dec: Optional[int] = None) -> Dict[str, int]:
        """
        Configure speed parameters for a specific axis.
        Adapted from legacy ArcusPerformax4EXStage_Controller.py.
        
        Args:
            axis: 'x' or 'y'
            ls: Low speed (Hz)
            hs: High speed (Hz)
            acc: Acceleration (ms)
            dec: Deceleration (ms)
            
        Returns:
            Dictionary of effectively applied parameters
        """
        with self._lock:
            if not self._stage:
                raise RuntimeError("Not connected")

            axis_letter = axis.upper()
            
            # Get current parameters to ensure we don't overwrite with defaults if not specified
            # (Though in this implementation we only send what is specified)
            
            # Apply parameters with delays for stability (as per legacy driver)
            if ls is not None:
                self._stage.query(f"LS{axis_letter}={int(ls)}")
                time.sleep(0.1)
                
            if hs is not None:
                self._stage.query(f"HS{axis_letter}={int(hs)}")
                time.sleep(0.1)
                
            if acc is not None:
                self._stage.query(f"ACC{axis_letter}={int(acc)}")
                time.sleep(0.1)
                
            if dec is not None:
                self._stage.query(f"DEC{axis_letter}={int(dec)}")
                time.sleep(0.1)
                
            # Verify applied parameters
            return self.get_axis_params_dict(axis)

    def get_axis_params_dict(self, axis: str) -> Dict[str, int]:
        """Get axis parameters as a dictionary."""
        with self._lock:
            if not self._stage:
                raise RuntimeError("Not connected")
                
            axis_upper = axis.upper()
            return {
                "ls": int(self._stage.query(f"LS{axis_upper}")),
                "hs": int(self._stage.query(f"HS{axis_upper}")),
                "acc": int(self._stage.query(f"ACC{axis_upper}")),
                "dec": int(self._stage.query(f"DEC{axis_upper}"))
            }

    def set_speed(self, hs: int, axis: Optional[str] = None) -> None:
        """Legacy compatibility wrapper for set_axis_params."""
        target_axes = ["x", "y"] if axis is None else [axis.lower()]
        for ax in target_axes:
            self.set_axis_params(ax, hs=hs)

    def set_low_speed(self, ls: int, axis: Optional[str] = None) -> None:
        """Legacy compatibility wrapper for set_axis_params."""
        target_axes = ["x", "y"] if axis is None else [axis.lower()]
        for ax in target_axes:
            self.set_axis_params(ax, ls=ls)

    def set_acceleration(self, acc: int, axis: Optional[str] = None) -> None:
        """Legacy compatibility wrapper for set_axis_params."""
        target_axes = ["x", "y"] if axis is None else [axis.lower()]
        for ax in target_axes:
            self.set_axis_params(ax, acc=acc)

    def set_deceleration(self, dec: int, axis: Optional[str] = None) -> None:
        """Legacy compatibility wrapper for set_axis_params."""
        target_axes = ["x", "y"] if axis is None else [axis.lower()]
        for ax in target_axes:
            self.set_axis_params(ax, dec=dec)

    
    # ============================================================================
    # COMMANDS - Actions that modify state
    # ============================================================================
    
    def home(self, axis: str, blocking: bool = True, timeout: float = 120.0) -> None:
        """
        Home the specified axis.
        
        Args:
            axis: 'x' or 'y'
            blocking: If True, wait for homing to complete
            timeout: Maximum time to wait (seconds)
            
        Raises:
            RuntimeError: If not connected or homing fails
        """
        with self._lock:
            if not self._stage:
                raise RuntimeError("Not connected")
            
            axis_lower = axis.lower()
            
            print(f"[ArcusController] Homing {axis.upper()} (direction -)...")
            self._stage.home(axis_lower, direction="-", home_mode="only_home_input")
            
            if blocking:
                print(f"[ArcusController] Waiting for {axis.upper()} homing to complete...")
                self._stage.wait_move(axis_lower, timeout=timeout)
                self._stage.set_position_reference(axis_lower, 0)
                self._is_homed[axis_lower] = True
                print(f"[ArcusController] {axis.upper()} homed. Position set to 0.")
    
    def home_both(self, blocking: bool = True, timeout: float = 120.0) -> None:
        """
        Home both X and Y axes simultaneously.
        
        Args:
            blocking: If True, wait for both axes to complete
            timeout: Maximum time to wait per axis (seconds)
        """
        with self._lock:
            if not self._stage:
                raise RuntimeError("Not connected")
            
            print("[ArcusController] Homing X and Y simultaneously...")
            self._stage.home('x', direction='-', home_mode='only_home_input')
            self._stage.home('y', direction='-', home_mode='only_home_input')
            
            if blocking:
                print("[ArcusController] Waiting for both axes...")
                self._stage.wait_move('x', timeout=timeout)
                self._stage.wait_move('y', timeout=timeout)
                self._stage.set_position_reference('x', 0)
                self._stage.set_position_reference('y', 0)
                self._is_homed['x'] = True
                self._is_homed['y'] = True
                print("[ArcusController] Both axes homed. Positions set to 0.")
    
    def set_homed(self, axis: str, value: bool = True) -> None:
        """Manually set homing status (for testing/recovery)."""
        self._is_homed[axis.lower()] = value
    
    def move_to(self, axis: str, position: float) -> None:
        """
        Move axis to absolute position.
        
        Args:
            axis: 'x' or 'y'
            position: Target position (steps/increments)
            
        Raises:
            RuntimeError: If not homed or not connected
        """
        with self._lock:
            if not self._stage:
                raise RuntimeError("Not connected")
            
            axis_lower = axis.lower()
            
            # Check homing
            if not self._is_homed[axis_lower]:
                raise RuntimeError(f"Axis {axis.upper()} must be homed before movement")
            
            print(f"[ArcusController] DEBUG: Moving {axis.upper()} to position {position}")
            self._stage.move_to(axis_lower, position)
    
    def move_by(self, axis: str, displacement: float) -> None:
        """
        Move axis by relative displacement.
        
        Args:
            axis: 'x' or 'y'
            displacement: Relative displacement (steps)
        """
        with self._lock:
            if not self._stage:
                raise RuntimeError("Not connected")
            
            axis_lower = axis.lower()
            
            if not self._is_homed[axis_lower]:
                raise RuntimeError(f"Axis {axis.upper()} must be homed before movement")
            
            self._stage.move_by(axis_lower, displacement)
    
    def stop(self, axis: str, immediate: bool = False) -> None:
        """
        Stop axis motion.
        
        Args:
            axis: 'x' or 'y'
            immediate: If True, abrupt stop (ABORT). If False, gradual (STOP).
        """
        with self._lock:
            if not self._stage:
                raise RuntimeError("Not connected")
            
            command = "ABORT" if immediate else "STOP"
            self._stage.query(f"{command}{axis.upper()}")
    
    def wait_move(self, axis: str, timeout: Optional[float] = None) -> None:
        """
        Wait for axis to stop moving.
        
        Args:
            axis: 'x' or 'y'
            timeout: Maximum time to wait (seconds)
        """
        with self._lock:
            if not self._stage:
                raise RuntimeError("Not connected")
            
            self._stage.wait_move(axis.lower(), timeout=timeout)
    
    def set_position_reference(self, axis: str, position: float = 0) -> None:
        """
        Set current position as reference.
        
        Args:
            axis: 'x' or 'y'
            position: Reference value (default 0)
        """
        with self._lock:
            if not self._stage:
                raise RuntimeError("Not connected")
            
            self._stage.set_position_reference(axis.lower(), position)
    
    # ============================================================================
    # QUERIES - Read-only operations
    # ============================================================================
    
    def is_connected(self) -> bool:
        """Check if controller is connected."""
        with self._lock:
            if not self._stage:
                return False
            try:
                return self._stage.is_opened()
            except:
                return False
    
    def is_homed(self, axis: str) -> bool:
        """
        Check if axis has been homed.
        
        Args:
            axis: 'x' or 'y'
            
        Returns:
            True if axis is homed
        """
        return self._is_homed[axis.lower()]
    
    def is_moving(self, axis: Optional[str] = None) -> bool:
        """
        Check if axis is moving.
        
        Args:
            axis: 'x', 'y', or None for both
            
        Returns:
            True if moving
        """
        with self._lock:
            if not self._stage:
                return False
            
            moving = self._stage.is_moving()
            
            if axis is None:
                return moving[0] or moving[1]  # X or Y
            else:
                axis_idx = self._axis_mapping[axis.lower()]
                return moving[axis_idx]
    
    def get_position(self, axis: str) -> float:
        """
        Get current position of axis.
        
        Args:
            axis: 'x' or 'y'
            
        Returns:
            Current position (steps/increments)
        """
        with self._lock:
            if not self._stage:
                raise RuntimeError("Not connected")
            
            return self._stage.get_position(axis.lower())
    
    def get_axis_params(self, axis: str) -> AxisParams:
        """
        Get current axis parameters.
        
        Args:
            axis: 'x' or 'y'
            
        Returns:
            AxisParams with current settings
        """
        with self._lock:
            if not self._stage:
                raise RuntimeError("Not connected")
            
            axis_upper = axis.upper()
            
            ls = int(self._stage.query(f"LS{axis_upper}"))
            hs = int(self._stage.query(f"HS{axis_upper}"))
            acc = int(self._stage.query(f"ACC{axis_upper}"))
            dec = int(self._stage.query(f"DEC{axis_upper}"))
            
            return AxisParams(ls=ls, hs=hs, acc=acc, dec=dec)
    
    def get_status(self, axis: str) -> List[str]:
        """
        Get axis status flags.
        
        Args:
            axis: 'x' or 'y'
            
        Returns:
            List of status strings (e.g., ['sw_minus_lim', 'enabled'])
        """
        with self._lock:
            if not self._stage:
                raise RuntimeError("Not connected")
            
            return self._stage.get_status(axis.lower())
