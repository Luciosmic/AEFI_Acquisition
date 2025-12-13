import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLabel, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

class ScanVisualizationPanel(QWidget):
    """
    Panel for visualizing 2D scan results with matplotlib colormaps.
    Supports single channel view and 6-channel grid view.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Data storage
        self.data_grids = {}  # channel -> 2D numpy array
        self.extent = [0, 1, 0, 1]  # [x_min, x_max, y_min, y_max]
        self.available_channels = []
        self.current_channel = None
        
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Style
        self.setStyleSheet("""
            QLabel { color: #DDD; }
            QComboBox {
                background-color: #222;
                color: #FFF;
                border: 1px solid #444;
                padding: 4px;
                border-radius: 3px;
            }
        """)
        
        # --- Toolbar ---
        toolbar_layout = QHBoxLayout()
        
        # View Mode Selector
        toolbar_layout.addWidget(QLabel("View:"))
        self.combo_view_mode = QComboBox()
        self.combo_view_mode.addItems(["Single View", "6-Channel Grid"])
        self.combo_view_mode.currentTextChanged.connect(self._on_view_mode_changed)
        toolbar_layout.addWidget(self.combo_view_mode)
        
        # Channel Selector (only for Single View)
        self.lbl_channel = QLabel("Channel:")
        toolbar_layout.addWidget(self.lbl_channel)
        
        self.combo_channel = QComboBox()
        self.combo_channel.currentIndexChanged.connect(self._on_channel_index_changed)
        toolbar_layout.addWidget(self.combo_channel)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # --- Matplotlib Canvas ---
        self.figure = Figure(facecolor='#1E1E1E')
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)
        
        # Initialize visualization
        self.axes_dict = {}  # channel -> ax
        self.ims_dict = {}   # channel -> image artist
        self._setup_single_view()

    def initialize_scan(self, x_min, x_max, x_nb, y_min, y_max, y_nb):
        """Initialize data grids for a new scan."""
        self.extent = [float(x_min), float(x_max), float(y_min), float(y_max)]
        
        # Initialize 6 channels (X/Y/Z × In-Phase/Quadrature)
        self.available_channels = [
            'x_in_phase', 'x_quadrature',
            'y_in_phase', 'y_quadrature',
            'z_in_phase', 'z_quadrature'
        ]
        
        # Create empty grids
        for channel in self.available_channels:
            self.data_grids[channel] = np.full((int(y_nb), int(x_nb)), np.nan)
        
        # Set default channel
        self.current_channel = 'x_in_phase'
        
        # Populate channel combo
        self._update_channel_combo()
        
        # Reset visualization
        mode = self.combo_view_mode.currentText()
        if mode == "Single View":
            self._setup_single_view()
        else:
            self._setup_grid_view()

    def update_data_point(self, x_idx, y_idx, measurements: dict):
        """Update a single data point with measurements."""
        for channel, value in measurements.items():
            if channel in self.data_grids:
                self.data_grids[channel][y_idx, x_idx] = value
        
        self._refresh_visualization()

    def _on_view_mode_changed(self, mode: str):
        if mode == "Single View":
            self.combo_channel.setVisible(True)
            self.lbl_channel.setVisible(True)
            self._setup_single_view()
        else:
            self.combo_channel.setVisible(False)
            self.lbl_channel.setVisible(False)
            self._setup_grid_view()

    def _on_channel_index_changed(self, index: int):
        if index < 0:
            return
        channel = self.combo_channel.itemData(index)
        if channel:
            self.current_channel = channel
            self._refresh_visualization()

    def _update_channel_combo(self):
        """Update channel combo box with available channels."""
        self.combo_channel.blockSignals(True)
        self.combo_channel.clear()
        
        for channel in self.available_channels:
            title, _ = self._get_channel_metadata(channel)
            self.combo_channel.addItem(title, channel)
        
        # Select current channel
        idx = self.combo_channel.findData(self.current_channel)
        if idx >= 0:
            self.combo_channel.setCurrentIndex(idx)
        
        self.combo_channel.blockSignals(False)

    def _setup_single_view(self):
        """Configure figure for single subplot."""
        self.figure.clear()
        self.axes_dict = {}
        self.ims_dict = {}
        
        ax = self.figure.add_subplot(111, facecolor='#2A2A2A')
        ax.tick_params(colors='white')
        self.axes_dict['single'] = ax
        
        self.canvas.draw()
        self._refresh_visualization()

    def _setup_grid_view(self):
        """Configure figure for 2x3 grid."""
        self.figure.clear()
        self.axes_dict = {}
        self.ims_dict = {}
        
        # Grid mapping: (row, col) -> channel
        grid_map = {
            (0, 0): 'x_in_phase', (0, 1): 'y_in_phase', (0, 2): 'z_in_phase',
            (1, 0): 'x_quadrature', (1, 1): 'y_quadrature', (1, 2): 'z_quadrature'
        }
        
        for (row, col), channel in grid_map.items():
            idx = row * 3 + col + 1
            ax = self.figure.add_subplot(2, 3, idx, facecolor='#2A2A2A')
            ax.tick_params(colors='white', labelsize=8)
            
            title, color = self._get_channel_metadata(channel)
            ax.set_title(title, color=color, fontweight='bold', fontsize=10)
            self.axes_dict[channel] = ax
        
        self.figure.tight_layout()
        self.canvas.draw()
        self._refresh_visualization()

    def _refresh_visualization(self):
        """Refresh the matplotlib display."""
        mode = self.combo_view_mode.currentText()
        
        if mode == "Single View":
            self._update_single_view()
        else:
            self._update_grid_view()

    def _update_single_view(self):
        if not self.current_channel or self.current_channel not in self.data_grids:
            return
        
        ax = self.axes_dict.get('single')
        if ax is None:
            return

        data = self.data_grids[self.current_channel]
        title, color = self._get_channel_metadata(self.current_channel)
        
        # Initialize or update image
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
            ax.set_xlabel('X (mm)', color='white')
            ax.set_ylabel('Y (mm)', color='white')
            self.figure.colorbar(im, ax=ax, label='Value')
            self.ims_dict['single'] = im
        
        im = self.ims_dict['single']
        im.set_data(data)
        im.set_extent(self.extent)
        ax.set_title(title, color=color, fontweight='bold')
        
        self._autoscale_im(im, data)
        self.canvas.draw()

    def _update_grid_view(self):
        for channel, ax in self.axes_dict.items():
            if channel not in self.data_grids:
                continue
            
            data = self.data_grids[channel]
            title, color = self._get_channel_metadata(channel)
            
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
        """Auto-scale colormap based on data range."""
        vmin = np.nanmin(data)
        vmax = np.nanmax(data)
        if not (np.isnan(vmin) or np.isnan(vmax)):
            if vmin == vmax:
                im.set_clim(vmin=vmin - 1e-9, vmax=vmax + 1e-9)
            else:
                im.set_clim(vmin=vmin, vmax=vmax)

    def _get_channel_metadata(self, channel: str):
        """Return (Title, Color) for a channel."""
        # Parse axis
        axis = None
        if channel.startswith('x_'):
            axis = 'X'
        elif channel.startswith('y_'):
            axis = 'Y'
        elif channel.startswith('z_'):
            axis = 'Z'
        
        # Parse type
        m_type = ""
        if 'in_phase' in channel:
            m_type = "In-Phase"
        elif 'quadrature' in channel:
            m_type = "In-Quadrature"
        
        title = f"{axis} {m_type}" if axis and m_type else channel
        
        # Color mapping
        color_map = {'X': '#2196F3', 'Y': '#FFC107', 'Z': '#F44336'}
        color = color_map.get(axis, 'white')
        
        return title, color
