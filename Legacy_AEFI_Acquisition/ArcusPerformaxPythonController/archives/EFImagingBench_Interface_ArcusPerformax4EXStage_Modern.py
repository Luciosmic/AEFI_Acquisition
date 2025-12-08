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

from ArcusPerformaxPythonController.controller.ArcusPerformax4EXStage_Controller import EFImagingStageController

# Paramètres
DLL_PATH = r"C:/Users/manip/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/Dev/ArcusPerformaxPythonController/controller/DLL64"

class AxisControlWidget(QGroupBox):
    """Widget de contrôle pour un axe (X ou Y)"""
    
    def __init__(self, axis_name, axis_key, color='#2E86AB', emoji='📐'):
        super().__init__(f"{emoji} Axe {axis_name}")
        self.axis_key = axis_key
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {color};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)
        
        layout = QGridLayout()
        
        # Position actuelle
        self.pos_label = QLabel("Position:")
        self.pos_value = QLabel("0.00")
        self.pos_value.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
        
        # Position cible
        self.target_label = QLabel("Cible:")
        self.target_input = QDoubleSpinBox()
        self.target_input.setRange(-50000, 50000)
        self.target_input.setValue(14950)
        self.target_input.setDecimals(2)
        self.target_input.setSuffix(" µm")
        self.target_input.setStyleSheet("font-size: 14px; padding: 5px;")
        
        # Boutons de contrôle
        self.move_btn = QPushButton("🎯 Move To")
        self.home_btn = QPushButton("🏠 Home")
        self.stop_btn = QPushButton("⏸️ Stop")
        self.emergency_btn = QPushButton("🛑 STOP!")
        
        # Style des boutons
        self.move_btn.setStyleSheet("QPushButton { background-color: #2A9D8F; font-weight: bold; padding: 8px; }")
        self.home_btn.setStyleSheet("QPushButton { background-color: #F77F00; font-weight: bold; padding: 8px; }")
        self.stop_btn.setStyleSheet("QPushButton { background-color: #E63946; font-weight: bold; padding: 8px; }")
        self.emergency_btn.setStyleSheet("QPushButton { background-color: #8B0000; color: white; font-weight: bold; padding: 8px; }")
        
        # Disposition
        layout.addWidget(self.pos_label, 0, 0)
        layout.addWidget(self.pos_value, 0, 1)
        layout.addWidget(self.target_label, 1, 0)
        layout.addWidget(self.target_input, 1, 1)
        layout.addWidget(self.move_btn, 2, 0)
        layout.addWidget(self.home_btn, 2, 1)
        layout.addWidget(self.stop_btn, 3, 0)
        layout.addWidget(self.emergency_btn, 3, 1)
        
        self.setLayout(layout)
    
    def update_position(self, position):
        """Met à jour l'affichage de la position"""
        self.pos_value.setText(f"{position:.2f} µm")
    
    def get_target_position(self):
        """Retourne la position cible"""
        return self.target_input.value()

