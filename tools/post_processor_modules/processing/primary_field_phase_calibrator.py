"""
PrimaryFieldPhaseCalibrator - Calibrates phase using border reference points.
Extracts mean phase from image borders and rotates to cancel quadrature signal.
Adapted from signal_processor.py.
"""

from typing import Tuple, Optional
import numpy as np


class PrimaryFieldPhaseCalibrator:
    """
    Calibrates phase by using border pixels as reference points.
    Calculates mean phase angle at borders and applies rotation to cancel
    quadrature component for reference points.
    """
    
    def __init__(self, border_width: int = 1):
        """
        Initialize phase calibrator.
        
        Args:
            border_width: Width of border in pixels to use as reference
        """
        self.border_width = border_width
    
    def extract_border_pixels(self, data: np.ndarray) -> np.ndarray:
        """
        Extract border pixels from the data grid.
        
        Args:
            data: Input data array, shape (H, W, C) or (H, W)
            
        Returns:
            Array of border pixel values
        """
        if len(data.shape) == 2:
            # 2D array - add channel dimension
            data = data[:, :, np.newaxis]
        
        h, w, c = data.shape
        bw = self.border_width
        
        # Extract borders (top, bottom, left, right)
        top = data[:bw, :, :]
        bottom = data[-bw:, :, :]
        left = data[bw:-bw, :bw, :]  # Exclude corners already in top/bottom
        right = data[bw:-bw, -bw:, :]
        
        # Concatenate all border pixels
        border = np.concatenate([
            top.reshape(-1, c),
            bottom.reshape(-1, c),
            left.reshape(-1, c),
            right.reshape(-1, c)
        ], axis=0)
        
        return border
    
    def calculate_mean_phase(self, border_data: np.ndarray, axis_pairs: Optional[list] = None) -> dict:
        """
        Calculate mean phase angle for each axis from border data.
        
        Args:
            border_data: Border pixels, shape (N, C) where C is number of channels
            axis_pairs: List of (in_phase_idx, quadrature_idx) tuples for each axis.
                       If None, assumes standard 6-channel layout: [(0,1), (2,3), (4,5)]
            
        Returns:
            Dictionary mapping axis name to phase angle in radians
        """
        if axis_pairs is None:
            # Standard layout: X(I,Q), Y(I,Q), Z(I,Q)
            axis_pairs = [(0, 1), (2, 3), (4, 5)]
            axis_names = ['x', 'y', 'z']
        else:
            axis_names = [f'axis_{i}' for i in range(len(axis_pairs))]
        
        phase_angles = {}
        
        for axis_name, (i_idx, q_idx) in zip(axis_names, axis_pairs):
            # Extract I and Q components
            i_vals = border_data[:, i_idx]
            q_vals = border_data[:, q_idx]
            
            # Remove NaN values
            mask = ~(np.isnan(i_vals) | np.isnan(q_vals))
            i_vals = i_vals[mask]
            q_vals = q_vals[mask]
            
            if len(i_vals) == 0:
                # No valid data
                phase_angles[axis_name] = 0.0
                continue
            
            # Calculate phase angle for each point
            phases = np.arctan2(q_vals, i_vals)
            
            # Mean phase (circular mean would be more accurate, but simple mean works for small angles)
            mean_phase = np.mean(phases)
            
            phase_angles[axis_name] = mean_phase
        
        return phase_angles
    
    def apply_phase_rotation(
        self, 
        data: np.ndarray, 
        phase_angles: dict,
        axis_pairs: Optional[list] = None
    ) -> np.ndarray:
        """
        Apply phase rotation to cancel quadrature component.
        
        Rotation matrix for angle θ:
        [I']   [cos(θ)  sin(θ)] [I]
        [Q'] = [-sin(θ) cos(θ)] [Q]
        
        Args:
            data: Input data, shape (H, W, C)
            phase_angles: Dictionary mapping axis name to phase angle
            axis_pairs: List of (in_phase_idx, quadrature_idx) tuples
            
        Returns:
            Phase-corrected data
        """
        if axis_pairs is None:
            axis_pairs = [(0, 1), (2, 3), (4, 5)]
            axis_names = ['x', 'y', 'z']
        else:
            axis_names = [f'axis_{i}' for i in range(len(axis_pairs))]
        
        # Work on a copy
        rotated = data.copy()
        
        for axis_name, (i_idx, q_idx) in zip(axis_names, axis_pairs):
            theta = phase_angles.get(axis_name, 0.0)
            
            # Extract I and Q
            i_vals = data[:, :, i_idx]
            q_vals = data[:, :, q_idx]
            
            # Apply rotation by -theta to bring vector to I-axis
            # (We rotate by -theta to cancel the phase offset)
            cos_t = np.cos(theta)
            sin_t = np.sin(theta)
            
            i_new = i_vals * cos_t + q_vals * sin_t
            q_new = -i_vals * sin_t + q_vals * cos_t
            
            rotated[:, :, i_idx] = i_new
            rotated[:, :, q_idx] = q_new
        
        return rotated
    
    def calibrate(
        self, 
        data: np.ndarray,
        axis_pairs: Optional[list] = None
    ) -> Tuple[np.ndarray, dict]:
        """
        Complete phase calibration pipeline.
        
        Args:
            data: Input data, shape (H, W, C)
            axis_pairs: Optional axis pair indices
            
        Returns:
            Tuple of (calibrated data, phase angles dict)
        """
        # Extract border pixels
        border = self.extract_border_pixels(data)
        
        # Calculate mean phase
        phase_angles = self.calculate_mean_phase(border, axis_pairs)
        
        # Apply rotation
        calibrated = self.apply_phase_rotation(data, phase_angles, axis_pairs)
        
        return calibrated, phase_angles
