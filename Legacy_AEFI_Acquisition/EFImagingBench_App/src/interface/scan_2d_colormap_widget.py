import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.cm as cm
import matplotlib.colors as colors
import matplotlib.pyplot as plt # Added for Rectangle
from interface.presenters.scan_presenter import ScanPresenter

class Scan2DColormapWidget(QWidget):
    """
    Widget for 2D colormap visualization of a scan.
    Connects to ScanPresenter signals.
    """
    def __init__(self, presenter: ScanPresenter, parent=None):
        super().__init__(parent)
        self.presenter = presenter
        self.positions = []
        self.values = []
        
        # Setup UI with Matplotlib
        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot(111)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # Connect to Presenter signals
        self.presenter.scan_point_acquired.connect(self.on_point_acquired)
        self.presenter.scan_completed.connect(self.on_scan_completed)
        self.presenter.scan_started.connect(self.on_scan_started)

    def on_scan_started(self, scan_id: str, config: dict):
        """Reset plot on new scan."""
        self.positions = []
        self.values = []
        self.ax.clear()
        self.canvas.draw()

    def on_point_acquired(self, data: dict):
        """Receive point data from Presenter."""
        x = data['x']
        y = data['y']
        value = data['value']
        
        self.positions.append((x, y))
        self.values.append(value)
        self.update_plot()

    def on_scan_completed(self, scan_id: str, total_points: int):
        """Finalize plot."""
        self.update_plot(final=True)

    def update_plot(self, final=False):
        """Update colormap."""
        self.ax.clear()
        if not self.positions:
            return

        # Determine grid bounds
        xs = [p[0] for p in self.positions]
        ys = [p[1] for p in self.positions]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        
        # Estimate step size (naive)
        unique_xs = sorted(list(set(xs)))
        unique_ys = sorted(list(set(ys)))
        dx = (unique_xs[1] - unique_xs[0]) if len(unique_xs) > 1 else 1.0
        dy = (unique_ys[1] - unique_ys[0]) if len(unique_ys) > 1 else 1.0

        # Normalize colormap
        if not self.values:
            return
            
        norm = colors.Normalize(vmin=min(self.values), vmax=max(self.values))
        # Fix deprecation warning: use matplotlib.colormaps
        try:
            cmap = plt.get_cmap('viridis')
        except AttributeError:
             # Fallback for older versions if needed, or use new API
            cmap = cm.get_cmap('viridis')

        # Draw rectangles
        for (x, y), val in zip(self.positions, self.values):
            rect = plt.Rectangle((x - dx/2, y - dy/2), dx, dy,
                                 color=cmap(norm(val)))
            self.ax.add_patch(rect)

        # Set limits with some padding
        self.ax.set_xlim(x_min - dx, x_max + dx)
        self.ax.set_ylim(y_min - dy, y_max + dy)
        self.ax.set_aspect('equal')
        self.ax.set_title('Scan 2D Colormap')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')

        # Colorbar (re-add if needed, tricky in update loop without clearing figure)
        # For simplicity, we skip re-creating colorbar every frame or check if exists
        
        self.canvas.draw()

if __name__ == '__main__':
    # Simple test harness
    from PyQt6.QtWidgets import QApplication
    from infrastructure.events.in_memory_event_bus import InMemoryEventBus
    from application.scan_application_service.scan_application_service import ScanApplicationService
    from infrastructure.tests.mock_ports import MockMotionPort, MockAcquisitionPort
    
    app = QApplication(sys.argv)
    
    # Setup dependencies
    bus = InMemoryEventBus()
    motion = MockMotionPort()
    acq = MockAcquisitionPort()
    service = ScanApplicationService(motion, acq, bus)
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