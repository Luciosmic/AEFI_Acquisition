import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTabWidget, QDockWidget, QScrollArea,
    QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QWheelEvent, QMouseEvent

from interface.ui_motion_control.presenter_motion_control import MotionControlPresenter
from interface.ui_motion_control.widget_motion_control import MotionControlWidget

from interface.ui_2d_scan.presenter_2d_scan import ScanPresenter
from interface.ui_2d_scan.widget_scan_2d_colormap import Scan2DColormapWidget
from interface.ui_2d_scan.widget_2d_scan_control import ScanControlWidget

from interface.ui_excitation_configuration.presenter_excitation import ExcitationPresenter
from interface.ui_excitation_configuration.widget_excitation import ExcitationWidget
from domain.value_objects.excitation.excitation_mode import ExcitationMode

from interface.ui_continuous_acquisition.presenter_continuous_acquisition import ContinuousAcquisitionPresenter
from interface.ui_continuous_acquisition.widget_continuous_acquisition import ContinuousAcquisitionWidget
from interface.ui_system_lifecycle.presenter_system_lifecycle import SystemLifecyclePresenter
from interface.ui_system_lifecycle.view_shutdown import ShutdownView
from interface.shared.custom_dock_title_bar import CustomDockTitleBar
from interface.ui_hardware_advanced_configuration.presenter_generic_hardware_config import GenericHardwareConfigPresenter
from interface.ui_hardware_advanced_configuration.widget_generic_hardware_config import AdvancedConfigWidget
from PyQt6.QtGui import QCloseEvent, QAction


