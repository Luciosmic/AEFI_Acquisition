"""
PrimaryFieldAmplitudeSubtractor - Subtracts primary field using reference point.
Subtracts the signal measured at the reference point from the entire scan.
"""

from typing import Tuple, Optional
import numpy as np


class PrimaryFieldAmplitudeSubtractor:
    """
    Subtracts primary field by subtracting the reference point signal from all data.
    """
    
    def __init__(self, border_width: int = 1):
        """
        Initialize.
        Args:
            border_width: Deprecated, kept for backward compatibility.
        """
        self.border_width = border_width
    
    def get_reference_values(self, data: np.ndarray, ref_idx: Tuple[int, int]) -> np.ndarray:
        """
        Extract vector at reference point.
        """
        y, x = ref_idx
        if y >= data.shape[0] or x >= data.shape[1]:
             raise ValueError(f"Reference index {ref_idx} out of bounds.")
        return data[y, x, :]
    
    def subtract_primary_field(
        self, 
        data: np.ndarray,
        reference_idx: Tuple[int, int] = (0, 0),
        ignore_nan: bool = True # Kept for signature compatibility, unused
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Subtract reference signal from entire grid.
        
        Args:
            data: Input data (H, W, C)
            reference_idx: (y, x) coordinates of primary field reference
            
        Returns:
            Tuple (subtracted_data, reference_vector)
        """
        # Get reference vector
        ref_vec = self.get_reference_values(data, reference_idx)
        
        # Handle potential NaNs in reference
        # If ref is NaN, we probably shouldn't subtract anything (or error out)
        # Let's convert NaN to 0 to be safe, but warn?
        ref_to_subtract = np.nan_to_num(ref_vec, nan=0.0)
        
        # Subtract
        # Broadcast (C,) -> (1, 1, C)
        subtracted = data - ref_to_subtract[np.newaxis, np.newaxis, :]
        
        return subtracted, ref_to_subtract
