"""
Point d'entrée principal pour la visualisation du cube sensor.

Utilise le pattern DDD avec séparation des couches :
- Domain : Value objects, services de géométrie
- Application : Services d'application, commandes
- Infrastructure : Messaging (CommandBus, EventBus), rendering (ModernGL)
- Interface : UI, views
"""
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QPushButton, QGroupBox, QMainWindow, QSplitter
)
from PySide6.QtCore import QTimer, Qt
try:
    from PySide6QtAds import CDockManager, CDockWidget, LeftDockWidgetArea, CenterDockWidgetArea
    QTADS_AVAILABLE = True
except ImportError:
    QTADS_AVAILABLE = False
    print("Warning: PySide6-QtAds not available. Install with: pip install PySide6-QtAds")

from application.services.cube_visualizer_service import CubeVisualizerService
from infrastructure.rendering.cube_visualizer_adapter_modern_gl import CubeVisualizerAdapterModernGL
from domain.services.geometry_service import get_default_theta_y
from infrastructure.messaging.event_bus import EventBus, Event, EventType
from infrastructure.messaging.command_bus import CommandBus
from application.commands import UpdateAnglesCommand, ResetToDefaultCommand, ResetCameraViewCommand


class CubeVisualizerView(QMainWindow):
    """Fenêtre UI pour contrôler les angles du cube sensor avec visualisation intégrée."""
    
    def __init__(self):
        print("[DEBUG] CubeVisualizerView.__init__() - Début")
        super().__init__()
        self.setWindowTitle("Cube Sensor - Contrôle des Angles (ModernGL)")
        self.setGeometry(100, 100, 1200, 800)
        print("[DEBUG] Fenêtre créée, géométrie définie")
        
        # Créer CommandBus et EventBus (CQRS) - doivent être créés après QApplication
        self.command_bus = CommandBus()
        self.event_bus = EventBus()
        print("[DEBUG] CommandBus et EventBus créés")
        
        # Créer le service d'application
        self.service = CubeVisualizerService(
            command_bus=self.command_bus,
            event_bus=self.event_bus
        )
        print("[DEBUG] Service créé")
        
        # Utiliser QtAds si disponible, sinon fallback sur QSplitter
        if QTADS_AVAILABLE:
            print("[DEBUG] Utilisation de QtAds pour les dock widgets")
            self.dock_manager = CDockManager(self)
            self._setup_with_qtads()
        else:
            print("[DEBUG] QtAds non disponible, utilisation de QSplitter")
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QVBoxLayout(central_widget)
            splitter = QSplitter(Qt.Horizontal)
            main_layout.addWidget(splitter)
            self._setup_with_splitter(splitter)
    
    def _setup_with_qtads(self):
        """Configure l'UI avec QtAds dock widgets."""
        print("[DEBUG] Configuration avec QtAds...")
        
        # Panneau contrôle (dock widget)
        control_dock = CDockWidget("Contrôles")
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_dock.setWidget(control_panel)
        print("[DEBUG] Dock contrôle créé")
        
        # Panneau visualisation (dock widget)
        visualization_dock = CDockWidget("Visualisation 3D")
        visualization_panel = QWidget()
        visualization_layout = QVBoxLayout(visualization_panel)
        visualization_layout.setContentsMargins(0, 0, 0, 0)
        visualization_dock.setWidget(visualization_panel)
        print("[DEBUG] Dock visualisation créé")
        
        # Ajouter les docks au manager
        self.dock_manager.addDockWidget(LeftDockWidgetArea, control_dock)
        self.dock_manager.addDockWidget(CenterDockWidgetArea, visualization_dock)
        print("[DEBUG] Docks ajoutés au manager")
        
        # Configurer les panneaux
        self._setup_control_panel(control_layout)
        self._setup_visualization_panel(visualization_layout, visualization_panel)
    
    def _setup_with_splitter(self, splitter):
        """Configure l'UI avec QSplitter (fallback)."""
        print("[DEBUG] Configuration avec QSplitter...")
        
        # Panneau gauche : Contrôles
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        
        # Panneau droit : Visualisation ModernGL
        visualization_panel = QWidget()
        visualization_layout = QVBoxLayout(visualization_panel)
        visualization_layout.setContentsMargins(0, 0, 0, 0)
        
        splitter.addWidget(control_panel)
        splitter.addWidget(visualization_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([300, 900])
        
        # Configurer les panneaux
        self._setup_control_panel(control_layout)
        self._setup_visualization_panel(visualization_layout, visualization_panel)
    
    def _setup_control_panel(self, control_layout):
        """Configure le panneau de contrôle."""
        print("[DEBUG] Configuration du panneau contrôle...")
        
        # Groupe pour les angles
        group = QGroupBox("Angles de Rotation du Sensor")
        group_layout = QVBoxLayout(group)
        
        # Angle X
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("X (deg):"))
        self.spin_x = QDoubleSpinBox()
        self.spin_x.setRange(-180.0, 180.0)
        self.spin_x.setValue(0.0)
        self.spin_x.setDecimals(1)
        self.spin_x.setSingleStep(1.0)
        self.spin_x.valueChanged.connect(self._on_angle_changed)
        x_layout.addWidget(self.spin_x)
        group_layout.addLayout(x_layout)
        
        # Angle Y
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("Y (deg):"))
        self.spin_y = QDoubleSpinBox()
        self.spin_y.setRange(-180.0, 180.0)
        self.spin_y.setValue(get_default_theta_y())
        self.spin_y.setDecimals(1)
        self.spin_y.setSingleStep(1.0)
        self.spin_y.valueChanged.connect(self._on_angle_changed)
        y_layout.addWidget(self.spin_y)
        group_layout.addLayout(y_layout)
        
        # Angle Z
        z_layout = QHBoxLayout()
        z_layout.addWidget(QLabel("Z (deg):"))
        self.spin_z = QDoubleSpinBox()
        self.spin_z.setRange(-180.0, 180.0)
        self.spin_z.setValue(0.0)
        self.spin_z.setDecimals(1)
        self.spin_z.setSingleStep(1.0)
        self.spin_z.valueChanged.connect(self._on_angle_changed)
        z_layout.addWidget(self.spin_z)
        group_layout.addLayout(z_layout)
        
        control_layout.addWidget(group)
        
        # Boutons pour revenir aux vues
        view_buttons_group = QGroupBox("Retour aux Vues")
        view_buttons_layout = QVBoxLayout(view_buttons_group)
        view_buttons_row = QHBoxLayout()
        
        btn_view_3d = QPushButton("Vue 3D")
        btn_view_3d.clicked.connect(lambda: self._reset_camera_view('3d'))
        view_buttons_row.addWidget(btn_view_3d)
        
        btn_view_xy = QPushButton("Vue XY")
        btn_view_xy.clicked.connect(lambda: self._reset_camera_view('xy'))
        view_buttons_row.addWidget(btn_view_xy)
        
        view_buttons_layout.addLayout(view_buttons_row)
        
        view_buttons_row2 = QHBoxLayout()
        btn_view_xz = QPushButton("Vue XZ")
        btn_view_xz.clicked.connect(lambda: self._reset_camera_view('xz'))
        view_buttons_row2.addWidget(btn_view_xz)
        
        btn_view_yz = QPushButton("Vue YZ")
        btn_view_yz.clicked.connect(lambda: self._reset_camera_view('yz'))
        view_buttons_row2.addWidget(btn_view_yz)
        
        view_buttons_layout.addLayout(view_buttons_row2)
        control_layout.addWidget(view_buttons_group)
        
        # Bouton Reset
        btn_reset = QPushButton("Reset (Cube par défaut)")
        btn_reset.clicked.connect(self._on_reset)
        control_layout.addWidget(btn_reset)
        
        control_layout.addStretch()  # Pousser tout en haut
        print("[DEBUG] Panneau contrôle configuré")
    
    def _setup_visualization_panel(self, visualization_layout, visualization_panel):
        """Configure le panneau de visualisation."""
        print("[DEBUG] Configuration du panneau visualisation...")
        
        # Créer l'adapter ModernGL (QOpenGLWidget)
        self.adapter = CubeVisualizerAdapterModernGL(
            service=self.service,
            event_bus=self.event_bus,
            parent=visualization_panel
        )
        print("[DEBUG] Adapter ModernGL créé")
        
        # Ajouter le widget au layout
        visualization_layout.addWidget(self.adapter)
        self.adapter.setMinimumSize(400, 400)
        print("[DEBUG] Widget ModernGL ajouté au layout")
        
        # S'abonner aux événements pour synchroniser l'UI
        self.event_bus.subscribe(EventType.ANGLES_CHANGED, self._on_angles_changed_from_event)
        
        # Timer pour éviter trop de rafraîchissements
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._do_update)
        self.update_timer.setSingleShot(True)
        
        # Flag pour éviter les boucles
        self._updating_from_service = False
        print("[DEBUG] Panneau visualisation configuré")
    
    def _on_angle_changed(self):
        """Appelé quand un angle change depuis l'UI (envoie une commande via CommandBus)."""
        if self._updating_from_service:
            return
        self.update_timer.stop()
        self.update_timer.start(150)
    
    def _do_update(self):
        """Effectue la mise à jour depuis l'UI (envoie une commande via CommandBus)."""
        theta_x = self.spin_x.value()
        theta_y = self.spin_y.value()
        theta_z = self.spin_z.value()
        # Envoyer une commande via CommandBus (CQRS)
        command = UpdateAnglesCommand(theta_x, theta_y, theta_z)
        self.command_bus.send(command.to_command())
    
    def _on_angles_changed_from_event(self, event: Event):
        """Handler pour l'événement ANGLES_CHANGED depuis EventBus."""
        theta_x = event.data['theta_x']
        theta_y = event.data['theta_y']
        theta_z = event.data['theta_z']
        self._updating_from_service = True
        self.spin_x.setValue(theta_x)
        self.spin_y.setValue(theta_y)
        self.spin_z.setValue(theta_z)
        self._updating_from_service = False
    
    def _reset_camera_view(self, view_name: str):
        """Remet la caméra à sa position par défaut pour une vue (envoie une commande via CommandBus)."""
        command = ResetCameraViewCommand(view_name)
        self.command_bus.send(command.to_command())
    
    def _on_reset(self):
        """Reset aux valeurs par défaut (envoie une commande via CommandBus)."""
        command = ResetToDefaultCommand()
        self.command_bus.send(command.to_command())


def main():
    """Point d'entrée principal."""
    print("[DEBUG] main() - Début")
    print("[DEBUG] Création de QApplication...")
    try:
        app = QApplication(sys.argv)
        print("[DEBUG] QApplication créé")
    except Exception as e:
        print(f"[DEBUG] ERREUR lors de la création de QApplication: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("[DEBUG] Création de CubeVisualizerView...")
    try:
        window = CubeVisualizerView()
        print("[DEBUG] CubeVisualizerView créé")
    except Exception as e:
        print(f"[DEBUG] ERREUR lors de la création de CubeVisualizerView: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("[DEBUG] Affichage de la fenêtre...")
    try:
        window.show()
        print("[DEBUG] window.show() appelé")
    except Exception as e:
        print(f"[DEBUG] ERREUR lors de window.show(): {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("Fenêtre UI ouverte. Modifiez les angles pour voir le cube se mettre à jour.")
    
    print("[DEBUG] Démarrage de la boucle d'événements...")
    try:
        sys.exit(app.exec())
    except Exception as e:
        print(f"[DEBUG] ERREUR dans la boucle d'événements: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    main()

