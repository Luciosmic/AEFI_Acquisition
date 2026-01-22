"""
DataHandler - Manages HDF5 file lifecycle and CSV loading.
Provides traceability by saving each processing step with metadata.
"""

from pathlib import Path
from typing import Tuple, Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
import numpy as np
import h5py


class DataHandler:
    """
    Manages data loading from CSV and saving processing steps to HDF5.
    Each processing step is saved with metadata for complete traceability.
    """
    
    def __init__(self, file_path: Path, mode: str = 'a'):
        """
        Initialize DataHandler with HDF5 file.
        
        Args:
            file_path: Path to HDF5 file
            mode: File mode ('r', 'w', 'a'). Default 'a' (read/write, create if not exists)
        """
        self.file_path = Path(file_path)
        self.mode = mode
        self.hdf5_file: Optional[h5py.File] = None
        self.processing_history: List[str] = []
        
        # Open file if not in read-only mode or if file exists
        if mode != 'r' or self.file_path.exists():
            self._open_file()
    
    def _open_file(self):
        """Open HDF5 file and load processing history."""
        self.hdf5_file = h5py.File(self.file_path, self.mode)
        
        # Load processing history if it exists
        if 'processing_history' in self.hdf5_file.attrs:
            self.processing_history = list(self.hdf5_file.attrs['processing_history'])
    
    def load_csv(self, csv_path: Path) -> pd.DataFrame:
        """
        Load raw scan data from CSV file.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            DataFrame with scan data
        """
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        df = pd.read_csv(csv_path)
        
        # Save source file info to HDF5 metadata
        if self.hdf5_file is not None:
            self.hdf5_file.attrs['source_csv'] = str(csv_path)
            self.hdf5_file.attrs['load_timestamp'] = datetime.now().isoformat()
        
        return df
    
    def save_step(self, step_name: str, data: np.ndarray, metadata: Optional[Dict[str, Any]] = None):
        """
        Save a processing step to HDF5 with metadata.
        
        Args:
            step_name: Name of the processing step (e.g., 'preprocessed', 'phase_calibrated')
            data: Numpy array with processed data
            metadata: Optional dictionary with step-specific metadata
        """
        if self.hdf5_file is None:
            raise RuntimeError("HDF5 file not open. Cannot save step.")
        
        # Create group for this step
        group_name = f"/{step_name}"
        
        # Remove existing group if it exists
        if group_name in self.hdf5_file:
            del self.hdf5_file[group_name]
        
        group = self.hdf5_file.create_group(group_name)
        
        # Save data
        group.create_dataset('data', data=data, compression='gzip', compression_opts=4)
        
        # Save metadata
        group.attrs['timestamp'] = datetime.now().isoformat()
        group.attrs['step_name'] = step_name
        group.attrs['data_shape'] = data.shape
        group.attrs['data_dtype'] = str(data.dtype)
        
        if metadata:
            for key, value in metadata.items():
                # Handle different types appropriately
                if isinstance(value, (np.ndarray, list, tuple)):
                    group.attrs[key] = np.array(value)
                elif isinstance(value, (str, int, float, bool)):
                    group.attrs[key] = value
                elif isinstance(value, dict):
                    # Store dict as JSON string
                    import json
                    group.attrs[key] = json.dumps(value)
                else:
                    group.attrs[key] = str(value)
        
        # Update processing history
        self.processing_history.append(f"{step_name} @ {datetime.now().isoformat()}")
        self.hdf5_file.attrs['processing_history'] = self.processing_history
        
        # Flush to disk
        self.hdf5_file.flush()
    
    def load_step(self, step_name: str) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Load a processing step from HDF5.
        
        Args:
            step_name: Name of the processing step
            
        Returns:
            Tuple of (data array, metadata dict)
        """
        if self.hdf5_file is None:
            raise RuntimeError("HDF5 file not open. Cannot load step.")
        
        group_name = f"/{step_name}"
        
        if group_name not in self.hdf5_file:
            raise KeyError(f"Processing step '{step_name}' not found in HDF5 file.")
        
        group = self.hdf5_file[group_name]
        
        # Load data
        data = np.array(group['data'])
        
        # Load metadata
        metadata = dict(group.attrs)
        
        return data, metadata
    
    def get_processing_history(self) -> List[str]:
        """
        Get the complete processing history.
        
        Returns:
            List of processing steps with timestamps
        """
        return self.processing_history.copy()
    
    def list_steps(self) -> List[str]:
        """
        List all available processing steps in the HDF5 file.
        
        Returns:
            List of step names
        """
        if self.hdf5_file is None:
            return []
        
        steps = []
        for key in self.hdf5_file.keys():
            if isinstance(self.hdf5_file[key], h5py.Group):
                steps.append(key)
        
        return steps
    
    def close(self):
        """Close the HDF5 file."""
        if self.hdf5_file is not None:
            self.hdf5_file.close()
            self.hdf5_file = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __del__(self):
        """Destructor - ensure file is closed."""
        self.close()
