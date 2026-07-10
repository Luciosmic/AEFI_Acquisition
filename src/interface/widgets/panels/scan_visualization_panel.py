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
    def __init__(self, parent=None, enable_grid_view: bool = True):
        super().__init__(parent)

        # Data storage
        self.data_grids = {}  # channel -> 2D numpy array
        self.extent = [0, 1, 0, 1]  # [x_min, x_max, y_min, y_max]
        self.available_channels = []
        self.current_channel = None
        self._grid_shape = (1, 1)
        self._enable_grid_view = enable_grid_view

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
        view_modes = ["Single View", "6-Channel Grid"] if self._enable_grid_view else ["Single View"]
        self.combo_view_mode.addItems(view_modes)
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

    def initialize_scan(self, x_min, x_max, x_nb, y_min, y_max, y_nb, channels=None):
        """
        Initialize data grids for a new scan.

        `channels`: explicit channel list. Defaults to the 6 AD9106/ADS131A04
        voltage channels (X/Y/Z x In-Phase/Quadrature). Pass `[]` when the
        channel set isn't known yet (e.g. electric field probe, whose
        component count depends on the connected probe) — channels are then
        created lazily from whatever keys `update_data_point` receives.
        """
        self.extent = [float(x_min), float(x_max), float(y_min), float(y_max)]
        self._grid_shape = (int(y_nb), int(x_nb))

        if channels is None:
            channels = [
                'x_in_phase', 'x_quadrature',
                'y_in_phase', 'y_quadrature',
                'z_in_phase', 'z_quadrature'
            ]
        self.available_channels = list(channels)

        # Create empty grids
        self.data_grids = {ch: np.full(self._grid_shape, np.nan) for ch in self.available_channels}

        # Set default channel
        self.current_channel = self.available_channels[0] if self.available_channels else None

        # Populate channel combo
        self._update_channel_combo()
        
        # Reset visualization
        mode = self.combo_view_mode.currentText()
        if mode == "Single View":
            self._setup_single_view()
        else:
            self._setup_grid_view()

    def update_data_point(self, x_idx, y_idx, measurements: dict):
        """Update a single data point with measurements. Unknown channels are
        created lazily (grid shape fixed at `initialize_scan` time)."""
        new_channel_added = False
        for channel, value in measurements.items():
            if channel not in self.data_grids:
                self.data_grids[channel] = np.full(self._grid_shape, np.nan)
                self.available_channels.append(channel)
                new_channel_added = True
            self.data_grids[channel][y_idx, x_idx] = value

        if new_channel_added:
            if self.current_channel is None:
                self.current_channel = self.available_channels[0]
            self._update_channel_combo()

        self._refresh_visualization()

    def update_data_point_from_position(self, x, y, measurements: dict):
        """Update data point by calculating indices from physical coordinates."""
        # Calculate indices based on extent and grid size
        x_min, x_max, y_min, y_max = self.extent

        # Grid dimensions are fixed at `initialize_scan` time, independently
        # of whether any channel grid has been created yet (channels can be
        # created lazily on the first point — see `update_data_point`).
        y_nb, x_nb = self._grid_shape
        
        # Avoid division by zero
        if x_nb > 1:
            x_step = (x_max - x_min) / (x_nb - 1)
            x_idx = int(round((x - x_min) / x_step))
        else:
            x_idx = 0
            
        if y_nb > 1:
            y_step = (y_max - y_min) / (y_nb - 1)
            y_idx = int(round((y - y_min) / y_step))
        else:
            y_idx = 0
            
        # Bounds check
        if 0 <= x_idx < x_nb and 0 <= y_idx < y_nb:
            self.update_data_point(x_idx, y_idx, measurements)

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
        
        title = f"{axis} {m_type}" if axis and m_type else channel.replace('_', ' ').title()
        
        # Color mapping
        color_map = {'X': '#2196F3', 'Y': '#FFC107', 'Z': '#F44336'}
        color = color_map.get(axis, 'white')
        
        return title, color