class SpeedParametersWidget(QGroupBox):
    """Widget pour les paramètres de vitesse et accélération"""
    
    def __init__(self):
        super().__init__("⚙️ Paramètres de Vitesse & Accélération")
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #A23B72;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = QGridLayout()
        
        # En-têtes
        headers = ["", "Low Speed", "High Speed", "Acceleration", "Deceleration"]
        for i, header in enumerate(headers):
            if header:
                label = QLabel(header)
                label.setStyleSheet("font-weight: bold; color: #A23B72;")
                layout.addWidget(label, 0, i)
        
        # Paramètres pour X et Y
        self.params = {}
        colors = ["#0000FF", "#FFA500"]  # Bleu pour X, Orange pour Y
        
        for row, (axis, color) in enumerate([("X", colors[0]), ("Y", colors[1])]):
            axis_key = axis.lower()
            
            # Label de l'axe
            axis_label = QLabel(f"Axe {axis}")
            axis_label.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 14px;")
            layout.addWidget(axis_label, row + 1, 0)
            
            # Paramètres
            self.params[axis_key] = {}
            param_names = ["ls", "hs", "acc", "dec"]
            default_values = [10, 800, 300, 300]
            
            for col, (param, default) in enumerate(zip(param_names, default_values)):
                spinbox = QSpinBox()
                spinbox.setRange(1, 10000)
                spinbox.setValue(default)
                spinbox.setStyleSheet("font-size: 12px; padding: 3px;")
                layout.addWidget(spinbox, row + 1, col + 1)
                self.params[axis_key][param] = spinbox
        
        # Bouton d'application
        self.apply_btn = QPushButton("🚀 Appliquer Paramètres")
        self.apply_btn.setStyleSheet("QPushButton { background-color: #2E86AB; font-weight: bold; padding: 10px; }")
        layout.addWidget(self.apply_btn, 3, 0, 1, 5)
        
        self.setLayout(layout)
    
    def get_params(self, axis):
        """Retourne les paramètres d'un axe"""
        return {
            'ls': self.params[axis]['ls'].value(),
            'hs': self.params[axis]['hs'].value(),
            'acc': self.params[axis]['acc'].value(),
            'dec': self.params[axis]['dec'].value()
        }
    
    def set_params(self, axis, params):
        """Met à jour les paramètres affichés"""
        for param_name, value in params.items():
            if param_name in self.params[axis]:
                self.params[axis][param_name].setValue(value)

class SystemStatusWidget(QGroupBox):
    """Widget d'affichage du statut système"""
    
    def __init__(self):
        super().__init__("📊 Statut Système")
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #2A9D8F;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # État des axes
        self.x_status = QLabel("❌ Axe X: Déconnecté")
        self.y_status = QLabel("❌ Axe Y: Déconnecté")
        
        # Mise à jour des couleurs
        self.x_status.setStyleSheet("font-size: 12px; font-weight: bold; color: #0000FF;")
        self.y_status.setStyleSheet("font-size: 12px; font-weight: bold; color: #FFA500;")
        
        # Temps de fonctionnement
        self.uptime_label = QLabel("⏱️ Temps de fonctionnement: 00:00:00")
        self.uptime_label.setStyleSheet("font-size: 12px; color: #2A9D8F;")
        
        layout.addWidget(self.x_status)
        layout.addWidget(self.y_status)
        layout.addWidget(self.uptime_label)
        
        self.setLayout(layout)
    
    def update_axis_status(self, axis, status):
        """Met à jour le statut d'un axe"""
        color = "#0000FF" if axis == "x" else "#FFA500"
        icon = "✅" if status == "ready" else "🔄" if status == "moving" else "❌"
        text = f"{icon} Axe {axis.upper()}: {status.title()}"
        
        if axis == "x":
            self.x_status.setText(text)
        else:
            self.y_status.setText(text)

