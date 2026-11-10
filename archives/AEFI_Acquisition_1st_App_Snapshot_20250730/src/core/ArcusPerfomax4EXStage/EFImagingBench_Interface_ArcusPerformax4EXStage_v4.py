# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                            QLineEdit, QGroupBox, QStatusBar, QFrame, 
                            QSpinBox, QDoubleSpinBox, QTabWidget)
from PyQt5.QtCore import QTimer, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPalette, QColor
from datetime import datetime

# Ajout du chemin parent au PYTHONPATH pour permettre l'import du controller
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from .components.EFImagingBench_StageManager_ArcusPerformax4EXStage import StageManager
from .components.EFImagingBench_GeometricalView_Widget import GeometricalViewWidget
from .components.EFImagingBench_GeometricalParametersConversion_Module import (
    get_bench_limits_cm, clamp_rect_cm, inc_to_cm, cm_to_inc
)
from .components.EFImagingBench_DataBuffer_Module import Position_AdaptiveBuffer, PositionSample
from .components.EFImagingBench_AxisControl_Widget import AxisControlWidget
from .components.EFImagingBench_SpeedParameters_Widget import SpeedParametersWidget


# Paramètres
DLL_PATH = r"C:/Users/manip/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/Dev/ArcusPerformaxPythonController/controller/DLL64"


