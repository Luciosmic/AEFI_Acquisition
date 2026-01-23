"""
PrimaryFieldPhaseCalibrator - Calibrates phase using a reference point.
Rotates the entire field such that the reference point becomes In-Phase (Q=0),
while preserving the sign of the In-Phase component.
"""

from typing import Tuple, Optional, List
import numpy as np


class PrimaryFieldPhaseCalibrator:
    """
    Calibrates phase by zeroing the quadrature component at a reference point.
    Applies global rotation to the entire dataset.
    Preserves the sign of the In-Phase component at the reference point.
    """
    
    def __init__(self, border_width: int = 1):
        """
        Initialize phase calibrator.
        Args:
            border_width: Deprecated, kept for backward compatibility.
        """
        self.border_width = border_width
    
    def get_reference_values(self, data: np.ndarray, ref_idx: Tuple[int, int]) -> np.ndarray:
        """
        Extract vector at reference point.
        Args:
            data: Input data (H, W, C)
            ref_idx: (y_index, x_index)
        Returns:
            Reference vector (C,)
        """
        y, x = ref_idx
        if y >= data.shape[0] or x >= data.shape[1]:
             raise ValueError(f"Reference index {ref_idx} out of bounds for shape {data.shape}")
        return data[y, x, :]

    def calculate_phase_correction(
        self, 
        ref_vector: np.ndarray, 
        axis_pairs: Optional[List[Tuple[int, int]]] = None
    ) -> dict:
        """
        Calculate rotation setup for each axis to zero Q at reference.
        
        Args:
            ref_vector: Vector at reference point (C,)
            axis_pairs: List of (I, Q) indices
            
        Returns:
            Dictionary mapping axis name to:
            {
                'theta': float (rotation angle),
                'flip_sign': bool (whether to flip sign after rotation)
            }
        """
        if axis_pairs is None:
            axis_pairs = [(0, 1), (2, 3), (4, 5)]
            axis_names = ['x', 'y', 'z']
        else:
            axis_names = [f'axis_{i}' for i in range(len(axis_pairs))]
            
        corrections = {}
        
        for axis_name, (i_idx, q_idx) in zip(axis_names, axis_pairs):
            if i_idx >= len(ref_vector) or q_idx >= len(ref_vector):
                continue
                
            i_val = ref_vector[i_idx]
            q_val = ref_vector[q_idx]
            
            if np.isnan(i_val) or np.isnan(q_val):
                corrections[axis_name] = {'theta': 0.0, 'flip_sign': False}
                continue
            
            # Calculate angle of the vector
            theta = np.arctan2(q_val, i_val)
            
            # Predict I value after rotation by -theta
            # I_rotated = I_original * cos(-theta) - Q_original * sin(-theta) (standard vector rot)
            # Actually, we rotate the BASIS by -theta, or the VECTOR by -theta to align with I axis?
            # Goal: Make Q_new = 0.
            # If V = |V| * exp(j*theta), multiplying by exp(-j*theta) gives |V|.
            # So we rotate vector by -theta.
            # Resulting I should be |V| (positive).
            
            # Logic:
            # If original I was negative, we want final I to be negative.
            # But standard rotation to zero phase gives positive modulus.
            # So we flag to flip sign if original I < 0.
            # Edge case: If I=0, sign is ambiguous, usually check Q direction, but let's stick to I < 0.
            
            flip_sign = False
            if i_val < 0:
                flip_sign = True
            elif i_val == 0 and q_val != 0:
                # If pure quadrature, decide based on Q? 
                # signal_processor.py uses Q sign if I=0.
                # If Q > 0 (Up), I becomes > 0. If Q < 0 (Down), I becomes > 0 (magnitude).
                # Wait, signal processor says:
                # "Q < 0 means vector pointing 'down' -> negative I after rotation"
                # If we consider 'Up' as positive I direction?? No.
                # Let's trust simpler logic: if magnitude is |V|, we want to preserve "direction".
                # But "direction" is circular.
                # Let's essentially say: We rotate the vector to the NEAREST real axis.
                # If vector is close to -I axis (e.g. 170 deg), we rotate by small angle to -I.
                # vs rotating by large angle to +I.
                pass 
                
            corrections[axis_name] = {
                'theta': theta,
                'flip_sign': flip_sign
            }
            
        return corrections

    def apply_phase_rotation(
        self, 
        data: np.ndarray, 
        corrections: dict,
        axis_pairs: Optional[List[Tuple[int, int]]] = None
    ) -> np.ndarray:
        """
        Apply phase rotation and sign flip.
        """
        if axis_pairs is None:
            axis_pairs = [(0, 1), (2, 3), (4, 5)]
            axis_names = ['x', 'y', 'z']
        else:
            axis_names = [f'axis_{i}' for i in range(len(axis_pairs))]
            
        rotated = data.copy()
        
        for axis_name, (i_idx, q_idx) in zip(axis_names, axis_pairs):
            if axis_name not in corrections:
                continue
                
            params = corrections[axis_name]
            theta = params['theta']
            flip_sign = params['flip_sign']
            
            # Rotate by -theta
            # I_new = I * cos(theta) + Q * sin(theta)
            # Q_new = -I * sin(theta) + Q * cos(theta)
            
            i_vals = data[:, :, i_idx]
            q_vals = data[:, :, q_idx]
            
            cos_t = np.cos(theta)
            sin_t = np.sin(theta)
            
            i_new = i_vals * cos_t + q_vals * sin_t
            q_new = -i_vals * sin_t + q_vals * cos_t
            
            if flip_sign:
                i_new = -i_new
                q_new = -q_new # Flip Q too? Q should be ~0. But mathematically yes, flip vector.
            
            rotated[:, :, i_idx] = i_new
            rotated[:, :, q_idx] = q_new
            
        return rotated

    def calibrate(
        self, 
        data: np.ndarray,
        reference_idx: Tuple[int, int] = (0, 0),
        axis_pairs: Optional[list] = None
    ) -> Tuple[np.ndarray, dict]:
        """
        Execute calibration using reference point.
        """
        # 1. Get reference vector
        ref_vec = self.get_reference_values(data, reference_idx)
        
        # 2. Calculate corrections
        corrections = self.calculate_phase_correction(ref_vec, axis_pairs)
        
        # 3. Apply
        calibrated = self.apply_phase_rotation(data, corrections, axis_pairs)
        
        # Format phases for metadata (just the angle)
        phases_meta = {k: v['theta'] for k, v in corrections.items()}
        
        return calibrated, phases_meta