class ArcusGUIModern(QMainWindow):
    """Interface graphique moderne pour le contrôleur Arcus Performax"""
    
    def __init__(self):
        super().__init__()
        self.controller = EFImagingStageController(DLL_PATH)
        self.start_time = datetime.now()
        
        self.setup_ui()
        self.setup_connections()
        self.setup_timer()
        
        # Configuration initiale
        self.setWindowTitle("🎛️ Arcus Performax XY - Interface Moderne")
        self.setGeometry(100, 100, 800, 600)
        
        # Charger les paramètres actuels
        self.load_current_parameters()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout()
        
        # Barre de contrôle général
        control_layout = self.create_control_panel()
        main_layout.addLayout(control_layout)
        
        # Contenu principal avec onglets
        tab_widget = QTabWidget()
        
        # Onglet contrôle des axes
        control_tab = self.create_control_tab()
        tab_widget.addTab(control_tab, "🎯 Contrôle Axes")
        
        # Onglet paramètres
        params_tab = self.create_parameters_tab()
        tab_widget.addTab(params_tab, "⚙️ Paramètres")
        
        # --- Ajout de l'onglet Visualisation avec panneau de configuration du scan 2D ---
        visual_tab = QWidget()
        visual_layout = QVBoxLayout()
        # Panneau de configuration du scan 2D
        scan2d_group = QGroupBox("🗺️ Configuration Scan 2D")
        scan2d_layout = QGridLayout()
        # Inputs x_min, x_max, y_min, y_max (en cm)
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
        # Input N (nombre de lignes)
        scan2d_layout.addWidget(QLabel("N (lignes) :"), 2, 0)
        self.n_input = QSpinBox()
        self.n_input.setRange(1, 1000)
        scan2d_layout.addWidget(self.n_input, 2, 1)
        # Mode (E/S)
        scan2d_layout.addWidget(QLabel("Mode :"), 2, 2)
        from PyQt5.QtWidgets import QComboBox
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Entrée", "Sortie"])
        scan2d_layout.addWidget(self.mode_combo, 2, 3)
        # Boutons Générer et Exécuter
        self.generate_btn = QPushButton("Générer le scan")
        self.execute_btn = QPushButton("Exécuter le scan")
        scan2d_layout.addWidget(self.generate_btn, 3, 0, 1, 2)
        scan2d_layout.addWidget(self.execute_btn, 3, 2, 1, 2)
        scan2d_group.setLayout(scan2d_layout)
        visual_layout.addWidget(scan2d_group)
        visual_layout.addStretch()
        visual_tab.setLayout(visual_layout)
        tab_widget.addTab(visual_tab, "🗺️ Visualisation")
        # --- Fin ajout ---
        
        main_layout.addWidget(tab_widget)
        
        central_widget.setLayout(main_layout)
        
        # Barre de statut
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("🔌 Système initialisé")
    
    def create_control_panel(self):
        """Crée le panneau de contrôle général"""
        layout = QHBoxLayout()
        
        # Bouton de connexion/déconnexion
        self.connect_btn = QPushButton("🔌 Connecter")
        self.connect_btn.setStyleSheet("QPushButton { background-color: #2A9D8F; font-weight: bold; padding: 10px; }")
        layout.addWidget(self.connect_btn)
        
        # Bouton d'arrêt d'urgence global
        self.emergency_all_btn = QPushButton("🚨 ARRÊT D'URGENCE GLOBAL")
        self.emergency_all_btn.setStyleSheet("QPushButton { background-color: #8B0000; color: white; font-weight: bold; padding: 10px; }")
        layout.addWidget(self.emergency_all_btn)
        
        layout.addStretch()
        
        # Bouton de rafraîchissement
        self.refresh_btn = QPushButton("🔄 Actualiser")
        self.refresh_btn.setStyleSheet("QPushButton { background-color: #F77F00; font-weight: bold; padding: 10px; }")
        layout.addWidget(self.refresh_btn)
        
        return layout
    
    def create_control_tab(self):
        """Crée l'onglet de contrôle des axes"""
        widget = QWidget()
        layout = QGridLayout()
        
        # Widgets de contrôle des axes
        self.x_control = AxisControlWidget("X", "x", "#0000FF", "🔵")
        self.y_control = AxisControlWidget("Y", "y", "#FFA500", "🟠")
        
        # Widget de statut système
        self.status_widget = SystemStatusWidget()
        
        # Disposition
        layout.addWidget(self.x_control, 0, 0)
        layout.addWidget(self.y_control, 0, 1)
        layout.addWidget(self.status_widget, 1, 0, 1, 2)
        
        widget.setLayout(layout)
        return widget
    
    def create_parameters_tab(self):
        """Crée l'onglet des paramètres"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Widget des paramètres de vitesse
        self.speed_params = SpeedParametersWidget()
        layout.addWidget(self.speed_params)
        
        # Informations système
        info_group = QGroupBox("ℹ️ Informations Système")
        info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #2E86AB;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        info_layout = QVBoxLayout()
        self.dll_path_label = QLabel(f"📁 DLL Path: {DLL_PATH}")
        self.controller_info = QLabel("🎛️ Contrôleur: EF Imaging Bench - Arcus Performax 4EX Stage")
        self.version_label = QLabel("📋 Version: 2.0 Modern")
        
        info_layout.addWidget(self.dll_path_label)
        info_layout.addWidget(self.controller_info)
        info_layout.addWidget(self.version_label)
        info_group.setLayout(info_layout)
        
        layout.addWidget(info_group)
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
        
        # Contrôles généraux
        self.emergency_all_btn.clicked.connect(self.emergency_stop_all)
        self.refresh_btn.clicked.connect(self.refresh_all)
        
        # Paramètres
        self.speed_params.apply_btn.clicked.connect(self.apply_speed_parameters)
    
    def setup_timer(self):
        """Configure le timer pour la mise à jour automatique"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(500)  # Mise à jour toutes les 500ms
    
    def load_current_parameters(self):
        """Charge les paramètres actuels depuis le contrôleur"""
        try:
            for axis in ["x", "y"]:
                params = self.controller.get_axis_params(axis)
                self.speed_params.set_params(axis, params)
            self.status_bar.showMessage("✅ Paramètres chargés depuis le contrôleur")
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur chargement paramètres: {e}")
    
    def move_axis(self, axis):
        """Déplace un axe à la position cible"""
        try:
            if axis == "x":
                target = self.x_control.get_target_position()
            else:
                target = self.y_control.get_target_position()
            
            self.controller.move_to(axis, target)
            self.status_bar.showMessage(f"🎯 Déplacement axe {axis.upper()} vers {target:.2f} µm")
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur déplacement {axis}: {e}")
    
    def home_axis(self, axis):
        """Lance le homing d'un axe"""
        try:
            self.controller.home(axis)
            self.status_bar.showMessage(f"🏠 Homing axe {axis.upper()} en cours...")
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur homing {axis}: {e}")
    
    def stop_axis(self, axis, immediate=False):
        """Arrête le mouvement d'un axe"""
        try:
            self.controller.stop(axis, immediate=immediate)
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
                self.controller.stop(axis, immediate=True)
            self.status_bar.showMessage("🚨 ARRÊT D'URGENCE GLOBAL ACTIVÉ")
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur arrêt d'urgence: {e}")
    
    def apply_speed_parameters(self):
        """Applique les paramètres de vitesse"""
        try:
            for axis in ["x", "y"]:
                params = self.speed_params.get_params(axis)
                self.controller.set_axis_params(axis, **params)
            self.status_bar.showMessage("🚀 Paramètres de vitesse appliqués avec succès")
        except Exception as e:
            self.status_bar.showMessage(f"❌ Erreur application paramètres: {e}")
    
    def refresh_all(self):
        """Actualise toutes les données"""
        self.load_current_parameters()
        self.status_bar.showMessage("🔄 Données actualisées")
    
    def update_display(self):
        """Met à jour l'affichage en temps réel"""
        try:
            # Mise à jour des positions
            for axis in ["x", "y"]:
                position = self.controller.get_position(axis)
                if axis == "x":
                    self.x_control.update_position(position)
                else:
                    self.y_control.update_position(position)
                
                # Mise à jour du statut (simplifié)
                self.status_widget.update_axis_status(axis, "ready")
            
            # Mise à jour du temps de fonctionnement
            uptime = datetime.now() - self.start_time
            uptime_str = str(uptime).split('.')[0]  # Enlever les microsecondes
            self.status_widget.uptime_label.setText(f"⏱️ Temps de fonctionnement: {uptime_str}")
            
        except Exception:
            # En cas d'erreur, on continue silencieusement
            pass
    
    def closeEvent(self, event):
        """Gère la fermeture propre de l'application"""
        try:
            self.controller.close()
            self.status_bar.showMessage("🔌 Contrôleur fermé proprement")
        except:
            pass
        event.accept()

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