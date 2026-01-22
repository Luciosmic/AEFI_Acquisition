"""
DataInterpolator - Interpolates data onto finer grids.
Supports multiple interpolation methods and handles NaN values.
"""

from typing import Tuple, Dict, Optional
import numpy as np
from scipy.interpolate import griddata, RectBivariateSpline


class DataInterpolator:
    """
    Interpolates scan data onto finer grids.
    Supports multiple interpolation methods and quality validation.
    """
    
    def __init__(
        self, 
        target_grid_size: Optional[int] = None,
        interpolation_method: str = 'cubic'
    ):
        """
        Initialize interpolator.
        
        Args:
            target_grid_size: Target grid size. If None, determined from data.
            interpolation_method: 'linear', 'cubic', or 'nearest'
        """
        self.target_grid_size = target_grid_size
        self.interpolation_method = interpolation_method
    
    def create_finer_grid(
        self, 
        original_extent: list, 
        factor: int = 2
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create a finer grid based on original extent.
        
        Args:
            original_extent: [x_min, x_max, y_min, y_max]
            factor: Upsampling factor (2 = double resolution)
            
        Returns:
            Tuple of (x_grid, y_grid) meshgrids
        """
        x_min, x_max, y_min, y_max = original_extent
        
        if self.target_grid_size is not None:
            n_points = self.target_grid_size
        else:
            # Estimate from extent and factor
            # Assume original had some grid size, multiply by factor
            n_points = int(100 * factor)  # Default assumption
        
        x_fine = np.linspace(x_min, x_max, n_points)
        y_fine = np.linspace(y_min, y_max, n_points)
        
        x_grid, y_grid = np.meshgrid(x_fine, y_fine)
        
        return x_grid, y_grid
    
    def interpolate_channel(
        self,
        data_2d: np.ndarray,
        x_coords: np.ndarray,
        y_coords: np.ndarray,
        x_grid: np.ndarray,
        y_grid: np.ndarray,
        method: str = 'cubic'
    ) -> np.ndarray:
        """
        Interpolate a single channel.
        
        Args:
            data_2d: 2D data array, shape (H, W)
            x_coords: X coordinates of original grid
            y_coords: Y coordinates of original grid
            x_grid: Target X grid
            y_grid: Target Y grid
            method: Interpolation method
            
        Returns:
            Interpolated data on fine grid
        """
        # Get valid (non-NaN) points
        valid_mask = ~np.isnan(data_2d)
        
        # Create coordinate arrays for valid points
        y_idx, x_idx = np.where(valid_mask)
        
        if len(x_idx) == 0:
            # No valid data, return NaN grid
            return np.full_like(x_grid, np.nan)
        
        # Get coordinates and values
        points_x = x_coords[x_idx]
        points_y = y_coords[y_idx]
        values = data_2d[valid_mask]
        
        # Stack coordinates
        points = np.column_stack([points_x, points_y])
        
        # Interpolate using griddata
        interpolated = griddata(
            points,
            values,
            (x_grid, y_grid),
            method=method,
            fill_value=np.nan
        )
        
        return interpolated
    
    def interpolate_values(
        self,
        data: np.ndarray,
        extent: list,
        method: Optional[str] = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Interpolate all channels to finer grid.
        
        Args:
            data: Input data, shape (H, W, C)
            extent: [x_min, x_max, y_min, y_max]
            method: Interpolation method (overrides default if provided)
            
        Returns:
            Tuple of (interpolated data, x_grid, y_grid)
        """
        if method is None:
            method = self.interpolation_method
        
        h, w, c = data.shape
        
        # Create original coordinate arrays
        x_min, x_max, y_min, y_max = extent
        x_coords = np.linspace(x_min, x_max, w)
        y_coords = np.linspace(y_min, y_max, h)
        
        # Create finer grid
        factor = 2 if self.target_grid_size is None else int(self.target_grid_size / w)
        x_grid, y_grid = self.create_finer_grid(extent, factor)
        
        # Interpolate each channel
        h_fine, w_fine = x_grid.shape
        interpolated = np.zeros((h_fine, w_fine, c))
        
        for ch in range(c):
            interpolated[:, :, ch] = self.interpolate_channel(
                data[:, :, ch],
                x_coords,
                y_coords,
                x_grid,
                y_grid,
                method
            )
        
        return interpolated, x_grid, y_grid
    
    def validate_quality(
        self, 
        original: np.ndarray, 
        interpolated: np.ndarray
    ) -> Dict:
        """
        Validate interpolation quality.
        
        Args:
            original: Original data
            interpolated: Interpolated data
            
        Returns:
            Dictionary with quality metrics
        """
        # Count valid points
        orig_valid = np.sum(~np.isnan(original))
        interp_valid = np.sum(~np.isnan(interpolated))
        
        # Calculate statistics on valid regions
        orig_mean = np.nanmean(original)
        orig_std = np.nanstd(original)
        interp_mean = np.nanmean(interpolated)
        interp_std = np.nanstd(interpolated)
        
        metrics = {
            'original_valid_points': int(orig_valid),
            'interpolated_valid_points': int(interp_valid),
            'original_mean': float(orig_mean),
            'original_std': float(orig_std),
            'interpolated_mean': float(interp_mean),
            'interpolated_std': float(interp_std),
            'mean_difference': float(abs(interp_mean - orig_mean)),
            'std_difference': float(abs(interp_std - orig_std))
        }
        
        return metrics
    
    def interpolate(
        self,
        data: np.ndarray,
        extent: list,
        factor: Optional[int] = None
    ) -> Tuple[np.ndarray, Dict]:
        """
        Complete interpolation pipeline.
        
        Args:
            data: Input data, shape (H, W, C)
            extent: [x_min, x_max, y_min, y_max]
            factor: Optional upsampling factor
            
        Returns:
            Tuple of (interpolated data, metadata)
        """
        # Interpolate
        interpolated, x_grid, y_grid = self.interpolate_values(data, extent)
        
        # Validate quality
        quality_metrics = self.validate_quality(data, interpolated)
        
        # Create metadata
        metadata = {
            'interpolation_method': self.interpolation_method,
            'original_shape': data.shape,
            'interpolated_shape': interpolated.shape,
            'extent': extent,
            'quality_metrics': quality_metrics
        }
        
        return interpolated, metadata
