"""
Adapter PyVista pour la visualisation du cube sensor.

Responsabilité : Interface PyVista, gestion d'un seul plotter, rendu.
Utilise uniquement EventBus pour la communication (pas de callbacks directs).
Pas de sliders PyVista (redondants avec l'UI Qt).
"""
import pyvista as pv
from typing import Optional
from PySide6.QtWidgets import QWidget
from cube_geometry import (
    create_colored_cube,
    apply_rotation_to_mesh,
)
from cube_visualizer_presenter import CubeVisualizerPresenter
from event_bus import EventBus, Event, EventType


class CubeVisualizerAdapter:
    """
    Adapter gérant l'interface PyVista avec une seule fenêtre.
    
    Responsabilités:
    - Création et gestion d'un seul plotter PyVista (synchrone)
    - Rendu du cube avec possibilité de changer de vue
    - Synchronisation avec le presenter via EventBus uniquement
    """
    
    # Positions de caméra par défaut pour chaque vue
    CAMERA_POSITIONS = {
        '3d': ([(3, -3, 2), (0, 0, 0), (0, 0, 1)], 1.0),
        'xy': ([(0, 0, 3), (0, 0, 0), (0, 1, 0)], 0.8),
        'xz': ([(0, -3, 0), (0, 0, 0), (0, 0, 1)], 0.8),
        'yz': ([(3, 0, 0), (0, 0, 0), (0, 0, 1)], 0.8),
    }
    
    def __init__(self, presenter: CubeVisualizerPresenter, event_bus: EventBus, parent_widget: Optional[QWidget] = None):
        """
        Args:
            presenter: Presenter gérant la logique métier
            event_bus: EventBus pour recevoir les événements (requis)
            parent_widget: Widget Qt parent pour intégrer le plotter (optionnel)
        """
        print(f"[DEBUG] CubeVisualizerAdapter.__init__() - Début, parent_widget={parent_widget}")
        self.presenter = presenter
        self.event_bus = event_bus
        self.current_view = '3d'  # Vue actuelle
        self.parent_widget = parent_widget
        
        # S'abonner aux événements EventBus
        self.event_bus.subscribe(EventType.ANGLES_CHANGED, self._on_angles_changed_event)
        self.event_bus.subscribe(EventType.CAMERA_VIEW_CHANGED, self._on_camera_view_changed_event)
        print("[DEBUG] Abonné aux événements EventBus")
        
        # Initialiser le plotter comme None pour l'instant
        self.plotter = None
        self.plotter_widget = None
        
        # Créer le plotter de manière différée (après que le widget parent soit visible)
        if parent_widget is not None:
            print("[DEBUG] parent_widget fourni, création différée de QtInteractor...")
            # Utiliser QTimer pour créer après que le widget soit visible
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self._create_plotter_qt)
        else:
            print("[DEBUG] Pas de parent_widget, création d'une fenêtre séparée")
            self._create_plotter_standalone()
        
        print("[DEBUG] CubeVisualizerAdapter.__init__() - Fin")
    
    def _create_plotter_qt(self):
        """Crée le plotter Qt de manière différée (appelé via QTimer)."""
        print("[DEBUG] _create_plotter_qt() appelé")
        if self.plotter is not None:
            print("[DEBUG] Plotter déjà créé, ignoré")
            return
        
        # Option: utiliser une fenêtre séparée si l'intégration Qt pose problème
        # NOTE: L'intégration Qt avec pyvistaqt pose des problèmes de rendu sur macOS
        # - Le widget QtInteractor ne rend pas correctement
        # - Problèmes de contexte OpenGL/VTK avec Qt
        # La fenêtre séparée fonctionne correctement et est recommandée
        USE_STANDALONE_WINDOW = True  # Changer à False pour essayer l'intégration Qt (non recommandé)
        
        if USE_STANDALONE_WINDOW:
            print("[DEBUG] Mode fenêtre séparée activé (évite les problèmes d'intégration Qt)")
            self._create_plotter_standalone()
            return
        
        try:
            import pyvistaqt as pvqt
            print("[DEBUG] pyvistaqt importé avec succès")
            print("[DEBUG] Création de QtInteractor avec parent_widget...")
            if self.parent_widget is None:
                print("[DEBUG] parent_widget est None, impossible de créer QtInteractor")
                return
            
            # Essayer avec parent directement (approche recommandée par pyvistaqt)
            self.plotter = pvqt.QtInteractor(parent=self.parent_widget)
            self.plotter_widget = self.plotter.interactor
            print(f"[DEBUG] QtInteractor créé: {self.plotter_widget}")
            print(f"[DEBUG] Parent du widget: {self.plotter_widget.parent()}")
            
            # S'assurer que le widget est visible et a une taille
            self.plotter_widget.setMinimumSize(400, 400)
            self.plotter_widget.show()
            print(f"[DEBUG] Widget configuré avec taille minimale et show() appelé")
            
            self._initialize_plotter()
        except ImportError as e:
            print(f"[DEBUG] ImportError pyvistaqt: {e}")
            print("[DEBUG] Fallback vers fenêtre séparée...")
            self._create_plotter_standalone()
        except Exception as e:
            print(f"[DEBUG] Exception lors de la création de QtInteractor: {e}")
            import traceback
            traceback.print_exc()
            print("[DEBUG] Fallback vers fenêtre séparée...")
            self._create_plotter_standalone()
    
    def _create_plotter_standalone(self):
        """
        Crée un plotter en fenêtre séparée.
        
        NOTE: Mode recommandé car l'intégration Qt pose des problèmes de rendu.
        """
        print("[DEBUG] _create_plotter_standalone() appelé")
        self.plotter = pv.Plotter(title="Cube Sensor - Visualisation 3D")
        self.plotter_widget = None  # Pas de widget Qt pour une fenêtre séparée
        self._initialize_plotter()
        
        # Afficher la fenêtre séparée après un court délai pour s'assurer que tout est initialisé
        from PySide6.QtCore import QTimer
        def show_window():
            print("[DEBUG] Affichage de la fenêtre PyVista séparée...")
            try:
                # Afficher la fenêtre (non-bloquant)
                self.plotter.show(auto_close=False, interactive_update=True)
                print("[DEBUG] Fenêtre PyVista affichée")
                
                # Effectuer le rendu initial après que la fenêtre soit visible
                # Plusieurs tentatives avec délais croissants pour s'assurer que la fenêtre est prête
                def do_initial_render():
                    print("[DEBUG] Tentative de rendu initial dans fenêtre séparée...")
                    try:
                        self.update_view()
                        print("[DEBUG] Rendu initial effectué dans fenêtre séparée")
                    except Exception as e:
                        print(f"[DEBUG] ERREUR lors du rendu initial: {e}")
                        import traceback
                        traceback.print_exc()
                
                QTimer.singleShot(200, do_initial_render)
                QTimer.singleShot(500, do_initial_render)  # Tentative supplémentaire
            except Exception as e:
                print(f"[DEBUG] ERREUR lors de l'affichage de la fenêtre PyVista: {e}")
                import traceback
                traceback.print_exc()
        
        QTimer.singleShot(300, show_window)
    
    def _initialize_plotter(self):
        """Initialise le plotter (appelé après création)."""
        print("[DEBUG] _initialize_plotter() appelé")
        if self.plotter is None:
            print("[DEBUG] Plotter est None, impossible d'initialiser")
            return
        
        try:
            self.plotter.set_background('white')
            self.plotter.show_grid()
            
            # Stocker les acteurs
            self.cube_actor = None
            self.arrows_mes = {}
            self.arrows_labo = {}
            self.text_actor = None
            
            # Configurer la caméra initiale
            self._setup_camera('3d')
            
            # Activer le zoom au touchpad
            self.plotter.enable_trackball_style()
            
            # Pas de sliders PyVista (redondants avec l'UI Qt)
            # Le rendu initial sera fait dans showEvent de l'UI
            
            print("[DEBUG] _initialize_plotter() terminé")
        except Exception as e:
            print(f"[DEBUG] ERREUR lors de l'initialisation du plotter: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_angles_changed_event(self, event: Event):
        """Handler pour l'événement ANGLES_CHANGED (appelé directement depuis EventBus sur thread principal)."""
        print(f"[DEBUG] _on_angles_changed_event: {event.data}")
        theta_x = event.data['theta_x']
        theta_y = event.data['theta_y']
        theta_z = event.data['theta_z']
        # Appel DIRECT (EventBus garantit déjà l'exécution sur le thread principal)
        self.update_view(theta_x, theta_y, theta_z)
    
    def _on_camera_view_changed_event(self, event: Event):
        """Handler pour l'événement CAMERA_VIEW_CHANGED (appelé directement depuis EventBus)."""
        view_name = event.data.get('view_name', '3d')
        # Appel DIRECT
        self.reset_camera_view(view_name)
    
    def _setup_camera(self, view_name: str):
        """Configure la caméra pour une vue spécifique."""
        pos, zoom = self.CAMERA_POSITIONS[view_name]
        self.plotter.camera_position = pos
        self.plotter.camera.zoom(zoom)
        self.current_view = view_name
    
    def reset_camera_view(self, view_name: str):
        """
        Remet la caméra à sa position par défaut pour une vue.

        Args:
            view_name: '3d', 'xy', 'xz', ou 'yz'
        """
        if self.plotter is None:
            print("[DEBUG] reset_camera_view: plotter pas encore initialisé")
            return
        try:
            self._setup_camera(view_name)
            self.plotter.render()
        except Exception as e:
            print(f"[DEBUG] ERREUR lors du reset_camera_view: {e}")
            import traceback
            traceback.print_exc()
    
    def update_view(self, theta_x: Optional[float] = None, theta_y: Optional[float] = None, theta_z: Optional[float] = None):
        """
        Met à jour la vue avec l'orientation actuelle.

        Args:
            theta_x, theta_y, theta_z: Angles (optionnels, récupérés du presenter si None)
        """
        # Vérifier que le plotter est initialisé
        if self.plotter is None:
            print("[DEBUG] update_view: plotter pas encore initialisé")
            return
        
        if theta_x is None or theta_y is None or theta_z is None:
            theta_x, theta_y, theta_z = self.presenter.get_angles()
        
        try:
            rotation = self.presenter.get_rotation()
            
            # Supprimer les anciens acteurs
            if self.cube_actor is not None:
                self.plotter.remove_actor(self.cube_actor)
            for arrow in self.arrows_mes.values():
                self.plotter.remove_actor(arrow)
            for arrow in self.arrows_labo.values():
                self.plotter.remove_actor(arrow)
            if self.text_actor is not None:
                self.plotter.remove_actor(self.text_actor)
            
            self.arrows_mes.clear()
            self.arrows_labo.clear()
            
            # Créer et ajouter le cube
            cube = create_colored_cube(size=1.0)
            cube_rotated = apply_rotation_to_mesh(cube.copy(), rotation)
            
            if "colors" in cube_rotated.cell_data:
                self.cube_actor = self.plotter.add_mesh(
                    cube_rotated,
                    scalars="colors",
                    rgb=True,
                    show_edges=True,
                    edge_color='black',
                    line_width=2,
                    opacity=1.0
                )
            else:
                self.cube_actor = self.plotter.add_mesh(
                    cube_rotated,
                    color='lightgray',
                    show_edges=True,
                    edge_color='black',
                    line_width=2,
                    opacity=1.0
                )
            
            # Ajouter les axes _mes
            axis_length = 0.8
            arrow_radius = 0.05
            
            arrow_x = pv.Arrow(start=(0, 0, 0), direction=(1, 0, 0), scale=axis_length,
                              tip_radius=arrow_radius, tip_length=0.2, shaft_radius=arrow_radius * 0.6)
            self.arrows_mes['x'] = self.plotter.add_mesh(apply_rotation_to_mesh(arrow_x, rotation), color='#4DA6FF')
            
            arrow_y = pv.Arrow(start=(0, 0, 0), direction=(0, 1, 0), scale=axis_length,
                              tip_radius=arrow_radius, tip_length=0.2, shaft_radius=arrow_radius * 0.6)
            self.arrows_mes['y'] = self.plotter.add_mesh(apply_rotation_to_mesh(arrow_y, rotation), color='#FFE633')
            
            arrow_z = pv.Arrow(start=(0, 0, 0), direction=(0, 0, 1), scale=axis_length,
                              tip_radius=arrow_radius, tip_length=0.2, shaft_radius=arrow_radius * 0.6)
            self.arrows_mes['z'] = self.plotter.add_mesh(apply_rotation_to_mesh(arrow_z, rotation), color='#FF3333')
            
            # Ajouter les axes _labo (fixes)
            labo_axis_length = 1.5
            labo_arrow_radius = 0.03
            
            self.arrows_labo['x'] = self.plotter.add_mesh(
                pv.Arrow(start=(0, 0, 0), direction=(1, 0, 0), scale=labo_axis_length,
                        tip_radius=labo_arrow_radius, tip_length=0.15, shaft_radius=labo_arrow_radius * 0.6),
                color='#4DA6FF'
            )
            self.arrows_labo['y'] = self.plotter.add_mesh(
                pv.Arrow(start=(0, 0, 0), direction=(0, 1, 0), scale=labo_axis_length,
                        tip_radius=labo_arrow_radius, tip_length=0.15, shaft_radius=labo_arrow_radius * 0.6),
                color='#FFE633'
            )
            self.arrows_labo['z'] = self.plotter.add_mesh(
                pv.Arrow(start=(0, 0, 0), direction=(0, 0, 1), scale=labo_axis_length,
                        tip_radius=labo_arrow_radius, tip_length=0.15, shaft_radius=labo_arrow_radius * 0.6),
                color='#FF3333'
            )
            
            # Titre selon la vue actuelle
            view_titles = {
                '3d': 'Vue 3D',
                'xy': 'Vue X-Y (Z vers haut)',
                'xz': 'Vue X-Z (Y vers fond)',
                'yz': 'Vue Y-Z (X vers droite)',
            }
            title = view_titles.get(self.current_view, 'Vue 3D')
            
            # Ajouter le texte
            self.text_actor = self.plotter.add_text(
                f"{title} - Rotation: X={theta_x:.1f}° Y={theta_y:.1f}° Z={theta_z:.1f}°",
                position='upper_left',
                font_size=12,
                color='black'
            )
            
            # Pas de sliders PyVista à mettre à jour (redondants avec l'UI Qt)
            print(f"[DEBUG] Appel de plotter.render()...")
            print(f"[DEBUG] Plotter type: {type(self.plotter)}")
            # Pour une fenêtre séparée, plotter_widget est None
            if self.plotter_widget:
                print(f"[DEBUG] Plotter widget visible: {self.plotter_widget.isVisible()}")
                print(f"[DEBUG] Plotter widget size: {self.plotter_widget.size()}")
            else:
                print("[DEBUG] Mode fenêtre séparée (pas de widget Qt)")
            
            # Forcer le rendu
            self.plotter.render()
            print(f"[DEBUG] plotter.render() appelé")
            
            # Pour QtInteractor, il faut parfois forcer un update
            if self.plotter_widget:
                self.plotter_widget.update()
                self.plotter_widget.repaint()
                print(f"[DEBUG] Widget update() et repaint() appelés")
        except Exception as e:
            print(f"[DEBUG] ERREUR lors de update_view: {e}")
            import traceback
            traceback.print_exc()
    
    def get_widget(self):
        """
        Retourne le widget Qt pour intégration dans l'UI.
        
        Returns:
            QWidget: Widget PyVista intégré, ou None si fenêtre séparée ou pas encore créé
        """
        if hasattr(self, 'plotter_widget'):
            return self.plotter_widget
        return None
    
    def show(self):
        """Affiche la fenêtre PyVista (si non intégrée dans Qt)."""
        if self.plotter_widget is None:
            self.plotter.show(auto_close=False, interactive_update=True)
