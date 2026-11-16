"""
DataPreProcessor - Transforms CSV to HDF5, fills incomplete scans, and homogenizes grids.
Adapted from plot_scan.py's create_square_grid functionality.
"""

from typing import Tuple, Dict, Optional
import pandas as pd
import numpy as np

from aefi_post_processor_module.domain.processing.grid_builder.grid_builder import build_square_grid


class DataPreProcessor:
    """
    Preprocesses raw scan data:
    - Transforms CSV DataFrame to structured numpy arrays
    - Fills incomplete scans with NaN padding
    - Homogenizes grid to square dimensions
    """
    
    def __init__(self, grid_size: Optional[int] = None):
        """
        Initialize preprocessor.
        
        Args:
            grid_size: Optional fixed grid size. If None, determined from data.
        """
        self.grid_size = grid_size
    
    def create_square_grid(
        self, 
        df: pd.DataFrame, 
        value_columns: Optional[list] = None
    ) -> Tuple[np.ndarray, Dict[str, any]]:
        """
        Create a square grid from scan data with NaN padding if necessary.
        Adapted from plot_scan.py.
        
        Args:
            df: DataFrame with columns ['x', 'y', voltage_columns...]
            value_columns: List of voltage column names. If None, auto-detect.
            
        Returns:
            Tuple of (grid_data, metadata)
            - grid_data: shape (N, N, num_channels) where N = max(nx, ny)
            - metadata: dict with extent, coordinates, etc.
        """
        # Auto-detect voltage columns if not provided
        if value_columns is None:
            value_columns = [
                'voltage_x_in_phase', 'voltage_x_quadrature',
                'voltage_y_in_phase', 'voltage_y_quadrature',
                'voltage_z_in_phase', 'voltage_z_quadrature'
            ]
            # Filter to only existing columns
            value_columns = [col for col in value_columns if col in df.columns]
        
        if not value_columns:
            raise ValueError("No voltage columns found in DataFrame")
        
        grid, metadata = build_square_grid(
            df['x'].to_numpy(),
            df['y'].to_numpy(),
            df[value_columns].to_numpy(dtype=float),
            value_columns,
            self.grid_size,
        )
        return grid, metadata
    
    def transform_to_hdf5(self, df: pd.DataFrame) -> Tuple[np.ndarray, Dict]:
        """
        Transform CSV DataFrame to HDF5-ready numpy array.
        
        Args:
            df: Raw DataFrame from CSV
            
        Returns:
            Tuple of (data array, metadata)
        """
        return self.create_square_grid(df)
    
    def fill_incomplete_scans(
        self, 
        data: np.ndarray, 
        coords: Optional[Dict] = None
    ) -> np.ndarray:
        """
        Fill incomplete scans with NaN padding.
        This is already handled by create_square_grid, but provided for explicit calls.
        
        Args:
            data: Input data array
            coords: Optional coordinate information
            
        Returns:
            Data with NaN padding
        """
        # Already handled in create_square_grid
        # This method is for future enhancements or explicit padding operations
        return data
    
    def homogenize_grid(self, data: np.ndarray) -> np.ndarray:
        """
        Ensure grid is square and homogeneous.
        
        Args:
            data: Input data array
            
        Returns:
            Homogenized square grid
        """
        # If already square, return as-is
        if data.shape[0] == data.shape[1]:
            return data
        
        # Make square by padding
        max_dim = max(data.shape[0], data.shape[1])
        
        if len(data.shape) == 2:
            # 2D array
            padded = np.full((max_dim, max_dim), np.nan)
            padded[:data.shape[0], :data.shape[1]] = data
        elif len(data.shape) == 3:
            # 3D array (with channels)
            padded = np.full((max_dim, max_dim, data.shape[2]), np.nan)
            padded[:data.shape[0], :data.shape[1], :] = data
        else:
            raise ValueError(f"Unsupported data shape: {data.shape}")
        
        return padded
    
    def preprocess(self, df: pd.DataFrame) -> Tuple[np.ndarray, Dict]:
        """
        Complete preprocessing pipeline: CSV → homogenized grid.
        
        Args:
            df: Raw DataFrame from CSV
            
        Returns:
            Tuple of (preprocessed data, metadata)
        """
        # Create square grid (already handles padding and homogenization)
        grid, metadata = self.create_square_grid(df)
        
        return grid, metadata
