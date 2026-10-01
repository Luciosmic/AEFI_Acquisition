import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QComboBox, QLabel, QHBoxLayout,
    QListWidget, QListWidgetItem
)
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
            QListWidget {
                background-color: #222;
                color: #FFF;
                border: 1px solid #444;
            }
        """)
        
        # --- Toolbar ---
        toolbar_layout = QHBoxLayout()
        
        # View Mode Selector
        toolbar_layout.addWidget(QLabel("View:"))
        self.combo_view_mode = QComboBox()
        view_modes = ["Single View", "6-Channel Grid"] if self._enable_grid_view else ["Single View"]
        view_modes.append("Profiles")
        self.combo_view_mode.addItems(view_modes)
        self.combo_view_mode.currentTextChanged.connect(self._on_view_mode_changed)
        toolbar_layout.addWidget(self.combo_view_mode)
        
        # Channel Selector (only for Single View)
        self.lbl_channel = QLabel("Channel:")
        toolbar_layout.addWidget(self.lbl_channel)
        
        self.combo_channel = QComboBox()
        self.combo_channel.currentIndexChanged.connect(self._on_channel_index_changed)
        toolbar_layout.addWidget(self.combo_channel)

        # Profile axis selector (only for Profiles view)
        self.lbl_profile_axis = QLabel("Profiles along:")
        toolbar_layout.addWidget(self.lbl_profile_axis)

        self.combo_profile_axis = QComboBox()
        self.combo_profile_axis.addItem("X (fixed X, vs Y)", 'x')
        self.combo_profile_axis.addItem("Y (fixed Y, vs X)", 'y')
        self.combo_profile_axis.currentIndexChanged.connect(self._on_profile_axis_changed)
        toolbar_layout.addWidget(self.combo_profile_axis)

        self.lbl_profile_axis.setVisible(False)
        self.combo_profile_axis.setVisible(False)

        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

        # --- Matplotlib Canvas + profile list ---
        content_layout = QHBoxLayout()

        self.figure = Figure(facecolor='#1E1E1E')
        self.canvas = FigureCanvasQTAgg(self.figure)
        content_layout.addWidget(self.canvas, stretch=1)

        self.list_profiles = QListWidget()
        self.list_profiles.setMaximumWidth(160)
        self.list_profiles.itemChanged.connect(self._on_profile_item_changed)
        self.list_profiles.setVisible(False)
        content_layout.addWidget(self.list_profiles)

        layout.addLayout(content_layout)

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
        self._update_profile_list()

        # Reset visualization
        mode = self.combo_view_mode.currentText()
        if mode == "Single View":
            self._setup_single_view()
        elif mode == "Profiles":
            self._setup_profiles_view()
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
        single_channel = mode in ("Single View", "Profiles")
        profiles = mode == "Profiles"

        self.combo_channel.setVisible(single_channel)
        self.lbl_channel.setVisible(single_channel)
        self.lbl_profile_axis.setVisible(profiles)
        self.combo_profile_axis.setVisible(profiles)
        self.list_profiles.setVisible(profiles)

        if mode == "Single View":
            self._setup_single_view()
        elif profiles:
            self._setup_profiles_view()
        else:
            self._setup_grid_view()

    def _on_profile_axis_changed(self, index: int):
        self._update_profile_list()
        self._refresh_visualization()

    def _on_profile_item_changed(self, item: QListWidgetItem):
        self._refresh_visualization()

    def _profile_axis(self) -> str:
        return self.combo_profile_axis.currentData() or 'x'

    def _axis_coords(self, axis: str):
        """Physical coordinates of the grid along `axis` ('x' or 'y')."""
        x_min, x_max, y_min, y_max = self.extent
        y_nb, x_nb = self._grid_shape
        if axis == 'x':
            return np.linspace(x_min, x_max, x_nb)
        return np.linspace(y_min, y_max, y_nb)

    def _update_profile_list(self):
        """Rebuild the list of available profiles. Nothing is checked by default."""
        axis = self._profile_axis()
        coords = self._axis_coords(axis)

        self.list_profiles.blockSignals(True)
        self.list_profiles.clear()
        for idx, value in enumerate(coords):
            item = QListWidgetItem(f"{axis.upper()} = {value:.2f} mm")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, idx)
            self.list_profiles.addItem(item)
        self.list_profiles.blockSignals(False)

    def _checked_profiles(self):
        """(grid index, physical coordinate) of every checked profile."""
        coords = self._axis_coords(self._profile_axis())
        out = []
        for row in range(self.list_profiles.count()):
            item = self.list_profiles.item(row)
            if item.checkState() == Qt.Checked:
                idx = item.data(Qt.UserRole)
                out.append((idx, coords[idx]))
        return out

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

    def _setup_profiles_view(self):
        """Configure figure for a single line-plot axes."""
        self.figure.clear()
        self.axes_dict = {}
        self.ims_dict = {}

        ax = self.figure.add_subplot(111, facecolor='#2A2A2A')
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_color('#666')
        self.axes_dict['profiles'] = ax

        self.canvas.draw()
        self._refresh_visualization()

    def _refresh_visualization(self):
        """Refresh the matplotlib display."""
        mode = self.combo_view_mode.currentText()

        if mode == "Single View":
            self._update_single_view()
        elif mode == "Profiles":
            self._update_profiles_view()
        else:
            self._update_grid_view()

    def _update_profiles_view(self):
        ax = self.axes_dict.get('profiles')
        if ax is None:
            return

        ax.clear()
        ax.set_facecolor('#2A2A2A')
        ax.tick_params(colors='white')
        ax.grid(True, color='#444', linestyle=':')

        axis = self._profile_axis()
        # A profile at fixed X is plotted against Y, and vice versa.
        abscissa = self._axis_coords('y' if axis == 'x' else 'x')
        ax.set_xlabel('Y (mm)' if axis == 'x' else 'X (mm)', color='white')
        ax.set_ylabel('Value', color='white')

        data = self.data_grids.get(self.current_channel)
        if data is not None:
            for idx, coord in self._checked_profiles():
                # data is indexed [y, x]
                series = data[:, idx] if axis == 'x' else data[idx, :]
                ax.plot(abscissa, series, marker='o', markersize=3,
                        label=f"{axis.upper()} = {coord:.2f} mm")

            if ax.get_legend_handles_labels()[0]:
                legend = ax.legend(fontsize=8, facecolor='#1E1E1E', edgecolor='#444')
                for text in legend.get_texts():
                    text.set_color('white')

        title, color = self._get_channel_metadata(self.current_channel or "")
        ax.set_title(title, color=color, fontweight='bold')
        self.figure.tight_layout()
        self.canvas.draw()

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
            cbar = self.figure.colorbar(im, ax=ax, label='Value')
            cbar.ax.tick_params(colors='white')
            cbar.set_label('Value', color='white')
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
        if channel.startswith('x_') or channel == 'field_x':
            axis = 'X'
        elif channel.startswith('y_') or channel == 'field_y':
            axis = 'Y'
        elif channel.startswith('z_') or channel == 'field_z':
            axis = 'Z'

        # Parse type
        m_type = ""
        if 'in_phase' in channel:
            m_type = "In-Phase"
        elif 'quadrature' in channel:
            m_type = "In-Quadrature"
        elif channel.startswith('field_'):
            m_type = "Field"

        title = f"{axis} {m_type}" if axis and m_type else channel.replace('_', ' ').title()
        
        # Color mapping
        color_map = {'X': '#2196F3', 'Y': '#FFC107', 'Z': '#F44336'}
        color = color_map.get(axis, 'white')
        
        return title, color