class ZoomableScrollArea(QScrollArea):
    """
    QScrollArea with zoom functionality and maximum size constraints.
    
    Features:
    - Zoom in/out with Ctrl+MouseWheel
    - Maximum size limit for the contained widget
    - Scrollbars appear automatically when needed
    """
    
    zoomChanged = pyqtSignal(float)  # Emits new zoom factor
    
    def __init__(self, parent=None, max_width: int = 2000, max_height: int = 2000):
        super().__init__(parent)
        self._zoom_factor = 1.0
        self._min_zoom = 0.5
        self._max_zoom = 2.0
        self._zoom_step = 0.1
        self._max_width = max_width
        self._max_height = max_height
        
        self.setWidgetResizable(False)  # We control sizing manually for zoom
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Enable gesture recognition for pinch-to-zoom (touchpad/trackpad)
        self.grabGesture(Qt.GestureType.PinchGesture)
    
    def setWidget(self, widget: QWidget) -> None:
        """Override to apply maximum size constraints."""
        super().setWidget(widget)
        if widget:
            # Store original size hint or current size as baseline
            size_hint = widget.sizeHint()
            if size_hint.isValid():
                self._original_size = size_hint
            else:
                # Fallback to current size if sizeHint not available
                self._original_size = widget.size()
            
            # Apply maximum size constraint
            widget.setMaximumSize(self._max_width, self._max_height)
            
            # Install event filter on widget and all its children to capture Ctrl+Wheel
            # This ensures zoom works even when hovering over child widgets
            widget.installEventFilter(self)
            self._install_event_filter_recursive(widget)
            
            # Initial zoom update
            self._update_zoom()
    
    def _install_event_filter_recursive(self, widget: QWidget) -> None:
        """Recursively install event filter on widget and all its children."""
        for child in widget.findChildren(QWidget):
            if child != widget:  # Don't reinstall on self
                child.installEventFilter(self)
                self._install_event_filter_recursive(child)
    
    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        Handle zoom with Ctrl+Wheel or touchpad pinch gestures.
        
        On macOS with trackpad:
        - Pan (two-finger scroll): pixelDelta() non-zero, no modifier → normal scroll
        - Pinch-to-zoom: pixelDelta() non-zero + Cmd modifier, or angleDelta() with Ctrl
        - Ctrl+Wheel: angleDelta() with Ctrl modifier → zoom
        """
        # Check for Ctrl+Wheel zoom (mouse wheel with Ctrl key)
        has_ctrl = event.modifiers() & Qt.KeyboardModifier.ControlModifier
        
        # Check for touchpad gestures
        has_pixel_delta = event.pixelDelta().x() != 0 or event.pixelDelta().y() != 0
        
        # On macOS, pinch-to-zoom often comes with Cmd modifier
        # Check for Cmd (Meta) modifier which is common for pinch on macOS
        has_cmd = event.modifiers() & (Qt.KeyboardModifier.MetaModifier | Qt.KeyboardModifier.AltModifier)
        
        # Distinguish between pan and zoom:
        # - Pan: pixelDelta without modifiers → normal scroll
        # - Zoom: pixelDelta with Cmd/Ctrl, or angleDelta with Ctrl
        is_zoom_gesture = (
            has_ctrl or  # Ctrl+Wheel (mouse) or Ctrl+trackpad
            (has_pixel_delta and has_cmd)  # Pinch with Cmd modifier (macOS)
        )
        
        if is_zoom_gesture:
            # Zoom based on gesture
            if has_pixel_delta:
                # Touchpad pinch: use pixelDelta for smooth zoom
                delta = event.pixelDelta().y()
                if delta == 0:
                    delta = event.pixelDelta().x()  # Fallback to horizontal
            else:
                # Ctrl+Wheel: use angleDelta
                delta = event.angleDelta().y()
            
            if delta > 0:
                self.zoom_in()
            elif delta < 0:
                self.zoom_out()
            event.accept()
        else:
            # Normal scroll/pan (two-finger scroll on trackpad)
            super().wheelEvent(event)
    
    def event(self, event) -> bool:
        """
        Handle gesture events for pinch-to-zoom on touchpad.
        """
        from PyQt6.QtWidgets import QGestureEvent
        
        if isinstance(event, QGestureEvent):
            pinch = event.gesture(Qt.GestureType.PinchGesture)
            if pinch:
                # Get scale factor from pinch gesture
                # QPinchGesture is accessed via the gesture object
                scale_factor = pinch.scaleFactor() if hasattr(pinch, 'scaleFactor') else 1.0
                if abs(scale_factor - 1.0) > 0.01:  # Only react to significant changes
                    if scale_factor > 1.0:
                        # Pinch out (zoom in) - apply proportional zoom
                        new_zoom = min(self._zoom_factor * scale_factor, self._max_zoom)
                        self.set_zoom(new_zoom)
                    elif scale_factor < 1.0:
                        # Pinch in (zoom out) - apply proportional zoom
                        new_zoom = max(self._zoom_factor * scale_factor, self._min_zoom)
                        self.set_zoom(new_zoom)
                event.accept()
                return True
        return super().event(event)
    
    def eventFilter(self, obj, event) -> bool:
        """
        Event filter to capture Ctrl+Wheel events from child widgets
        and redirect them to the zoom functionality.
        """
        if isinstance(event, QWheelEvent):
            # If Ctrl is pressed, handle zoom at this level
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                # Redirect to our wheelEvent for zoom handling
                self.wheelEvent(event)
                return True  # Event handled
        # Let other events pass through normally
        return super().eventFilter(obj, event)
    
    def zoom_in(self) -> None:
        """Increase zoom level."""
        new_zoom = min(self._zoom_factor + self._zoom_step, self._max_zoom)
        self.set_zoom(new_zoom)
    
    def zoom_out(self) -> None:
        """Decrease zoom level."""
        new_zoom = max(self._zoom_factor - self._zoom_step, self._min_zoom)
        self.set_zoom(new_zoom)
    
    def set_zoom(self, factor: float) -> None:
        """Set zoom factor (0.5 to 2.0)."""
        factor = max(self._min_zoom, min(factor, self._max_zoom))
        if abs(factor - self._zoom_factor) < 0.01:
            return
        
        self._zoom_factor = factor
        self._update_zoom()
        self.zoomChanged.emit(factor)
    
    def zoom_factor(self) -> float:
        """Get current zoom factor."""
        return self._zoom_factor
    
    def reset_zoom(self) -> None:
        """Reset zoom to 1.0."""
        self.set_zoom(1.0)
    
    def _update_zoom(self) -> None:
        """Apply zoom factor to the contained widget."""
        widget = self.widget()
        if not widget or not hasattr(self, '_original_size'):
            return
        
        # Calculate new size based on original size and zoom
        new_width = int(self._original_size.width() * self._zoom_factor)
        new_height = int(self._original_size.height() * self._zoom_factor)
        
        # Respect maximum size
        new_width = min(new_width, self._max_width)
        new_height = min(new_height, self._max_height)
        
        # Allow smaller sizes for better flexibility when docked
        # Reduced minimum to allow more compact layouts
        new_width = max(new_width, 100)
        new_height = max(new_height, 100)
        
        widget.resize(new_width, new_height)
        
        # Disable manual zoom on signal plots when zoomed out (reduced mode)
        # This prevents pyqtgraph PlotWidget from interfering with scroll area zoom
        self._update_plot_widgets_zoom_state()
    
    def _update_plot_widgets_zoom_state(self) -> None:
        """
        Disable manual zoom on signal plots (pyqtgraph, matplotlib).
        
        Signal plots should not have interactive zoom/pan to prevent conflicts
        with the scroll area zoom. Users can zoom the entire dock instead.
        """
        widget = self.widget()
        if not widget:
            return
        
        # Always disable zoom on signal plots (not just in reduced mode)
        # Handle pyqtgraph PlotWidget instances
        try:
            import pyqtgraph as pg
            plot_widgets = widget.findChildren(pg.PlotWidget)
            for plot in plot_widgets:
                # Disable mouse interactions for zoom/pan permanently
                plot.setMouseEnabled(x=False, y=False)
                # Disable auto-range button
                if hasattr(plot, 'vb'):  # ViewBox
                    plot.vb.setMouseEnabled(x=False, y=False)
        except ImportError:
            pass  # pyqtgraph not available
        
        # Handle matplotlib FigureCanvas instances
        try:
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
            canvas_widgets = widget.findChildren(FigureCanvasQTAgg)
            for canvas in canvas_widgets:
                # Disable navigation toolbar interactions permanently
                if hasattr(canvas, 'figure'):
                    # Disable zoom/pan tools on matplotlib figure
                    for ax in canvas.figure.get_axes():
                        ax.set_navigate(False)
        except ImportError:
            pass  # matplotlib not available


class DashBoard(QMainWindow):
    """
    Main entry point for the UI.
    Receives fully constructed dependencies (Presenters) from the Composition Root.
    """
    def __init__(
        self, 
        scan_presenter: ScanPresenter,
        excitation_presenter: ExcitationPresenter,
        continuous_presenter: ContinuousAcquisitionPresenter,
        lifecycle_presenter: SystemLifecyclePresenter,
        motion_presenter: MotionControlPresenter,
        config_presenter: GenericHardwareConfigPresenter
    ):
        super().__init__()
        self.setWindowTitle("AEFI - Test Bench Control Dashboard")
        self.resize(1300, 850)
        
        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #252525;
                color: #FFFFFF;
            }
            QWidget {
                background-color: #252525;
                color: #FFFFFF;
            }
            QDockWidget {
                background-color: #353535;
                color: #FFFFFF;
                titlebar-close-icon: none;
                titlebar-normal-icon: none;
            }
            QDockWidget::title {
                background-color: #2E86AB;
                padding: 5px;
                color: #FFFFFF;
            }
            QScrollArea {
                background-color: #252525;
                border: none;
            }
            QMenuBar {
                background-color: #353535;
                color: #FFFFFF;
            }
            QMenuBar::item:selected {
                background-color: #2E86AB;
            }
            QMenu {
                background-color: #353535;
                color: #FFFFFF;
            }
            QMenu::item:selected {
                background-color: #2E86AB;
            }
        """)
        
        # --- Enable Fluid Docking ---
        # Allow nested docks (placing windows arbitrarily in grid)
        # Allow tabbed docks (stacking)
        # Animated docks (smoother transitions)
        self.setDockOptions(
            QMainWindow.DockOption.AllowNestedDocks | 
            QMainWindow.DockOption.AllowTabbedDocks | 
            QMainWindow.DockOption.AnimatedDocks |
            QMainWindow.DockOption.GroupedDragging
        )

        
        self.scan_presenter = scan_presenter
        self.excitation_presenter = excitation_presenter
        self.continuous_presenter = continuous_presenter
        self.lifecycle_presenter = lifecycle_presenter
        self.motion_presenter = motion_presenter
        self.config_presenter = config_presenter
        
        self._shutdown_complete = False
        
        # Store scroll areas for zoom reset functionality
        self._dock_scroll_areas = {}
        
        self._init_menu()
        
        # --- UI Assembly ---
        # We use QDockWidgets instead of QTabWidget for detachable tabs
        
        # 1. 2D Scan Dock
        self.dock_scan = QDockWidget("2D Scan", self)
        scroll_scan = self._wrap_in_scroll_area(self._build_scan_tab())
        self._dock_scroll_areas[self.dock_scan] = scroll_scan
        self.dock_scan.setWidget(scroll_scan)
        self.dock_scan.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                                   QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                                   QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.dock_scan.setTitleBarWidget(CustomDockTitleBar(self.dock_scan))
        self._setup_dock_interactions(self.dock_scan)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, self.dock_scan)

        # 2. Excitation Configuration Dock
        self.dock_excitation = QDockWidget("Excitation Configuration", self)
        excitation_widget = ExcitationWidget(self.excitation_presenter)
        scroll_excitation = self._wrap_in_scroll_area(excitation_widget)
        self._dock_scroll_areas[self.dock_excitation] = scroll_excitation
        self.dock_excitation.setWidget(scroll_excitation)
        self.dock_excitation.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                                         QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                                         QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.dock_excitation.setTitleBarWidget(CustomDockTitleBar(self.dock_excitation))
        self._setup_dock_interactions(self.dock_excitation)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, self.dock_excitation)

        # 3. Motion Control Dock
        self.dock_motion = QDockWidget("Motion Control", self)
        motion_widget = MotionControlWidget(self.motion_presenter)
        scroll_motion = self._wrap_in_scroll_area(motion_widget)
        self._dock_scroll_areas[self.dock_motion] = scroll_motion
        self.dock_motion.setWidget(scroll_motion)
        self.dock_motion.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                                     QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                                     QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.dock_motion.setTitleBarWidget(CustomDockTitleBar(self.dock_motion))
        self._setup_dock_interactions(self.dock_motion)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, self.dock_motion)

        # 4. Continuous Acquisition Dock (Controls + Visualizer combined)
        self.dock_continuous = QDockWidget("Continuous Acquisition", self)
        continuous_widget = ContinuousAcquisitionWidget(self.continuous_presenter)
        scroll_continuous = self._wrap_in_scroll_area(continuous_widget)
        self._dock_scroll_areas[self.dock_continuous] = scroll_continuous
        self.dock_continuous.setWidget(scroll_continuous)
        self.dock_continuous.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                                         QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                                         QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.dock_continuous.setTitleBarWidget(CustomDockTitleBar(self.dock_continuous))
        self._setup_dock_interactions(self.dock_continuous)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, self.dock_continuous)

        # 6. Advanced Config Dock (hidden by default)
        self.dock_config = QDockWidget("Advanced Config", self)
        scroll_config = self._wrap_in_scroll_area(self._build_advanced_config_tab())
        self._dock_scroll_areas[self.dock_config] = scroll_config
        self.dock_config.setWidget(scroll_config)
        self.dock_config.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                                     QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                                     QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.dock_config.setTitleBarWidget(CustomDockTitleBar(self.dock_config))
        self._setup_dock_interactions(self.dock_config)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, self.dock_config)
        self.dock_config.hide()  # Hidden by default
        
        # Create Windows Carrier (main visualization area for docks)
        self._create_windows_carrier()
        
        # Initial Layout: Grid (Scan Left, Continuous/Config Right)
        self._apply_layout_grid()
        
        # Create system dock at bottom (fixed size, always visible)
        self._create_system_dock()

        
        # --- Context Menu for Detaching ---
        # Locate the internal QTabBar used for dock tabs and add a context menu
        # We need to do this slightly after init or force layout update? 
        # Usually it's available immediately after tabifying.
        # --- Final UI Setup ---
        self._setup_view_menu()
        self._setup_layout_menu()

    def _setup_tab_context_menu(self):
        """
        Finds the QTabBar used by the dock widgets and enables a custom context menu
        to allow detaching (floating) via right-click.
        """
        from PyQt6.QtWidgets import QTabBar
        
        # Give Qt a moment to create the tab bar structure (though usually immediate)
        tab_bars = self.findChildren(QTabBar)
        for bar in tab_bars:
            bar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            bar.customContextMenuRequested.connect(self._on_tab_context_menu)

    def _on_tab_context_menu(self, point):
        """
        Show context menu on tab right-click.
        """
        from PyQt6.QtWidgets import QMenu, QTabBar
        
        sender = self.sender()
        if not isinstance(sender, QTabBar):
            return
            
        tab_index = sender.tabAt(point)
        if tab_index < 0:
            return
            
        # Identify which DockWidget corresponds to this tab text
        # (Heuristic: match window title)
        tab_text = sender.tabText(tab_index)
        target_dock = None
        
        for dock in [self.dock_scan, self.dock_continuous, self.dock_config]:
            if dock.windowTitle() == tab_text:
                target_dock = dock
                break
        
        if target_dock:
            menu = QMenu(self)
            action_detach = QAction("Detach (Float)", self)
            action_detach.triggered.connect(lambda: target_dock.setFloating(True))
            menu.addAction(action_detach)
            
            menu.exec(sender.mapToGlobal(point))

    def _init_menu(self):
        """
        Initialize the Menu Bar.
        Added "View" menu to toggle dock visibility.
        """
        menu_bar = self.menuBar()
        menu_bar.clear() # Clear existing if any

    def _setup_view_menu(self):
        """
        Populate the View menu with dock toggle actions.
        Must be called after docks are created.
        """
        menu_bar = self.menuBar()
        view_menu = menu_bar.addMenu("View")
        
        # Add toggle actions for each dock
        # These actions are automatically checkable and synced with visibility
        view_menu.addAction(self.dock_scan.toggleViewAction())
        view_menu.addAction(self.dock_excitation.toggleViewAction())
        view_menu.addAction(self.dock_motion.toggleViewAction())
        view_menu.addAction(self.dock_continuous.toggleViewAction())
        view_menu.addAction(self.dock_config.toggleViewAction())

    def _setup_layout_menu(self):
        """
        Populate the Layout menu with preset configurations.
        """
        menu_bar = self.menuBar()
        layout_menu = menu_bar.addMenu("Layout")
        
        layout_menu.addAction("Tabbed (Default)", self._apply_layout_tabbed)
        layout_menu.addAction("Grid (Split)", self._apply_layout_grid)
        layout_menu.addAction("Columns (Vertical)", self._apply_layout_columns)

    def _apply_layout_tabbed(self):
        """Reset to initial tabbed state."""
        # Ensure all are visible
        self.dock_scan.show()
        self.dock_continuous.show()
        self.dock_config.show()
        self.dock_scan.setFloating(False)
        self.dock_continuous.setFloating(False)
        self.dock_config.setFloating(False)
        
        # Add all to Top
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, self.dock_scan)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, self.dock_continuous)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, self.dock_config)
        
        # Tabify
        self.tabifyDockWidget(self.dock_scan, self.dock_continuous)
        self.tabifyDockWidget(self.dock_continuous, self.dock_config)
        self.dock_scan.raise_()

    def _apply_layout_grid(self):
        """
        Arranges docks in a grid layout with modular components.
        """
        # Show all docks
        self.dock_scan.show()
        self.dock_excitation.show()
        self.dock_motion.show()
        self.dock_continuous.show()
        self.dock_config.show()
        self.dock_scan.setFloating(False)
        self.dock_excitation.setFloating(False)
        self.dock_motion.setFloating(False)
        self.dock_continuous.setFloating(False)
        self.dock_config.setFloating(False)
        
        # 1. Main split: Scan on Left
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_scan)
        
        # 2. Right side: Top = Continuous, Bottom = Controls
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_continuous)
        
        # 3. Split continuous with excitation vertically
        self.splitDockWidget(self.dock_continuous, self.dock_excitation, Qt.Orientation.Vertical)
        
        # 4. Split excitation with motion
        self.splitDockWidget(self.dock_excitation, self.dock_motion, Qt.Orientation.Vertical)
        
        # 5. Split motion with config
        self.splitDockWidget(self.dock_motion, self.dock_config, Qt.Orientation.Vertical)

    def _apply_layout_columns(self):
        """Arranges docks in vertical columns."""
        self.dock_scan.show()
        self.dock_excitation.show()
        self.dock_motion.show()
        self.dock_continuous.show()
        self.dock_config.show()
        self.dock_scan.setFloating(False)
        self.dock_excitation.setFloating(False)
        self.dock_motion.setFloating(False)
        self.dock_continuous.setFloating(False)
        self.dock_config.setFloating(False)
        
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, self.dock_scan)
        self.splitDockWidget(self.dock_scan, self.dock_excitation, Qt.Orientation.Vertical)
        self.splitDockWidget(self.dock_excitation, self.dock_motion, Qt.Orientation.Vertical)
        self.splitDockWidget(self.dock_motion, self.dock_continuous, Qt.Orientation.Vertical)
        self.splitDockWidget(self.dock_continuous, self.dock_config, Qt.Orientation.Vertical)

    def _setup_dock_interactions(self, dock: QDockWidget) -> None:
        """
        Setup Ctrl+Click interaction to bring dock to front and reset zoom.
        
        When user Ctrl+Clicks on a dock:
        - Brings the dock to front (raise_)
        - Resets zoom to 1.0 for balanced visual rendering
        """
        def on_dock_clicked(event: QMouseEvent) -> None:
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                if event.button() == Qt.MouseButton.LeftButton:
                    # Bring dock to front
                    dock.raise_()
                    # Reset zoom to default (1.0)
                    if dock in self._dock_scroll_areas:
                        scroll_area = self._dock_scroll_areas[dock]
                        if isinstance(scroll_area, ZoomableScrollArea):
                            scroll_area.reset_zoom()
                    event.accept()
                    return
            # Let default behavior handle other clicks
            event.ignore()
        
        # Install event filter on the dock widget
        dock.installEventFilter(self)
        # Store the handler for this dock
        if not hasattr(self, '_dock_click_handlers'):
            self._dock_click_handlers = {}
        self._dock_click_handlers[dock] = on_dock_clicked
    
    def eventFilter(self, obj, event) -> bool:
        """Event filter to catch Ctrl+Click on dock widgets."""
        if isinstance(obj, QDockWidget):
            if hasattr(self, '_dock_click_handlers') and obj in self._dock_click_handlers:
                if isinstance(event, QMouseEvent):
                    handler = self._dock_click_handlers[obj]
                    handler(event)
                    if event.isAccepted():
                        return True
        return super().eventFilter(obj, event)
    
    def _create_windows_carrier(self) -> None:
        """
        Create the Windows Carrier - main visualization area that contains all dock widgets.
        
        This is the "aircraft carrier" area where all visualization docks (Scan, Continuous, Config)
        are placed. It takes up all available space above the fixed System Dock.
        """
        # Create central widget as Windows Carrier
        self.windows_carrier = QWidget()
        self.windows_carrier.setStyleSheet("background-color: #252525;")
        self.setCentralWidget(self.windows_carrier)
        # Note: We don't hide it - it serves as the container for docks
    
    def _create_system_dock(self) -> None:
        """
        Create a system dock at the bottom of the window for attaching/reducing dock windows.
        
        The dock shows buttons for each dock widget, allowing:
        - Click to bring dock to front
        - Toggle visibility (minimize/restore)
        - Visual indicator of dock state
        
        The dock has a FIXED HEIGHT, full width, and is always visible at the bottom.
        It cannot be resized or moved.
        """
        # Create a dock widget for the system dock itself
        self.dock_system = QDockWidget("System Dock", self)
        self.dock_system.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)  # Not movable/floating
        self.dock_system.setTitleBarWidget(QWidget())  # Hide title bar
        
        # Create dock bar widget - FIXED height, full width
        dock_bar = QFrame()
        dock_bar.setFrameShape(QFrame.Shape.NoFrame)  # No visible frame for cleaner look
        dock_bar.setFixedHeight(50)  # FIXED height - cannot be resized
        dock_bar.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-top: 1px solid #404040;
            }
        """)
        
        layout = QHBoxLayout(dock_bar)
        layout.setContentsMargins(8, 2, 8, 2)  # Minimal vertical margins
        layout.setSpacing(6)  # Tighter spacing
        
        # Create buttons for each dock
        self._dock_buttons = {}
        docks = [
            ("2D Scan", self.dock_scan),
            ("Excitation", self.dock_excitation),
            ("Motion", self.dock_motion),
            ("Continuous", self.dock_continuous),
            ("Config", self.dock_config),
        ]
        
        for name, dock in docks:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setChecked(dock.isVisible())
            btn.setFixedHeight(28)  # Compact button height
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3a3a3a;
                    color: white;
                    border: 1px solid #555;
                    border-radius: 4px;
                    padding: 2px 10px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                }
                QPushButton:checked {
                    background-color: #0078d4;
                    border: 1px solid #005a9e;
                }
            """)
            
            # Connect button to dock visibility
            def make_toggle_handler(d):
                def handler():
                    d.setVisible(not d.isVisible())
                    if d.isVisible():
                        d.raise_()
                return handler
            
            btn.clicked.connect(make_toggle_handler(dock))
            self._dock_buttons[dock] = btn
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Set dock bar as widget
        self.dock_system.setWidget(dock_bar)
        
        # Add system dock to bottom area - FIXED position
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dock_system)
        
        # Force fixed size constraints - dock cannot be resized
        # Use sizePolicy to prevent expansion
        self.dock_system.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # Can expand horizontally
            QSizePolicy.Policy.Fixed  # Fixed height, cannot expand vertically
        )
        self.dock_system.setMinimumHeight(50)
        self.dock_system.setMaximumHeight(50)  # FIXED height - prevent expansion
        self.dock_system.setMinimumWidth(1)  # Allow shrinking but will expand to full width
        
        # Ensure it's always visible and cannot be closed
        self.dock_system.setVisible(True)
        
        # Also set size policy on the dock_bar widget itself
        dock_bar.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        
        # Add to bottom dock area (standard view mode)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dock_system)
        
        # Ensure it's always visible and takes minimal space
        self.dock_system.setVisible(True)
        
        # Connect dock visibility changes to update button states
        for dock in [self.dock_scan, self.dock_excitation, self.dock_motion,
                     self.dock_continuous, self.dock_config]:
            dock.visibilityChanged.connect(lambda visible, d=dock: self._on_dock_visibility_changed(d, visible))
    
    def _on_dock_visibility_changed(self, dock: QDockWidget, visible: bool) -> None:
        """Update button state when dock visibility changes."""
        if dock in self._dock_buttons:
            self._dock_buttons[dock].setChecked(visible)
    
    def _wrap_in_scroll_area(self, widget: QWidget, max_width: int = 2000, max_height: int = 2000) -> ZoomableScrollArea:
        """
        Wrap a widget in a ZoomableScrollArea to enable panning/scrolling and zoom.
        
        Features:
        - Mouse wheel scrolling (normal)
        - Zoom in/out with Ctrl+MouseWheel
        - Scrollbar navigation
        - Maximum size constraints to prevent widgets from growing too large
        
        Args:
            widget: The widget to wrap
            max_width: Maximum width for the widget (default: 2000px)
            max_height: Maximum height for the widget (default: 2000px)
        """
        scroll = ZoomableScrollArea(max_width=max_width, max_height=max_height)
        scroll.setWidget(widget)
        return scroll

    def _build_advanced_config_tab(self) -> QWidget:
        # Use the dedicated AdvancedConfigWidget which uses the GenericHardwareConfigPresenter
        return AdvancedConfigWidget(self.config_presenter)

    def _build_scan_tab(self) -> QWidget:
        widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        
        # Left Column: Controls
        left_column = QVBoxLayout()
        left_column.setSpacing(4)
        left_column.setContentsMargins(0, 0, 0, 0)
        
        # Scan Control
        control_widget = ScanControlWidget(self.scan_presenter)
        left_column.addWidget(control_widget)
        
        # Excitation Control (Shared)
        excitation_widget = ExcitationWidget(self.excitation_presenter)
        left_column.addWidget(excitation_widget)
        
        # Remove stretch to avoid wasted space
        
        main_layout.addLayout(left_column, stretch=1)
        
        # Right: Visualization
        colormap_widget = Scan2DColormapWidget(self.scan_presenter)
        main_layout.addWidget(colormap_widget, stretch=3)
        
        widget.setLayout(main_layout)
        return widget

    def _build_continuous_tab(self) -> QWidget:
        widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        
        # Left Column: Excitation & Motion Control
        left_layout = QVBoxLayout()
        left_layout.setSpacing(4)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Excitation Configuration using existing Widget
        excitation_widget = ExcitationWidget(self.excitation_presenter)
        left_layout.addWidget(excitation_widget)
        
        # 2. Motion Control Widget
        motion_widget = MotionControlWidget(self.motion_presenter)
        left_layout.addWidget(motion_widget)
        
        # Remove stretch to avoid wasted space
        
        # Right Column: Continuous Acquisition Visualization
        continuous_widget = ContinuousAcquisitionWidget(self.continuous_presenter)
        
        # Add layouts
        main_layout.addLayout(left_layout, stretch=1)
        main_layout.addWidget(continuous_widget, stretch=3)
        
        widget.setLayout(main_layout)
        return widget

    def closeEvent(self, event: QCloseEvent):
        """
        Intercept close event to ensuring proper system shutdown.
        """
        if self._shutdown_complete:
            # Already shut down, allow close
            event.accept()
        else:
            # Prevent immediate close
            event.ignore()
            
            # Launch Shutdown View (Modal)
            shutdown_view = ShutdownView(self.lifecycle_presenter)
            result = shutdown_view.exec()
            
            # After shutdown dialog closes (Accepted or Rejected)
            # We assume it's safe to close now, or user forced it.
            self._shutdown_complete = True
            
            # Now trigger the close again
            self.close()
