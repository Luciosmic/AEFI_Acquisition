from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSlot
import numpy as np
from typing import Dict, Optional, List
from interface.ui_2d_scan.presenter_2d_scan import ScanPresenter

class BaseScan2DWidget(QWidget):
    """
    Base widget for 2D scan visualization.
    Handles data storage for multiple channels and signal connections.
    
    Attributes:
        data_grids (Dict[str, np.ndarray]): Dictionary of 2D arrays for each channel.
        current_channel (str): Currently selected channel for visualization.
        extent (List[float]): [x_min, x_max, y_min, y_max]
        nx (int): Number of points in X.
        ny (int): Number of points in Y.
    """
    
    def __init__(self, presenter: ScanPresenter, parent=None):
        super().__init__(parent)
        self.presenter = presenter
        
        # Data storage
        self.data_grids: Dict[str, np.ndarray] = {}
        self.current_channel: Optional[str] = None
        self.available_channels: List[str] = []
        
        self.extent = [0, 1, 0, 1]
        self.nx = 0
        self.ny = 0
        
        # Connect signals
        self.presenter.scan_started.connect(self.on_scan_started)
        self.presenter.scan_point_acquired.connect(self.on_point_acquired)
        self.presenter.scan_completed.connect(self.on_scan_completed)

    @pyqtSlot(str, dict)
    def on_scan_started(self, scan_id: str, config: dict):
        """Initialize grids on new scan."""
        self.nx = config.get('x_nb_points', 10)
        self.ny = config.get('y_nb_points', 10)
        x_min = config.get('x_min', 0)
        x_max = config.get('x_max', 10)
        y_min = config.get('y_min', 0)
        y_max = config.get('y_max', 10)
        
        self.extent = [x_min, x_max, y_min, y_max]
        
        # Reset data
        self.data_grids = {}
        self.available_channels = []
        
        # We don't know the channels yet until the first point arrives, 
        # or we could pre-define them if passed in config.
        # For now, we'll lazy-init in on_point_acquired or just clear here.
        
        self.prepare_visualization()

    @pyqtSlot(dict)
    def on_point_acquired(self, data: dict):
        """Update grids with new point."""
        value_data = data['value']
        index = data['index']
        
        # If this is the first point, initialize grids based on keys
        if not self.data_grids:
            if isinstance(value_data, dict):
                self.available_channels = list(value_data.keys())
                for channel in self.available_channels:
                    self.data_grids[channel] = np.full((self.ny, self.nx), np.nan)
                
                # Set default channel if not set
                if not self.current_channel or self.current_channel not in self.available_channels:
                    # Prefer 'x_in_phase' if available, else first one
                    if 'x_in_phase' in self.available_channels:
                        self.current_channel = 'x_in_phase'
                    else:
                        self.current_channel = self.available_channels[0]
                    self.on_channel_changed(self.current_channel)
            else:
                # Fallback for scalar value
                self.available_channels = ['default']
                self.data_grids['default'] = np.full((self.ny, self.nx), np.nan)
                self.current_channel = 'default'
                self.on_channel_changed('default')

        # Map index to grid coordinates
        # Using physical coordinates for robustness
        x = data['x']
        y = data['y']
        
        if self.nx > 1:
            x_idx = int(round((x - self.extent[0]) / (self.extent[1] - self.extent[0]) * (self.nx - 1)))
        else:
            x_idx = 0
            
        if self.ny > 1:
            y_idx = int(round((y - self.extent[2]) / (self.extent[3] - self.extent[2]) * (self.ny - 1)))
        else:
            y_idx = 0
            
        x_idx = max(0, min(x_idx, self.nx - 1))
        y_idx = max(0, min(y_idx, self.ny - 1))
        
        # Update grids
        if isinstance(value_data, dict):
            for channel, val in value_data.items():
                if channel in self.data_grids:
                    self.data_grids[channel][y_idx, x_idx] = val
        else:
            self.data_grids['default'][y_idx, x_idx] = value_data
            
        self.update_visualization()

    @pyqtSlot(str, int)
    def on_scan_completed(self, scan_id: str, total_points: int):
        pass

    def set_channel(self, channel: str):
        """Switch the displayed channel."""
        if channel in self.data_grids:
            self.current_channel = channel
            self.update_visualization()

    # --- Abstract Methods / Hooks ---
    
    def prepare_visualization(self):
        """Called when scan starts to reset/prepare plot."""
        pass
        
    def update_visualization(self):
        """Called when data is updated."""
        pass
        
    def on_channel_changed(self, new_channel: str):
        """Called when available channels are detected or channel is switched."""
        pass
