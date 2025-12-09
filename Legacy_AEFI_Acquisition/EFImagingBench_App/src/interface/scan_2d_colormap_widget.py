import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.cm as cm
import matplotlib.colors as colors
from application.event_bus import EventBus
from domain.events.scan_events import ScanPointAcquired, ScanCompleted

class Scan2DColormapWidget(QWidget):
    """
    Widget générique pour visualisation colormap 2D d'un scan.
    Souscrit à l'EventBus pour recevoir les événements de scan.
    Chaque point est représenté comme un rectangle remplissant uniformément la grille.
    """
    def __init__(self, event_bus: EventBus, parent=None):
        super().__init__(parent)
        self.event_bus = event_bus
        self.positions = []
        self.values = []
        self.grid_x = None
        self.grid_y = None

        # Setup UI avec Matplotlib
        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot(111)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # Souscription aux événements
        self.event_bus.subscribe('scanpointacquired', self.on_point_acquired)
        self.event_bus.subscribe('scancompleted', self.on_scan_completed)

    def on_point_acquired(self, event: ScanPointAcquired):
        """Réception d'un point : stocker position et valeur (ex: voltage_x_in_phase)."""
        pos = event.position
        value = event.measurement.voltage_x_in_phase  # Exemple ; adapter selon besoin
        self.positions.append((pos.x, pos.y))
        self.values.append(value)
        self.update_plot()  # Mise à jour progressive

    def on_scan_completed(self, event: ScanCompleted):
        """Scan terminé : finaliser le plot si nécessaire."""
        self.update_plot(final=True)

    def update_plot(self, final=False):
        """Mise à jour du colormap avec rectangles pour grille uniforme."""
        self.ax.clear()
        if not self.positions:
            return

        # Déterminer grille (min/max pour uniformité)
        xs = [p[0] for p in self.positions]
        ys = [p[1] for p in self.positions]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        dx = (x_max - x_min) / (len(set(xs)) - 1) if len(set(xs)) > 1 else 1
        dy = (y_max - y_min) / (len(set(ys)) - 1) if len(set(ys)) > 1 else 1

        # Normaliser colormap
        norm = colors.Normalize(vmin=min(self.values), vmax=max(self.values))
        cmap = cm.get_cmap('viridis')

        # Dessiner rectangles
        for (x, y), val in zip(self.positions, self.values):
            rect = plt.Rectangle((x - dx/2, y - dy/2), dx, dy,
                                 color=cmap(norm(val)))
            self.ax.add_patch(rect)

        self.ax.set_xlim(x_min - dx/2, x_max + dx/2)
        self.ax.set_ylim(y_min - dy/2, y_max + dy/2)
        self.ax.set_aspect('equal')
        self.ax.set_title('Scan 2D Colormap')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')

        # Colorbar
        sm = cm.ScalarMappable(norm=norm, cmap=cmap)
        self.figure.colorbar(sm, ax=self.ax, label='Value')

        self.canvas.draw()

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    event_bus = EventBus()  # Pour test
    window = Scan2DColormapWidget(event_bus)
    window.show()
    sys.exit(app.exec())