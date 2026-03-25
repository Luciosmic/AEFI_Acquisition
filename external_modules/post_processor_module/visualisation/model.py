"""
Visualization Model
Handles data loading from HDF5 repository.
"""

from pathlib import Path
from typing import List, Tuple, Dict, Any
import numpy as np

from post_processor_module.processing.datahandler import DataHandler

class VisualisationModel:
    """
    Model for Visualization App.
    Scans repository for .h5 files and loads processing steps.
    """
    
    DEFAULT_CHANNELS = [
        'voltage_x_in_phase', 'voltage_x_quadrature',
        'voltage_y_in_phase', 'voltage_y_quadrature',
        'voltage_z_in_phase', 'voltage_z_quadrature'
    ]
    
    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)
    
    def list_scans(self) -> List[Path]:
        """List all .h5 files in the repository."""
        if not self.repo_path.exists():
            return []
        # Return sorted list of h5 files
        return sorted(list(self.repo_path.glob("**/*.h5")))
    
    def load_scan_steps(self, scan_path: Path) -> List[str]:
        """List available processing steps in a scan file."""
        if not scan_path.exists():
            return []
            
        try:
            with DataHandler(scan_path, mode='r') as handler:
                return handler.list_steps()
        except Exception as e:
            print(f"Error loading steps from {scan_path}: {e}")
            return []
            
    def get_step_data(self, scan_path: Path, step_name: str) -> Tuple[Dict[str, np.ndarray], List[float], Dict[str, Any]]:
        """
        Load data for a specific step.
        Returns format compatible with plotting logic:
        - grids: dict {channel_name: 2d_array}
        - extent: [left, right, bottom, top]
        - metadata: dict
        """
        try:
            with DataHandler(scan_path, mode='r') as handler:
                data, metadata = handler.load_step(step_name)
                
                # Convert 3D array (N, N, Ch) to dict of 2D grids
                grids = {}
                
                # Get channel names from metadata or fallback
                channel_names = metadata.get('channel_names', None)
                
                # If metadata channel names are json string, parse it?
                # DataHandler saves lists as is or json strings. 
                # Let's handle list (robustness)
                import json
                if isinstance(channel_names, str):
                    try:
                        channel_names = json.loads(channel_names)
                    except:
                        pass # keep as is or fallback
                
                if not channel_names or not isinstance(channel_names, list) or len(channel_names) != data.shape[2]:
                    # Layout fallback matching DataPreProcessor defaults
                    channel_names = self.DEFAULT_CHANNELS[:data.shape[2]]
                
                for i, ch in enumerate(channel_names):
                    if i < data.shape[2]:
                        grids[ch] = data[:, :, i]
                
                # Extract extent
                extent = metadata.get('extent', [0, 1, 0, 1])
                if isinstance(extent, str):
                    try:
                        extent = json.loads(extent)
                    except:
                        pass
                
                return grids, extent, metadata
                
        except Exception as e:
            raise RuntimeError(f"Failed to load step {step_name}: {e}")