class ArcusGUIModern(QMainWindow):
    """Interface graphique moderne pour le contrôleur Arcus Performax"""
    
    def __init__(self):
        super().__init__()
        self.manager = StageManager(dll_path=DLL_PATH)
        self.start_time = datetime.now()
        
        self.setup_ui()
        self.setup_connections()
        self.setup_timer()
        
        # Configuration initiale
        self.setWindowTitle("🎛️ Arcus Performax XY - Interface Moderne")
        self.setGeometry(100, 100, 800, 600)
        
        # Charger les paramètres actuels
        self.load_current_parameters()
        # Connexion au signal position_changed
        self.manager.position_changed.connect(self._on_position_changed)
        # Connexion au signal status_changed pour activer/désactiver les boutons
        self.manager.status_changed.connect(self._on_state_changed)

    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        control_layout = self.create_control_panel()
        main_layout.addLayout(control_layout)
        tab_widget = QTabWidget()
        # Onglet contrôle des axes + visualisation fusionnée
        control_tab = self.create_control_tab()
        tab_widget.addTab(control_tab, "🎯 Contrôle Axes + Visualisation")
        # Onglet paramètres
        params_tab = self.create_parameters_tab()
        tab_widget.addTab(params_tab, "⚙️ Paramètres")
        main_layout.addWidget(tab_widget)
        central_widget.setLayout(main_layout)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("🔌 Système initialisé")
    
    def create_control_panel(self):
        """Crée le panneau de contrôle général"""
        layout = QHBoxLayout()

        # Bouton Homing X+Y
        self.home_both_btn = QPushButton("🏠 Homing X+Y")
        self.home_both_btn.setStyleSheet("QPushButton { background-color: #2E86AB; color: white; font-weight: bold; padding: 10px; }")
        layout.addWidget(self.home_both_btn)

        # Bouton d'arrêt d'urgence global
        self.emergency_all_btn = QPushButton("🚨 ARRÊT D'URGENCE")
        self.emergency_all_btn.setStyleSheet("QPushButton { background-color: #8B0000; color: white; font-weight: bold; padding: 10px; }")
        layout.addWidget(self.emergency_all_btn)

        # Label statut du mode
        self.mode_status_label = QLabel()
        self.mode_status_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #A23B72;")
        layout.addWidget(self.mode_status_label)

        layout.addStretch()

        return layout
    
    def create_control_tab(self):
        """Crée l'onglet de contrôle des axes + visualisation + config scan à gauche"""
        from PyQt5.QtWidgets import QComboBox
        widget = QWidget()
        layout = QVBoxLayout()
        # Ligne de contrôle des axes
        axes_layout = QHBoxLayout()
        self.x_control = AxisControlWidget("X", "x", "#0000FF", "🔵")
        self.y_control = AxisControlWidget("Y", "y", "#FFA500", "🟠")
        axes_layout.addWidget(self.x_control)
        axes_layout.addWidget(self.y_control)
        layout.addLayout(axes_layout)
        # Fixer la hauteur max des widgets axes à leur taille minimale actuelle
        self.x_control.setMaximumHeight(self.x_control.sizeHint().height())
        self.y_control.setMaximumHeight(self.y_control.sizeHint().height())
        # Zone du bas : config scan à gauche (largeur fixe), visualisation à droite (stretch)
        bottom_layout = QHBoxLayout()
        scan2d_group = QGroupBox("🗺️ Configuration Scan 2D")
        scan2d_layout = QGridLayout()
        scan2d_layout.addWidget(QLabel("x_min (cm) :"), 0, 0)
        self.xmin_input = QDoubleSpinBox()
        self.xmin_input.setRange(-100.0, 100.0)
        self.xmin_input.setDecimals(2)
        scan2d_layout.addWidget(self.xmin_input, 0, 1)
        scan2d_layout.addWidget(QLabel("x_max (cm) :"), 0, 2)
        self.xmax_input = QDoubleSpinBox()
        self.xmax_input.setRange(-100.0, 100.0)
        self.xmax_input.setDecimals(2)
        scan2d_layout.addWidget(self.xmax_input, 0, 3)
        scan2d_layout.addWidget(QLabel("y_min (cm) :"), 1, 0)
        self.ymin_input = QDoubleSpinBox()
        self.ymin_input.setRange(-100.0, 100.0)
        self.ymin_input.setDecimals(2)
        scan2d_layout.addWidget(self.ymin_input, 1, 1)
        scan2d_layout.addWidget(QLabel("y_max (cm) :"), 1, 2)
        self.ymax_input = QDoubleSpinBox()
        self.ymax_input.setRange(-100.0, 100.0)
        self.ymax_input.setDecimals(2)
        scan2d_layout.addWidget(self.ymax_input, 1, 3)
        scan2d_layout.addWidget(QLabel("N (lignes) :"), 2, 0)
        self.n_input = QSpinBox()
        self.n_input.setRange(1, 1000)
        scan2d_layout.addWidget(self.n_input, 2, 1)
        scan2d_layout.addWidget(QLabel("Mode :"), 2, 2)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["E", "S"])
        scan2d_layout.addWidget(self.mode_combo, 2, 3)
        self.generate_btn = QPushButton("Générer le scan")
        self.execute_btn = QPushButton("Exécuter le scan")
        scan2d_layout.addWidget(self.generate_btn, 3, 0, 1, 2)
        scan2d_layout.addWidget(self.execute_btn, 3, 2, 1, 2)
        scan2d_group.setLayout(scan2d_layout)
        scan2d_group.setMaximumWidth(320)
        bottom_layout.addWidget(scan2d_group)
        # Widget de visualisation à droite (stretch)
        self.visual_widget = GeometricalViewWidget()
        bottom_layout.addWidget(self.visual_widget, stretch=1)
        layout.addLayout(bottom_layout)
        widget.setLayout(layout)
        return widget
    
    def create_parameters_tab(self):
        """Crée l'onglet des paramètres"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Widget des paramètres de vitesse
        self.speed_params = SpeedParametersWidget()
        layout.addWidget(self.speed_params)
        
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def setup_connections(self):
        """Configure les connexions des signaux"""
        # Contrôles des axes
        self.x_control.move_btn.clicked.connect(lambda: self.move_axis("x"))
        self.x_control.home_btn.clicked.connect(lambda: self.home_axis("x"))
        self.x_control.stop_btn.clicked.connect(lambda: self.stop_axis("x", False))
        self.x_control.emergency_btn.clicked.connect(lambda: self.stop_axis("x", True))
        self.y_control.move_btn.clicked.connect(lambda: self.move_axis("y"))
        self.y_control.home_btn.clicked.connect(lambda: self.home_axis("y"))
        self.y_control.stop_btn.clicked.connect(lambda: self.stop_axis("y", False))
        self.y_control.emergency_btn.clicked.connect(lambda: self.stop_axis("y", True))
        self.home_both_btn.clicked.connect(self.home_both_axes)
        self.emergency_all_btn.clicked.connect(self.emergency_stop_all)
        self.speed_params.apply_btn.clicked.connect(self.apply_speed_parameters)
        self.manager.position_changed.connect(self._on_position_changed)
        # Connexion des boutons scan
        self.generate_btn.clicked.connect(self._update_subrect_from_ui)
        self.execute_btn.clicked.connect(self._execute_scan2d_from_ui)
    
    def setup_timer(self):
        """Configure le timer pour la mise à jour automatique"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(500)  # Mise à jour toutes les 500ms
    
    def load_current_parameters(self):
        """Charge les paramètres actuels depuis le manager (asynchrone via callback, thread-safe)"""
        try:
            for axis in ["x", "y"]:
                def on_params(params, axis=axis):
                    from PyQt5.QtCore import QTimer
                    def update_ui():
                        self.speed_params.set_params(axis, params)
                        self.status_bar.showMessage(f"✅ Paramètres {axis.upper()} chargés depuis le contrôleur")
                    QTimer.singleShot(0, update_ui)
                self.manager.get_axis_params(axis, callback=on_params)
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur chargement paramètres: {e}")
    
    def move_axis(self, axis):
        """Déplace un axe à la position cible (saisie en cm, convertie en incréments)"""
        try:
            if axis == "x":
                target_cm = self.x_control.get_target_position()
            else:
                target_cm = self.y_control.get_target_position()
            target_inc, _ = cm_to_inc(target_cm)
            self.manager.move_to(axis, target_inc)
            self.status_bar.showMessage(f"🎯 Déplacement axe {axis.upper()} vers {target_cm:.3f} cm")
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur déplacement {axis}: {e}")
    
    def home_axis(self, axis):
        """Lance le homing d'un axe (non bloquant, confirmation réelle)"""
        print(f"[UI] Appel home_axis avec axis={axis}")  # LOG
        try:
            self.manager.home(axis)
            self.status_bar.showMessage(f"🏠 Homing axe {axis.upper()} en cours...")
            # Démarre un timer pour surveiller la fin du mouvement
            self._homing_timer_axis = QTimer(self)
            self._homing_timer_axis.setInterval(200)
            self._homing_timer_axis.timeout.connect(lambda: self._check_homing_axis_done(axis))
            self._homing_timer_axis.start()
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur homing {axis}: {e}")

    def _check_homing_axis_done(self, axis):
        try:
            # Utilisation du callback pour is_moving
            def on_moving(moving):
                from PyQt5.QtCore import QTimer
                def update_ui():
                    if not moving:
                        # Axe arrêté, on fixe la référence à 0
                        self.manager.set_position_reference(axis, 0)
                        self.manager.set_axis_homed(axis, True)
                        self.status_bar.showMessage(f"✅ Homing axe {axis.upper()} terminé. Référence mise à 0.")
                        # Mise à jour affichage position via le buffer
                        latest = self.manager.get_latest_position_samples(1)
                        if latest:
                            x = latest[0].x
                            y = latest[0].y
                            self._on_position_changed(x, y)
                        # Correction : arrêt du timer dans le thread principal pour éviter QObject::killTimer
                        self._homing_timer_axis.stop()
                QTimer.singleShot(0, update_ui)
            self.manager.is_moving(axis, callback=on_moving)
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur vérification homing {axis}: {e}")
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._homing_timer_axis.stop())
    

    def home_both_axes(self):
        """Lance le homing simultané X+Y (non bloquant, confirmation réelle)"""
        print("[UI] Appel home_both_axes (commande HOME_BOTH)")  # LOG
        try:
            self.manager.home_both()
            self.status_bar.showMessage("🏠 Homing X+Y en cours...")
            # Démarre un timer pour surveiller la fin du mouvement
            self._homing_timer = QTimer(self)
            self._homing_timer.setInterval(200)
            self._homing_timer.timeout.connect(self._check_homing_xy_done)
            self._homing_timer.start()
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur homing X+Y: {e}")

    def _check_homing_xy_done(self):
        try:
            # Utilisation du callback pour is_moving sur x puis y
            def on_moving_x(moving_x):
                def on_moving_y(moving_y):
                    from PyQt5.QtCore import QTimer
                    def update_ui():
                        if not moving_x and not moving_y:
                            # Les deux axes sont arrêtés, on fixe la référence à 0
                            self.manager.set_position_reference('x', 0)
                            self.manager.set_position_reference('y', 0)
                            # Marquer comme homed
                            self.manager.set_axis_homed('x', True)
                            self.manager.set_axis_homed('y', True)
                            self.status_bar.showMessage("✅ Homing X+Y terminé. Références mises à 0.")
                            # Mise à jour affichage position via le buffer
                            latest = self.manager.get_latest_position_samples(1)
                            if latest:
                                x = latest[0].x
                                y = latest[0].y
                                self._on_position_changed(x, y)
                            # Correction : arrêt du timer dans le thread principal pour éviter QObject::killTimer
                            self._homing_timer.stop()
                    QTimer.singleShot(0, update_ui)
                self.manager.is_moving('y', callback=on_moving_y)
            self.manager.is_moving('x', callback=on_moving_x)
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur vérification homing: {e}")
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._homing_timer.stop())




    def stop_axis(self, axis, immediate=False):
        """Arrête le mouvement d'un axe"""
        try:
            self.manager.stop(axis, immediate=immediate)
            if immediate:
                self.status_bar.showMessage(f"🛑 Arrêt d'urgence axe {axis.upper()}")
            else:
                self.status_bar.showMessage(f"⏸️ Arrêt contrôlé axe {axis.upper()}")
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur arrêt {axis}: {e}")
    
    def emergency_stop_all(self):
        """Arrêt d'urgence de tous les axes"""
        try:
            for axis in ["x", "y"]:
                self.manager.stop(axis, immediate=True)
            self.status_bar.showMessage("🚨 ARRÊT D'URGENCE GLOBAL ACTIVÉ")
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur arrêt d'urgence: {e}")
    
    def apply_speed_parameters(self):
        """Applique les paramètres de vitesse"""
        try:
            for axis in ["x", "y"]:
                params = self.speed_params.get_params(axis)
                self.manager.set_axis_params(axis, **params)
            self.status_bar.showMessage("🚀 Paramètres de vitesse appliqués avec succès")
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur application paramètres: {e}")
    
    def refresh_all(self):
        """Actualise toutes les données"""
        self.load_current_parameters()
        # Rafraîchit la position via le buffer
        latest = self.manager.get_latest_position_samples(1)
        if latest:
            x = latest[0].x
            y = latest[0].y
            self._on_position_changed(x, y)
        self.status_bar.showMessage("🔄 Données actualisées")
    
    def update_display(self):
        """Met à jour l'affichage en temps réel (statut, uptime)"""
        try:
            # Mise à jour du statut (simplifié)
            for axis in ["x", "y"]:
                # self.status_widget.update_axis_status(axis, "ready") # This line is removed
                pass # This line is added
            # Mise à jour du temps de fonctionnement
            uptime = datetime.now() - self.start_time
            uptime_str = str(uptime).split('.')[0]
            # self.status_widget.uptime_label.setText(f"⏱️ Temps de fonctionnement: {uptime_str}") # This line is removed
        except Exception:
            pass
    
    def _on_position_changed(self, x_inc, y_inc):
        # Conversion inc -> cm pour la visualisation et l'affichage
        x_cm = inc_to_cm(x_inc)
        y_cm = inc_to_cm(y_inc)
        self.visual_widget.set_current_position(x_cm, y_cm)
        # Mise à jour des widgets de contrôle classiques (en cm)
        self.x_control.update_position(x_inc)
        self.y_control.update_position(y_inc)
    
    def update_mode_status(self):
        mode = self.manager.mode
        if mode == self.manager.MODE_EXPLORATION:
            self.mode_status_label.setText("Mode : Exploration")
        else:
            self.mode_status_label.setText("Mode : Export (UI bloquée)")

    def _on_state_changed(self, state):
        if state == "ui_buttons_disabled":
            self._set_all_buttons_enabled(False)
        elif state == "ui_buttons_enabled":
            self._set_all_buttons_enabled(True)
        # Le bouton change_mode_btn n'est jamais désactivé (suppression)

    def _set_all_buttons_enabled(self, enabled):
        # Désactive/active tous les boutons ET champs éditables principaux de l'UI sauf change_mode_btn
        widgets = [
            self.x_control.move_btn, self.x_control.home_btn, self.x_control.stop_btn, self.x_control.emergency_btn,
            self.y_control.move_btn, self.y_control.home_btn, self.y_control.stop_btn, self.y_control.emergency_btn,
            self.home_both_btn, self.emergency_all_btn, self.speed_params.apply_btn,
            # Champs éditables :
            self.x_control.target_input, self.y_control.target_input
        ]
        # Ajoute les spinbox des paramètres de vitesse
        for axis in ["x", "y"]:
            for param in ["ls", "hs", "acc", "dec"]:
                widgets.append(self.speed_params.params[axis][param])
        for w in widgets:
            w.setEnabled(enabled)

    def closeEvent(self, event):
        """Gère la fermeture propre de l'application"""
        try:
            self.manager.close()
            self.status_bar.showMessage("🔌 Contrôleur fermé proprement")
        except:
            pass
        event.accept()

    def set_test_subrect(self):
        # Exemple : sous-rectangle centré, 20x20 cm
        x_max, y_max = self.manager.get_bench_limits_cm()
        x_min = x_max/2 - 10
        x_max_ = x_max/2 + 10
        y_min = y_max/2 - 10
        y_max_ = y_max/2 + 10
        self.visual_widget.set_subrect(x_min, x_max_, y_min, y_max_)

    # --- Ajout méthode pour mettre à jour le sous-rectangle ---
    def _update_subrect_from_ui(self):
        x_min = self.xmin_input.value()
        x_max = self.xmax_input.value()
        y_min = self.ymin_input.value()
        y_max = self.ymax_input.value()
        self.visual_widget.set_subrect(x_min, x_max, y_min, y_max)

    def _execute_scan2d_from_ui(self):
        # Récupère les valeurs de l'UI
        x_min_cm = self.xmin_input.value()
        x_max_cm = self.xmax_input.value()
        y_min_cm = self.ymin_input.value()
        y_max_cm = self.ymax_input.value()
        N = self.n_input.value()
        mode_str = self.mode_combo.currentText()
        mode = 'E' if mode_str.startswith('E') else 'S'
        # Conversion cm -> inc
        x_min_inc, _ = cm_to_inc(x_min_cm)
        x_max_inc, _ = cm_to_inc(x_max_cm)
        y_min_inc, _ = cm_to_inc(y_min_cm)
        y_max_inc, _ = cm_to_inc(y_max_cm)
        # Génération de la séquence de scan
        scan_config = self.manager.generate_scan2d(x_min_inc, x_max_inc, y_min_inc, y_max_inc, N, mode)
        # Désactive les boutons de l'UI pendant l'exécution
        self._set_all_buttons_enabled(False)
        self.status_bar.showMessage("⏳ Scan 2D en cours...")
        try:
            # Remplacement : inject_scan_batch au lieu de execute_flyscan2d
            self.manager.inject_scan_batch(scan_config)
            self.status_bar.showMessage("✅ Scan 2D injecté (batch)")
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur exécution scan : {e}")
        finally:
            self._set_all_buttons_enabled(True)

def main():
    app = QApplication(sys.argv)
    
    # Application du style moderne
    app.setStyle('Fusion')
    
    # Palette de couleurs sombre
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, QColor(0, 0, 0))
    palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)
    
    # Créer et afficher l'interface
    window = ArcusGUIModern()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 