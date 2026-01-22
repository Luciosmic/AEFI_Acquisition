import math
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional

@dataclass
class ProcessingState:
    """Stores the calibration constants."""
    # Noise Offset (Zero)
    noise_offset: Dict[str, Tuple[float, float]] = field(default_factory=dict) # {axis: (I, Q)}
    noise_correction_enabled: bool = False

    # Phase Correction
    phase_angles: Dict[str, float] = field(default_factory=dict) # {axis: radians}
    phase_correction_enabled: bool = False

    # Primary Field Offset (Tare)
    primary_offset: Dict[str, Tuple[float, float]] = field(default_factory=dict) # {axis: (I, Q)}
    primary_correction_enabled: bool = False

class SignalPostProcessor:
    """
    Encapsulates signal processing logic for the interface.
    Handles Noise Correction -> Phase Alignment -> Primary Field Subtraction.
    """
    
    def __init__(self):
        self.state = ProcessingState()

    def process_sample(self, raw_measurement: Dict[str, float]) -> Dict[str, float]:
        """
        Apply enabled corrections to a raw measurement dictionary.
        Expected keys format: "Ux In-Phase", "Ux Quadrature", etc.
        """
        processed = raw_measurement.copy()
        
        # We process by axis pairs (X, Y, Z)
        axes = ["Ux", "Uy", "Uz"]
        
        for axis in axes:
            k_i = f"{axis} In-Phase"
            k_q = f"{axis} Quadrature"
            
            if k_i not in processed or k_q not in processed:
                continue

            i_val = processed[k_i]
            q_val = processed[k_q]

            # 1. Noise Subtraction
            if self.state.noise_correction_enabled:
                offset_i, offset_q = self.state.noise_offset.get(axis, (0.0, 0.0))
                i_val -= offset_i
                q_val -= offset_q

            # 2. Phase Rotation (Maximize In-Phase)
            if self.state.phase_correction_enabled:
                theta = self.state.phase_angles.get(axis, 0.0)
                # Rotate (I, Q) by -theta to align on I-axis
                # I_new = I cos(-th) - Q sin(-th) = I cos(th) + Q sin(th)
                # Q_new = I sin(-th) + Q cos(-th) = -I sin(th) + Q cos(th)
                
                # Determine expected sign based on original vector quadrant
                # The sign should reflect the quadrant of the original vector (I, Q)
                if i_val != 0.0:
                    expected_sign = 1.0 if i_val >= 0 else -1.0
                else:
                    # When I = 0, sign is determined by Q direction
                    # Q > 0 means vector pointing "up" -> positive I after rotation
                    # Q < 0 means vector pointing "down" -> negative I after rotation
                    expected_sign = 1.0 if q_val >= 0 else -1.0
                
                cos_t = math.cos(theta)
                sin_t = math.sin(theta)
                
                # Perform rotation (preserves magnitude)
                i_rotated = i_val * cos_t + q_val * sin_t
                q_new = -i_val * sin_t + q_val * cos_t
                
                # Preserve sign: if rotated I has wrong sign, correct it
                # This ensures negative signals remain negative after phase correction
                if (i_rotated >= 0) != (expected_sign >= 0):
                    # Sign mismatch: correct by flipping sign while preserving magnitude
                    i_val = -i_rotated
                else:
                    i_val = i_rotated
                q_val = q_new

            # 3. Primary Field Subtraction
            if self.state.primary_correction_enabled:
                offset_i, offset_q = self.state.primary_offset.get(axis, (0.0, 0.0))
                i_val -= offset_i
                q_val -= offset_q

            processed[k_i] = i_val
            processed[k_q] = q_val
            
        return processed

    def calibrate_noise(self, current_sample: Dict[str, float]):
        """Store current values as noise offset."""
        axes = ["Ux", "Uy", "Uz"]
        for axis in axes:
            i = current_sample.get(f"{axis} In-Phase", 0.0)
            q = current_sample.get(f"{axis} Quadrature", 0.0)
            self.state.noise_offset[axis] = (i, q)
        
        self.state.noise_correction_enabled = True

    def calibrate_phase(self, current_sample_pre_phase: Dict[str, float]):
        """
        Calculate angle to rotate (I, Q) onto the I axis (Q=0).
        This should be called AFTER noise subtraction but BEFORE primary subtraction.
        """
        axes = ["Ux", "Uy", "Uz"]
        for axis in axes:
            # Get values (potentially already noise-corrected if passed correctly)
            i = current_sample_pre_phase.get(f"{axis} In-Phase", 0.0)
            q = current_sample_pre_phase.get(f"{axis} Quadrature", 0.0)
            
            # Calculate angle of the vector
            theta = math.atan2(q, i)
            self.state.phase_angles[axis] = theta
            
        self.state.phase_correction_enabled = True

    def calibrate_primary(self, current_sample_fully_processed: Dict[str, float]):
        """Store current values (after noise+phase) as primary offset."""
        axes = ["Ux", "Uy", "Uz"]
        for axis in axes:
            i = current_sample_fully_processed.get(f"{axis} In-Phase", 0.0)
            q = current_sample_fully_processed.get(f"{axis} Quadrature", 0.0)
            self.state.primary_offset[axis] = (i, q)
            
        self.state.primary_correction_enabled = True
    
    def reset_calibration(self):
        """Reset all calibrations."""
        self.state = ProcessingState()
