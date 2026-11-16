"""
DataHandler - Reads the processing steps of an HDF5 file (the writing moved to infrastructure/hdf5_step_writer).
"""

import logging
from pathlib import Path
from typing import Tuple, Dict, List, Optional, Any
import numpy as np
import h5py

logger = logging.getLogger(__name__)


class DataHandler:
    """
    Opens an HDF5 file and reads its processing steps with their metadata.
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
