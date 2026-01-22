"""
PrimaryFieldAmplitudeSubtractor - Subtracts primary field using border reference.
Calculates mean amplitude at borders (excluding NaN) and subtracts from entire image.
Adapted from signal_processor.py.
"""

from typing import Tuple, Optional
import numpy as np


class PrimaryFieldAmplitudeSubtractor:
    """
    Subtracts primary field amplitude using border pixels as reference.
    Calculates mean amplitude at borders and subtracts from entire image.
    """
    
    def __init__(self, border_width: int = 1):
        """
        Initialize amplitude subtractor.
        
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
    
    def calculate_mean_amplitude(
        self, 
        border_data: np.ndarray, 
        ignore_nan: bool = True
    ) -> np.ndarray:
        """
        Calculate mean amplitude for each channel from border data.
        
        Args:
            border_data: Border pixels, shape (N, C)
            ignore_nan: If True, exclude NaN values from mean calculation
            
        Returns:
            Array of mean values, shape (C,)
        """
        if ignore_nan:
            mean_values = np.nanmean(border_data, axis=0)
        else:
            mean_values = np.mean(border_data, axis=0)
        
        # Replace any NaN results with 0
        mean_values = np.nan_to_num(mean_values, nan=0.0)
        
        return mean_values
    
    def subtract_from_all(self, data: np.ndarray, mean_values: np.ndarray) -> np.ndarray:
        """
        Subtract mean values from entire image.
        
        Args:
            data: Input data, shape (H, W, C)
            mean_values: Mean values to subtract, shape (C,)
            
        Returns:
            Data with mean subtracted
        """
        # Broadcast subtraction across all pixels
        subtracted = data - mean_values[np.newaxis, np.newaxis, :]
        
        return subtracted
    
    def subtract_primary_field(
        self, 
        data: np.ndarray,
        ignore_nan: bool = True
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Complete primary field subtraction pipeline.
        
        Args:
            data: Input data, shape (H, W, C)
            ignore_nan: If True, exclude NaN from mean calculation
            
        Returns:
            Tuple of (subtracted data, mean amplitudes)
        """
        # Extract border pixels
        border = self.extract_border_pixels(data)
        
        # Calculate mean amplitude
        mean_amplitudes = self.calculate_mean_amplitude(border, ignore_nan)
        
        # Subtract from all
        subtracted = self.subtract_from_all(data, mean_amplitudes)
        
        return subtracted, mean_amplitudes
