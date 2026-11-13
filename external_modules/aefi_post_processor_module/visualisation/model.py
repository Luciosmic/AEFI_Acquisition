"""
Visualization Model
Handles data loading from HDF5 repository.
"""

import json
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any
import numpy as np

from aefi_post_processor_module.processing.datahandler import DataHandler

logger = logging.getLogger(__name__)

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
            logger.warning("scan.file_missing path=%s", scan_path)
            return []

        try:
            with DataHandler(scan_path, mode='r') as handler:
                return handler.list_steps()
        except Exception as e:
            logger.warning(
                "scan.steps_unreadable path=%s error_type=%s error=%s", scan_path, type(e).__name__, e, exc_info=True
            )
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
                
                # DataHandler saves string lists as JSON strings.
                if isinstance(channel_names, str):
                    try:
                        channel_names = json.loads(channel_names)
                    except json.JSONDecodeError:
                        pass  # not JSON: the fallback below takes over

                if not channel_names or not isinstance(channel_names, list) or len(channel_names) != data.shape[2]:
                    # Layout fallback matching DataPreProcessor defaults
                    channel_names = self.DEFAULT_CHANNELS[:data.shape[2]]
                    logger.warning(
                        "step.channel_names_defaulted path=%s step=%s channels=%s", scan_path, step_name, channel_names
                    )
                
                for i, ch in enumerate(channel_names):
                    if i < data.shape[2]:
                        grids[ch] = data[:, :, i]
                
                # Extract extent
                extent = metadata.get('extent', [0, 1, 0, 1])
                if isinstance(extent, str):
                    try:
                        extent = json.loads(extent)
                    except json.JSONDecodeError:
                        logger.warning("step.extent_unreadable path=%s step=%s extent=%r", scan_path, step_name, extent)
                
                return grids, extent, metadata
                
        except Exception as e:
            raise RuntimeError(f"Failed to load step {step_name}: {e}")
