"""
Point d'entrée principal pour la visualisation du cube sensor.

Utilise le pattern Presenter-Adapter avec séparation des responsabilités.
Utilise PySide6-QtAds pour les dock widgets.
"""
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QPushButton, QGroupBox, QMainWindow
)
from PySide6.QtCore import QTimer, Qt
try:
    from PySide6QtAds import CDockManager, CDockWidget, LeftDockWidgetArea, CenterDockWidgetArea
    QTADS_AVAILABLE = True
except ImportError:
    QTADS_AVAILABLE = False
    print("Warning: PySide6-QtAds not available. Install with: pip install PySide6-QtAds")
from cube_visualizer_presenter import CubeVisualizerPresenter
from cube_visualizer_adapter_pyvista import CubeVisualizerAdapter
from cube_geometry import get_default_theta_x, get_default_theta_y
from event_bus import EventBus, Event, EventType
from command_bus import CommandBus
from commands import UpdateAnglesCommand, ResetToDefaultCommand, ResetCameraViewCommand


class CubeSensorUI(QMainWindow):
    """Fenêtre UI pour contrôler les angles du cube sensor avec visualisation intégrée."""
    
    def __init__(self):
        print("[DEBUG] CubeSensorUI.__init__() - Début")
        super().__init__()
        self.setWindowTitle("Cube Sensor - Contrôle des Angles")
        self.setGeometry(100, 100, 1200, 800)
        print("[DEBUG] Fenêtre créée, géométrie définie")
        
        # Utiliser QtAds si disponible, sinon fallback sur QSplitter
        if QTADS_AVAILABLE:
            print("[DEBUG] Utilisation de QtAds pour les dock widgets")
            self.dock_manager = CDockManager(self)
            self._setup_with_qtads()
        else:
            print("[DEBUG] QtAds non disponible, utilisation de QSplitter")
            from PySide6.QtWidgets import QSplitter
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QVBoxLayout(central_widget)
            splitter = QSplitter(Qt.Horizontal)
            main_layout.addWidget(splitter)
            self._setup_with_splitter(splitter)
    
    def _setup_with_qtads(self):
        """Configure l'UI avec QtAds dock widgets."""
        print("[DEBUG] Configuration avec QtAds...")
        
        # Panneau contrôle (dock widget) - SEUL panneau nécessaire
        control_dock = CDockWidget("Contrôles")
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_dock.setWidget(control_panel)
        print("[DEBUG] Dock contrôle créé")
        
        # Ajouter le dock au manager (zone centrale)
        self.dock_manager.addDockWidget(CenterDockWidgetArea, control_dock)
        print("[DEBUG] Dock ajouté au manager")
        
        # Configurer le panneau de contrôle
        self._setup_control_panel(control_layout)
        
        # Créer les bus et le presenter (pas besoin de panneau de visualisation)
        self._setup_presenter_and_adapter()
    
    def _setup_with_splitter(self, splitter):
        """Configure l'UI avec QSplitter (fallback)."""
        print("[DEBUG] Configuration avec QSplitter...")
        
        # Panneau unique : Contrôles (pas de visualisation intégrée)
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        
        # Ajouter au central widget
        central_widget = self.centralWidget()
        main_layout = central_widget.layout()
        if main_layout is None:
            main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(control_panel)
        
        # Configurer le panneau de contrôle
        self._setup_control_panel(control_layout)
        
        # Créer les bus et le presenter (fenêtre séparée)
        self._setup_presenter_and_adapter()
    
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
        self.spin_x.setValue(get_default_theta_x())  # ~35.26°
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
        self.spin_y.setValue(get_default_theta_y())  # 45°
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
    
    def _setup_presenter_and_adapter(self):
        """Configure le presenter et l'adapter (mode fenêtre séparée)."""
        print("[DEBUG] Configuration du presenter et adapter...")
        
        # Créer CommandBus et EventBus (CQRS)
        print("[DEBUG] Création de CommandBus et EventBus...")
        try:
            self.command_bus = CommandBus()
            print("[DEBUG] CommandBus créé")
            self.event_bus = EventBus()
            print("[DEBUG] EventBus créé")
        except Exception as e:
            print(f"[DEBUG] ERREUR lors de la création des buses: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Créer le presenter avec CommandBus et EventBus (CQRS)
        print("[DEBUG] Création du presenter...")
        try:
            self.presenter = CubeVisualizerPresenter(
                command_bus=self.command_bus,
                event_bus=self.event_bus
            )
            print("[DEBUG] Presenter créé")
        except Exception as e:
            print(f"[DEBUG] ERREUR lors de la création du presenter: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Créer l'adapter SANS parent_widget (fenêtre séparée)
        print("[DEBUG] Création de l'adapter en mode fenêtre séparée...")
        self.adapter = CubeVisualizerAdapter(
            self.presenter, 
            event_bus=self.event_bus,
            parent_widget=None  # Pas de widget parent = fenêtre séparée
        )
        print("[DEBUG] Adapter créé")
        
        # S'abonner aux événements pour synchroniser l'UI
        self.event_bus.subscribe(EventType.ANGLES_CHANGED, self._on_angles_changed_from_event)
        
        # Timer pour éviter trop de rafraîchissements
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._do_update)
        self.update_timer.setSingleShot(True)
        
        # Flag pour éviter les boucles
        self._updating_from_presenter = False
        print("[DEBUG] Presenter et adapter configurés")
    
    def _setup_visualization_panel(self, visualization_layout, visualization_panel):
        """Configure le panneau de visualisation."""
        print("[DEBUG] Panneau visualisation créé")
        
        # Créer CommandBus et EventBus (CQRS) - doivent être créés après QApplication
        print("[DEBUG] Création de CommandBus et EventBus...")
        try:
            self.command_bus = CommandBus()
            print("[DEBUG] CommandBus créé")
            self.event_bus = EventBus()
            print("[DEBUG] EventBus créé")
        except Exception as e:
            print(f"[DEBUG] ERREUR lors de la création des buses: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Créer le presenter avec CommandBus et EventBus (CQRS)
        print("[DEBUG] Création du presenter...")
        try:
            self.presenter = CubeVisualizerPresenter(
                command_bus=self.command_bus,
                event_bus=self.event_bus
            )
            print("[DEBUG] Presenter créé")
        except Exception as e:
            print(f"[DEBUG] ERREUR lors de la création du presenter: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Créer l'adapter avec EventBus et parent_widget (création SYNCHRONE)
        print("[DEBUG] Création de l'adapter avec parent_widget...")
        self.adapter = CubeVisualizerAdapter(
            self.presenter, 
            event_bus=self.event_bus,
            parent_widget=visualization_panel
        )
        print("[DEBUG] Adapter créé")
        
        # S'abonner aux événements pour synchroniser l'UI
        self.event_bus.subscribe(EventType.ANGLES_CHANGED, self._on_angles_changed_from_event)
        
        # Le widget PyVista sera créé de manière différée
        # Vérifier si c'est une fenêtre séparée ou un widget intégré
        def check_widget_status():
            print("[DEBUG] check_widget_status() appelé")
            pvista_widget = self.adapter.get_widget()
            
            if pvista_widget:
                # Widget Qt disponible = intégration Qt
                print(f"[DEBUG] Widget PyVista récupéré: {pvista_widget}")
                print(f"[DEBUG] Parent actuel du widget: {pvista_widget.parent()}")
                
                # Si le widget a un parent, c'est qu'il est intégré dans Qt
                if pvista_widget.parent() == visualization_panel:
                    print("[DEBUG] Widget intégré dans Qt, ajout au layout...")
                    # Vérifier si le widget est déjà dans le layout
                    layout = visualization_panel.layout()
                    widget_in_layout = False
                    if layout:
                        for i in range(layout.count()):
                            item = layout.itemAt(i)
                            if item and item.widget() == pvista_widget:
                                widget_in_layout = True
                                break
                    
                    if not widget_in_layout:
                        visualization_layout.addWidget(pvista_widget)
                        pvista_widget.setMinimumSize(400, 400)
                        pvista_widget.show()
                        print("[DEBUG] Widget ajouté au layout")
                    else:
                        print("[DEBUG] Widget déjà dans le layout")
                else:
                    # Widget sans parent = fenêtre séparée (ne devrait pas arriver)
                    print("[DEBUG] Widget sans parent = fenêtre séparée PyVista")
                    info_label = QLabel("Visualisation 3D dans une fenêtre séparée PyVista")
                    info_label.setAlignment(Qt.AlignCenter)
                    visualization_layout.addWidget(info_label)
            else:
                # Pas de widget = fenêtre séparée ou pas encore créé
                if hasattr(self.adapter, 'plotter') and self.adapter.plotter is not None:
                    # Plotter existe mais pas de widget = fenêtre séparée
                    print("[DEBUG] Plotter en mode fenêtre séparée (pas de widget Qt)")
                    info_label = QLabel(
                        "Visualisation 3D dans une fenêtre séparée PyVista\n\n"
                        "La fenêtre PyVista s'ouvrira automatiquement.\n"
                        "Modifiez les angles ci-contre pour voir le cube se mettre à jour."
                    )
                    info_label.setAlignment(Qt.AlignCenter)
                    info_label.setWordWrap(True)
                    visualization_layout.addWidget(info_label)
                else:
                    # Plotter pas encore créé
                    print("[DEBUG] Plotter pas encore créé, réessai...")
                    if not hasattr(self, '_widget_retry_count'):
                        self._widget_retry_count = 0
                    self._widget_retry_count += 1
                    if self._widget_retry_count < 10:
                        QTimer.singleShot(200, check_widget_status)
                    else:
                        warning_label = QLabel("Erreur: Impossible de créer le plotter PyVista")
                        warning_label.setAlignment(Qt.AlignCenter)
                        visualization_layout.addWidget(warning_label)
        
        # Programmer la vérification après un délai
        QTimer.singleShot(300, check_widget_status)
        
        # Timer pour éviter trop de rafraîchissements
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._do_update)
        self.update_timer.setSingleShot(True)
        
        # Flag pour éviter les boucles
        self._updating_from_presenter = False
        print("[DEBUG] CubeSensorUI.__init__() - Fin")
    
    def _on_angle_changed(self):
        """Appelé quand un angle change depuis l'UI."""
        if self._updating_from_presenter:
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
    
    def _on_angles_changed_from_presenter(self, theta_x, theta_y, theta_z):
        """Callback appelé quand les angles changent depuis le presenter."""
        self._updating_from_presenter = True
        self.spin_x.setValue(theta_x)
        self.spin_y.setValue(theta_y)
        self.spin_z.setValue(theta_z)
        self._updating_from_presenter = False
    
    def _on_angles_changed_from_event(self, event: Event):
        """Handler pour l'événement ANGLES_CHANGED depuis EventBus."""
        theta_x = event.data['theta_x']
        theta_y = event.data['theta_y']
        theta_z = event.data['theta_z']
        self._on_angles_changed_from_presenter(theta_x, theta_y, theta_z)
    
    def _reset_camera_view(self, view_name: str):
        """Remet la caméra à sa position par défaut pour une vue (envoie un événement directement)."""
        # Pour la caméra, on envoie directement un événement (pas de modification d'état dans le presenter)
        if hasattr(self, 'event_bus') and self.event_bus:
            event = Event(
                event_type=EventType.CAMERA_VIEW_CHANGED,
                data={'view_name': view_name}
            )
            self.event_bus.publish(event)
        else:
            self.adapter.reset_camera_view(view_name)
    
    def _on_reset(self):
        """Reset aux valeurs par défaut (envoie une commande via CommandBus)."""
        # Envoyer une commande via CommandBus (CQRS)
        command = ResetToDefaultCommand()
        self.command_bus.send(command.to_command())
    
    def showEvent(self, event):
        """Initialise la visualisation après que la fenêtre Qt soit affichée."""
        print("[DEBUG] showEvent() appelé")
        super().showEvent(event)
        # Effectuer le rendu initial après que la fenêtre soit visible
        # Attendre un peu plus longtemps pour que le widget soit complètement initialisé
        def do_initial_render():
            print("[DEBUG] do_initial_render() appelé")
            if hasattr(self, 'adapter'):
                print(f"[DEBUG] Adapter existe: {self.adapter}")
                if hasattr(self.adapter, 'plotter'):
                    print(f"[DEBUG] Plotter existe: {self.adapter.plotter}")
                    if self.adapter.plotter is not None:
                        try:
                            print("[DEBUG] Vérification de l'état du widget...")
                            if self.adapter.plotter_widget:
                                print(f"[DEBUG] Widget visible: {self.adapter.plotter_widget.isVisible()}")
                                print(f"[DEBUG] Widget size: {self.adapter.plotter_widget.size()}")
                                print(f"[DEBUG] Widget parent: {self.adapter.plotter_widget.parent()}")
                            
                            print("[DEBUG] Appel de update_view() pour le rendu initial...")
                            self.adapter.update_view()
                            print("[DEBUG] Rendu initial effectué")
                            
                            # Forcer un update du widget après le rendu
                            if self.adapter.plotter_widget:
                                QTimer.singleShot(100, lambda: self.adapter.plotter_widget.update())
                        except Exception as e:
                            print(f"[DEBUG] ERREUR lors du rendu initial: {e}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print("[DEBUG] Plotter est None")
                else:
                    print("[DEBUG] Adapter n'a pas d'attribut plotter")
            else:
                print("[DEBUG] Adapter n'existe pas")
        
        # Pour une fenêtre séparée, le rendu sera fait dans _create_plotter_standalone
        # On fait juste une tentative ici au cas où
        QTimer.singleShot(1000, do_initial_render)
        print("[DEBUG] Rendu initial programmé")


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
    
    # S'assurer que QApplication est bien instancié avant de créer des QObject
    if QApplication.instance() is None:
        print("[DEBUG] ERREUR: QApplication.instance() est None")
        return
    
    print("[DEBUG] Création de CubeSensorUI...")
    try:
        window = CubeSensorUI()
        print("[DEBUG] CubeSensorUI créé")
    except Exception as e:
        print(f"[DEBUG] ERREUR lors de la création de CubeSensorUI: {e}")
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
    print("(La fenêtre PyVista s'ouvrira automatiquement après l'UI)")
    
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

