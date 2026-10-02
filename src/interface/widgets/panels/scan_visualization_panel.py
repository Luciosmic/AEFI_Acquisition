import time

import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QComboBox, QLabel, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton
)
from PySide6.QtCore import Qt, Signal, QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

class ScanVisualizationPanel(QWidget):
    """
    Panel for visualizing scan results, one channel or all channels at once:
    heatmaps by default, or (`profiles=True`) profiles at fixed X or Y.

    `channels`: channels expected by this panel. Defaults to the 6
    AD9106/ADS131A04 voltage channels. Pass `()` when the channel set isn't
    known up front (electric field probe: component count depends on the
    connected probe) — channels are then created lazily from whatever keys
    `update_data_point` receives.
    """
    VOLTAGE_CHANNELS = (
        'x_in_phase', 'x_quadrature',
        'y_in_phase', 'y_quadrature',
        'z_in_phase', 'z_quadrature',
    )
    SINGLE, ALL = "Single Channel", "All Channels"
    MIN_REDRAW_INTERVAL_MS = 200

    def __init__(self, parent=None, profiles: bool = False, channels=VOLTAGE_CHANNELS):
        super().__init__(parent)

        # Data storage
        self.data_grids = {}  # channel -> 2D numpy array
        self.extent = [0, 1, 0, 1]  # [x_min, x_max, y_min, y_max]
        self._default_channels = tuple(channels)
        self.available_channels = list(channels)
        self.current_channel = None
        self._grid_shape = (1, 1)
        self._profiles = profiles
        # Line scan geometry (x0, y0, ux, uy, step, length) or None for a 2D grid.
        # In line mode data grids are (1, n) and every view draws value vs distance.
        self._line = None

        # Deferred redraw (scan progress): data is updated on every point, the
        # figure at most every _redraw_interval_ms. A full redraw costs ~50 ms
        # (map) to ~330 ms (profiles) on an 81x81 grid (2026-10-01): drawing on
        # every point, the UI keeps up with ~2.6 points/s while a fly scan
        # produces 7-26/s — it fell behind, then the app went down.
        self._redraw_timer = QTimer(self)
        self._redraw_timer.setSingleShot(True)
        self._redraw_timer.timeout.connect(self._redraw_now)
        self._redraw_interval_ms = self.MIN_REDRAW_INTERVAL_MS
        self._stale = False

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
        # Profiles panel opens on all channels at once, map panel on a single heatmap
        self.combo_view_mode.addItems([self.ALL, self.SINGLE] if self._profiles else [self.SINGLE, self.ALL])
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

        # Profile list + check all / none, hidden together outside Profiles view
        self.profiles_box = QWidget()
        profiles_layout = QVBoxLayout(self.profiles_box)
        profiles_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout = QHBoxLayout()
        self.btn_check_all = QPushButton("Tout")
        self.btn_check_all.clicked.connect(lambda: self._set_all_profiles(Qt.Checked))
        self.btn_check_none = QPushButton("Aucun")
        self.btn_check_none.clicked.connect(lambda: self._set_all_profiles(Qt.Unchecked))
        buttons_layout.addWidget(self.btn_check_all)
        buttons_layout.addWidget(self.btn_check_none)
        profiles_layout.addLayout(buttons_layout)

        self.list_profiles = QListWidget()
        self.list_profiles.itemChanged.connect(self._on_profile_item_changed)
        profiles_layout.addWidget(self.list_profiles)

        self.profiles_box.setMaximumWidth(160)
        self.profiles_box.setVisible(False)
        content_layout.addWidget(self.profiles_box)

        layout.addLayout(content_layout)

        # Initialize visualization
        self.axes_dict = {}  # channel -> ax
        self.ims_dict = {}   # channel -> image artist
        self._on_view_mode_changed(self.combo_view_mode.currentText())

    def initialize_scan(self, x_min, x_max, x_nb, y_min, y_max, y_nb, channels=None):
        """
        Initialize data grids for a new 2D scan. `channels` overrides the
        panel's channel set (see class docstring).
        """
        self._line = None
        self.extent = [float(x_min), float(x_max), float(y_min), float(y_max)]
        self._grid_shape = (int(y_nb), int(x_nb))
        self._reset_channels(channels)

    def initialize_line(self, start_x, start_y, end_x, end_y, n_points, channels=None):
        """Initialize for a 1D line scan: data is plotted against the distance
        from the line start (mm), whatever the line orientation."""
        n = int(n_points)
        dx, dy = float(end_x) - float(start_x), float(end_y) - float(start_y)
        length = float(np.hypot(dx, dy))
        ux, uy = (dx / length, dy / length) if length > 0 else (1.0, 0.0)
        step = length / (n - 1) if n > 1 else 0.0
        self._line = (float(start_x), float(start_y), ux, uy, step, length)
        self._grid_shape = (1, n)
        self._reset_channels(channels)

    def _reset_channels(self, channels):
        self.available_channels = list(self._default_channels if channels is None else channels)

        # Create empty grids
        self.data_grids = {ch: np.full(self._grid_shape, np.nan) for ch in self.available_channels}

        # Set default channel
        self.current_channel = self.available_channels[0] if self.available_channels else None

        # Populate channel combo
        self._update_channel_combo()
        self._update_profile_list()

        # Reset visualization (also syncs the profile controls with line/grid mode)
        self._on_view_mode_changed(self.combo_view_mode.currentText())

    def update_data_point(self, x_idx, y_idx, measurements: dict, redraw: bool = True):
        """Update a single data point with measurements. Unknown channels are
        created lazily (grid shape fixed at `initialize_scan` time).
        `redraw=False`: the figure follows on the deferred redraw timer."""
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
            # Rebuild the view: the all-channels grid depends on the channel set
            self._on_view_mode_changed(self.combo_view_mode.currentText())
        elif redraw:
            self._refresh_visualization()
        elif not self._redraw_timer.isActive():
            self._redraw_timer.start(self._redraw_interval_ms)

    def _redraw_now(self):
        """Deferred redraw: skipped while hidden (drawn when shown again), and
        spaced by twice its own cost so it never takes more than ~1/3 of the
        UI thread, whatever the panel's size."""
        if not self.isVisible():
            self._stale = True
            return
        start = time.perf_counter()
        self._refresh_visualization()
        self._redraw_interval_ms = max(self.MIN_REDRAW_INTERVAL_MS, int(2000 * (time.perf_counter() - start)))

    def showEvent(self, event):
        super().showEvent(event)
        if self._stale:
            self._stale = False
            self._refresh_visualization()

    def update_data_point_from_position(self, x, y, measurements: dict, redraw: bool = True):
        """Update data point by calculating indices from physical coordinates."""
        if self._line is not None:
            x0, y0, ux, uy, step, _ = self._line
            s = (x - x0) * ux + (y - y0) * uy  # projection on the line
            idx = int(round(s / step)) if step > 0 else 0
            if 0 <= idx < self._grid_shape[1]:
                self.update_data_point(idx, 0, measurements, redraw)
            return

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
            self.update_data_point(x_idx, y_idx, measurements, redraw)

    def _on_view_mode_changed(self, mode: str):
        single_channel = mode == self.SINGLE
        # A line scan is its own single profile: no line list to pick from.
        profiles = self._profiles and self._line is None

        self.combo_channel.setVisible(single_channel)
        self.lbl_channel.setVisible(single_channel)
        self.lbl_profile_axis.setVisible(profiles)
        self.combo_profile_axis.setVisible(profiles)
        self.profiles_box.setVisible(profiles)

        if single_channel:
            self._setup_single_view()
        else:
            self._setup_grid_view()

    def _on_profile_axis_changed(self, index: int):
        self._update_profile_list()
        self._refresh_visualization()

    def _on_profile_item_changed(self, item: QListWidgetItem):
        self._refresh_visualization()

    def _set_all_profiles(self, state):
        # One redraw instead of one per item
        self.list_profiles.blockSignals(True)
        for row in range(self.list_profiles.count()):
            self.list_profiles.item(row).setCheckState(state)
        self.list_profiles.blockSignals(False)
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
        """Configure figure with one subplot per channel: a single row up to
        3 channels (field components), else 2 rows with in-phase on top and
        quadrature below (2x3 for the voltage channels)."""
        self.figure.clear()
        self.axes_dict = {}
        self.ims_dict = {}

        channels = sorted(self.available_channels, key=lambda ch: 'quadrature' in ch)
        rows = 1 if len(channels) <= 3 else 2
        cols = -(-len(channels) // rows)  # ceil

        for idx, channel in enumerate(channels, start=1):
            ax = self.figure.add_subplot(rows, cols, idx, facecolor='#2A2A2A')
            ax.tick_params(colors='white', labelsize=8)

            title, color = self._get_channel_metadata(channel)
            ax.set_title(title, color=color, fontweight='bold', fontsize=10)
            self.axes_dict[channel] = ax

        self.figure.tight_layout()
        self.canvas.draw()
        self._refresh_visualization()

    def _refresh_visualization(self):
        """Refresh the matplotlib display."""
        if self._line is not None:
            self._draw_curves(self._draw_line_profile)
        elif self._profiles:
            self._draw_curves(self._draw_profiles)
        elif 'single' in self.axes_dict:
            self._update_single_view()
        else:
            self._update_grid_view()

    def _draw_curves(self, draw):
        """Run a curve-drawing function on every axes: the 'single' axes
        shows the selected channel, grid axes their own channel."""
        first_ax = next(iter(self.axes_dict.values()), None)
        for key, ax in self.axes_dict.items():
            compact = key != 'single'
            channel = key if compact else self.current_channel
            draw(ax, channel, compact, legend=(ax is first_ax))
        self.figure.tight_layout()
        self.canvas.draw()

    def _prepare_curve_ax(self, ax, channel, compact, xlabel):
        ax.clear()
        ax.set_facecolor('#2A2A2A')
        ax.tick_params(colors='white', **({'labelsize': 8} if compact else {}))
        ax.grid(True, color='#444', linestyle=':')
        title, color = self._get_channel_metadata(channel or "")
        ax.set_title(title, color=color, fontweight='bold', **({'fontsize': 10} if compact else {}))
        if not compact:
            ax.set_xlabel(xlabel, color='white')
            ax.set_ylabel('Value', color='white')
        return color

    def _draw_line_profile(self, ax, channel, compact, legend):
        """Line scan: value vs distance from the line start."""
        color = self._prepare_curve_ax(ax, channel, compact, 'Distance along line (mm)')
        data = self.data_grids.get(channel)
        if data is not None:
            s = np.linspace(0.0, self._line[5], self._grid_shape[1])
            ax.plot(s, data[0, :], marker='o', markersize=3, color=color)

    def _draw_profiles(self, ax, channel, compact, legend):
        """2D scan: checked profiles at fixed X (vs Y) or fixed Y (vs X)."""
        axis = self._profile_axis()
        # A profile at fixed X is plotted against Y, and vice versa.
        abscissa = self._axis_coords('y' if axis == 'x' else 'x')
        self._prepare_curve_ax(ax, channel, compact, 'Y (mm)' if axis == 'x' else 'X (mm)')

        data = self.data_grids.get(channel)
        if data is None:
            return
        for idx, coord in self._checked_profiles():
            # data is indexed [y, x]
            series = data[:, idx] if axis == 'x' else data[idx, :]
            ax.plot(abscissa, series, marker='o', markersize=3,
                    label=f"{axis.upper()} = {coord:.2f} mm")

        # All-channels grid: one legend (same profiles everywhere) to keep plots readable
        if legend and ax.get_legend_handles_labels()[0]:
            leg = ax.legend(fontsize=7 if compact else 8, facecolor='#1E1E1E', edgecolor='#444')
            for text in leg.get_texts():
                text.set_color('white')

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
