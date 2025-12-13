import sys
import numpy as np
from PyQt6.QtWidgets import QVBoxLayout, QComboBox, QLabel, QHBoxLayout, QApplication
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from interface.ui_2d_scan.presenter_2d_scan import ScanPresenter
from interface.ui_2d_scan.base_scan_2d_widget import BaseScan2DWidget

class Scan2DColormapWidget(BaseScan2DWidget):
    """
    Widget for 2D colormap visualization of a scan.
    Inherits from BaseScan2DWidget for data management.
    """
    def __init__(self, presenter: ScanPresenter, parent=None):
        # Initialize base class (connects signals)
        super().__init__(presenter, parent)
        
        # Setup UI
        self.init_ui()
        
        self.im = None

    def init_ui(self):
        layout = QVBoxLayout()
        
        # --- Toolbar ---
        toolbar_layout = QHBoxLayout()
        
        # View Mode Selector
        toolbar_layout.addWidget(QLabel("View:"))
        self.combo_view_mode = QComboBox()
        self.combo_view_mode.addItems(["Single View", "6-Channel Grid"])
        self.combo_view_mode.currentTextChanged.connect(self.on_view_mode_changed)
        toolbar_layout.addWidget(self.combo_view_mode)
        
        # Channel Selector (only for Single View)
        self.lbl_channel = QLabel("Channel:")
        toolbar_layout.addWidget(self.lbl_channel)
        
        self.combo_channel = QComboBox()
        # Connect to index change to retrieve user data (raw key)
        self.combo_channel.currentIndexChanged.connect(self._on_combo_index_changed)
        toolbar_layout.addWidget(self.combo_channel)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # --- Matplotlib Canvas ---
        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
        
        # Initialize default view
        self.axes_dict = {}  # channel -> ax
        self.ims_dict = {}   # channel -> image artist
        self.setup_single_view()

    def prepare_visualization(self):
        """Override: Reset plot on scan start."""
        self.combo_channel.clear()
        # triggering view mode change to reset visuals
        mode = self.combo_view_mode.currentText()
        if mode == "Single View":
            self.setup_single_view()
        else:
            self.setup_grid_view()

    def on_view_mode_changed(self, mode: str):
        if mode == "Single View":
            self.combo_channel.setVisible(True)
            self.lbl_channel.setVisible(True)
            self.setup_single_view()
        else:
            self.combo_channel.setVisible(False)
            self.lbl_channel.setVisible(False)
            self.setup_grid_view()

    def setup_single_view(self):
        """Configure figure for a single plot."""
        self.figure.clear()
        self.axes_dict = {}
        self.ims_dict = {}
        
        # Single axes
        ax = self.figure.add_subplot(111)
        self.axes_dict['single'] = ax
        
        self.canvas.draw()
        
        # Trigger update if we have data and a channel is selected
        if self.current_channel:
            self.update_visualization()

    def setup_grid_view(self):
        """Configure figure for 2x3 grid."""
        self.figure.clear()
        self.axes_dict = {}
        self.ims_dict = {}
        
        # Define grid mapping: (row, col) -> channel_key
        # Row 0: In-Phase | Row 1: Quadrature
        # Cols: X, Y, Z
        grid_map = {
            (0, 0): 'x_in_phase', (0, 1): 'y_in_phase', (0, 2): 'z_in_phase',
            (1, 0): 'x_quadrature', (1, 1): 'y_quadrature', (1, 2): 'z_quadrature'
        }
        
        for (row, col), channel in grid_map.items():
            # subplots index is 1-based: rows, cols, index
            # Index row-major: 1..6
            idx = row * 3 + col + 1
            ax = self.figure.add_subplot(2, 3, idx)
            
            title, color = self._get_metadata(channel)
            ax.set_title(title, color=color, fontweight='bold')
            self.axes_dict[channel] = ax
            
        self.figure.tight_layout()
        self.canvas.draw()
        self.update_visualization()

    def _on_combo_index_changed(self, index: int):
        """Handle dropdown selection change."""
        if index < 0: return
        
        # Retrieve raw key from user data
        raw_key = self.combo_channel.itemData(index)
        if raw_key:
            self.set_channel(raw_key)

    def on_channel_changed(self, new_channel: str):
        """Override: Update combo box and re-initialize plot if needed."""
        # Check if we need to repopulate the combo box
        # We compare raw keys stored in itemData with self.available_channels
        
        current_keys = [self.combo_channel.itemData(i) for i in range(self.combo_channel.count())]
        
        if set(current_keys) != set(self.available_channels):
            self.combo_channel.blockSignals(True)
            self.combo_channel.clear()
            
            for channel in self.available_channels:
                # Format label: "X In-Phase" etc.
                title, _ = self._get_metadata(channel)
                self.combo_channel.addItem(title, channel)
                
            # Restore selection
            index = self.combo_channel.findData(new_channel)
            if index >= 0:
                self.combo_channel.setCurrentIndex(index)
                
            self.combo_channel.blockSignals(False)
        else:
            # update selection if changed externally
             index = self.combo_channel.findData(new_channel)
             if index >= 0 and index != self.combo_channel.currentIndex():
                 self.combo_channel.blockSignals(True)
                 self.combo_channel.setCurrentIndex(index)
                 self.combo_channel.blockSignals(False)
            
        # Refreshes visualization
        self.update_visualization()

    def update_visualization(self):
        """Override: Update the plots."""
        mode = self.combo_view_mode.currentText()
        
        if mode == "Single View":
            self._update_single_view()
        else:
            self._update_grid_view()
            
    def _update_single_view(self):
        if not self.current_channel or self.current_channel not in self.data_grids:
            return
            
        ax = self.axes_dict.get('single')
        if ax is None: return

        data = self.data_grids[self.current_channel]
        title, color = self._get_metadata(self.current_channel)
        
        # Check if we need to init image
        if 'single' not in self.ims_dict:
             im = ax.imshow(
                data, 
                origin='lower', 
                extent=self.extent, 
                aspect='auto',
                cmap='viridis',
                interpolation='nearest'
            )
             ax.set_title(title, color=color, fontweight='bold')
             self.figure.colorbar(im, ax=ax, label='Value')
             self.ims_dict['single'] = im
        
        im = self.ims_dict['single']
        im.set_data(data)
        im.set_extent(self.extent)
        ax.set_title(title, color=color, fontweight='bold')

        # Auto-scale colors
        self._autoscale_im(im, data)
        self.canvas.draw()

    def _update_grid_view(self):
        for channel, ax in self.axes_dict.items():
            if channel not in self.data_grids:
                continue
                
            data = self.data_grids[channel]
            title, color = self._get_metadata(channel)
            
            if channel not in self.ims_dict:
                 im = ax.imshow(
                    data, 
                    origin='lower', 
                    extent=self.extent, 
                    aspect='auto',
                    cmap='viridis',
                    interpolation='nearest'
                )
                 self.ims_dict[channel] = im
            
            im = self.ims_dict[channel]
            im.set_data(data)
            im.set_extent(self.extent)
            self._autoscale_im(im, data)
            
        self.canvas.draw()
            
    def _autoscale_im(self, im, data):
        vmin = np.nanmin(data)
        vmax = np.nanmax(data)
        if not (np.isnan(vmin) or np.isnan(vmax)):
            if vmin == vmax:
                im.set_clim(vmin=vmin - 1e-9, vmax=vmax + 1e-9)
            else:
                im.set_clim(vmin=vmin, vmax=vmax)
                
    def _get_metadata(self, channel: str):
        """
        Return (Title, TitleColor) based on channel name.
        Requirements:
        Labels: "X In-Phase", "X In-Quadrature"
        Colors: Title text colored.
        X - Blue
        Y - Yellow/Orange
        Z - Red
        """
        # Default
        title = channel
        color = 'black'
        
        # Parse axis
        axis = None
        if channel.startswith('x_'): axis = 'X'
        elif channel.startswith('y_'): axis = 'Y'
        elif channel.startswith('z_'): axis = 'Z'
        
        # Parse type
        m_type = ""
        if 'in_phase' in channel: m_type = "In-Phase"
        elif 'quadrature' in channel: m_type = "In-Quadrature"
        
        if axis and m_type:
            title = f"{axis} {m_type}"
            
        # Select Color
        if axis == 'X': color = 'blue'
        elif axis == 'Y': color = '#FFC107' # Amber/Orange-Yellow for visibility on white
        elif axis == 'Z': color = 'red'
        
        return title, color

if __name__ == '__main__':
    # Simple test harness
    from PyQt5.QtWidgets import QApplication
    from infrastructure.events.in_memory_event_bus import InMemoryEventBus
    from application.scan_application_service.scan_application_service import ScanApplicationService
    from infrastructure.tests.mock_ports import MockMotionPort, MockAcquisitionPort
    
    from infrastructure.execution.step_scan_executor import StepScanExecutor
    
    app = QApplication(sys.argv)
    
    # Setup dependencies
    bus = InMemoryEventBus()
    motion = MockMotionPort()
    acq = MockAcquisitionPort()
    executor = StepScanExecutor(motion, acq, bus)
    service = ScanApplicationService(motion, acq, bus, executor)
    presenter = ScanPresenter(service)
    
    window = Scan2DColormapWidget(presenter)
    window.show()
    
    # Simulate a scan start after 1s
    import threading
    import time
    def run_sim():
        time.sleep(1)
        presenter.start_scan({
            "x_min": 0, "x_max": 2, "x_nb_points": 3,
            "y_min": 0, "y_max": 2, "y_nb_points": 3,
            "scan_pattern": "RASTER"
        })
    
    t = threading.Thread(target=run_sim)
    t.start()
    
    sys.exit(app.exec())