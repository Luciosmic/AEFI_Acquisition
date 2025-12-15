#!/usr/bin/env python3
"""
Widget de sélection de direction d'excitation avec visualisation des 4 sphères
- Choix entre excitations X, Y, circulaires
- Visualisation colorée des 4 sphères selon DDS1, DDS1bar, DDS2, DDS2bar
- Gestion des phases relatives pour direction d'excitation
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QGroupBox, QGridLayout)
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt5.QtCore import Qt, pyqtSignal
import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from EFImagingBench_ExcitationDirection_Module import ExcitationConfig
        


class SphereVisualizationWidget(QWidget):
    """Widget de visualisation des 4 sphères avec coloration selon excitation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(100, 80)   # Taille plus compacte pour 4 sphères
        self.setMaximumSize(130, 100)  # Taille maximale réduite
        
        # État des sphères : mapping 1,2,3,4 → DDS1, DDS1_bar, DDS2, DDS2_bar
        self.sphere_colors = {
            'out1': QColor(100, 100, 100),      # Out1 = DDS1 (Gris par défaut)
            'out2': QColor(100, 100, 100),      # Out2 = DDS1_bar 
            'out3': QColor(100, 100, 100),      # Out3 = DDS2
            'out4': QColor(100, 100, 100)       # Out4 = DDS2_bar
        }
        
    def set_excitation_mode(self, mode: str):
        """Met à jour les couleurs selon le mode d'excitation"""
        red = QColor(230, 57, 70)    # Rouge
        blue = QColor(46, 134, 171)  # Bleu
        gray = QColor(120, 120, 120) # Gris neutre
        
        if mode == "ydir":
            # DDS1 et DDS2 en opposition → excitation Y
            self.sphere_colors = {
                'out1': red,     # Out1=DDS1 : Rouge (phase 0°)
                'out2': blue,    # Out2=DDS1_bar : Bleu (phase 180°)
                'out3': blue,    # Out3=DDS2 : Bleu (phase 180°)
                'out4': red      # Out4=DDS2_bar : Rouge (phase 0°)
            }
        elif mode == "xdir":
            # DDS1 et DDS2 en phase → excitation X
            self.sphere_colors = {
                'out1': red,     # Out1=DDS1 : Rouge (phase 0°)
                'out2': blue,    # Out2=DDS1_bar : Bleu (phase 180°)
                'out3': red,     # Out3=DDS2 : Rouge (phase 0°)
                'out4': blue     # Out4=DDS2_bar : Bleu (phase 180°)
            }
        elif mode == "circ+":
            # Excitation circulaire + (DDS2 en quadrature +90°)
            light_red = QColor(255, 150, 150)
            light_blue = QColor(150, 150, 255)
            self.sphere_colors = {
                'out1': red,        # Out1=DDS1 : Rouge (phase 0°)
                'out2': blue,       # Out2=DDS1_bar : Bleu (phase 180°)
                'out3': light_red,  # Out3=DDS2 : Rouge clair (phase 90°)
                'out4': light_blue  # Out4=DDS2_bar : Bleu clair (phase 270°)
            }
        elif mode == "circ-":
            # Excitation circulaire - (DDS2 en quadrature -90°)
            light_red = QColor(255, 150, 150)
            light_blue = QColor(150, 150, 255)
            self.sphere_colors = {
                'out1': red,        # Out1=DDS1 : Rouge (phase 0°)
                'out2': blue,       # Out2=DDS1_bar : Bleu (phase 180°)
                'out3': light_blue, # Out3=DDS2 : Bleu clair (phase -90°)
                'out4': light_red   # Out4=DDS2_bar : Rouge clair (phase 90°)
            }
        elif mode == "custom":
            # Mode custom : couleurs neutres mais distinguées du mode off
            custom_color = QColor(180, 180, 120)  # Jaune-gris pour indiquer un mode personnalisé
            self.sphere_colors = {k: custom_color for k in self.sphere_colors.keys()}
        else:
            # Mode off ou inconnu
            self.sphere_colors = {k: gray for k in self.sphere_colors.keys()}
        
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Disposition 2x2 des sphères
        sphere_size = min(w//3, h//3)
        margin_x = (w - 2*sphere_size) // 3
        margin_y = (h - 2*sphere_size) // 3
        
        # Positions des sphères selon mapping 1,2,3,4 (image de référence)
        positions = {
            'out1': (margin_x, margin_y + sphere_size + margin_y),               # Out1: Bas gauche
            'out2': (margin_x + sphere_size + margin_x, margin_y),               # Out2: Haut droite  
            'out3': (margin_x, margin_y),                                        # Out3: Haut gauche
            'out4': (margin_x + sphere_size + margin_x, margin_y + sphere_size + margin_y) # Out4: Bas droite
        }
        
        # Dessiner les sphères
        for out_name, (x, y) in positions.items():
            color = self.sphere_colors[out_name]
            
            # Sphère avec effet 3D
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.drawEllipse(x, y, sphere_size, sphere_size)
            
            # Highlight pour effet 3D
            highlight_color = QColor(255, 255, 255, 100)
            painter.setBrush(QBrush(highlight_color))
            painter.setPen(QPen(Qt.NoPen))
            painter.drawEllipse(x + sphere_size//4, y + sphere_size//4, 
                              sphere_size//3, sphere_size//3)
        
        # Labels Out1, Out2, Out3, Out4
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.setFont(QFont("Arial", 8, QFont.Bold))
        
        for out_name, (x, y) in positions.items():
            label = out_name.upper()  # OUT1, OUT2, OUT3, OUT4
            painter.drawText(x + 5, y + sphere_size + 15, label)


class ExcitationDirectionWidget(QWidget):
    """Widget principal pour la sélection de direction d'excitation"""
    
    # Signal émis quand la direction change
    excitation_changed = pyqtSignal(str, dict)  # mode, phase_config
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Contraintes de taille pour garder le widget compact
        self.setMaximumSize(300, 120)  # Largeur max 300px, hauteur max 120px
        self.setMinimumSize(200, 80)   # Taille minimale fonctionnelle
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)  # Marges réduites
        layout.setSpacing(3)  # Espacement réduit entre éléments
        
        # Titre
        # title = QLabel("🎯 Direction d'Excitation")
        # title.setAlignment(Qt.AlignCenter)
        # title.setStyleSheet("font-weight: bold; font-size: 14px; color: #2E86AB; padding: 5px;")
        # layout.addWidget(title)
        
        # Layout horizontal pour combo + visualisation
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)  # Pas de marges internes
        content_layout.setSpacing(8)  # Espacement réduit entre combo et visualisation
        
        # Sélecteur de mode
        selector_layout = QVBoxLayout()
        selector_layout.setContentsMargins(0, 0, 0, 0)
        selector_layout.setSpacing(2)  # Espacement minimal entre label et combobox
        
        mode_label = QLabel("Mode :")
        mode_label.setStyleSheet("font-weight: bold; color: white;")
        selector_layout.addWidget(mode_label)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Off",
            "X Direction", 
            "Y Direction",
            "Circulaire +",
            "Circulaire -",
            "Custom"
        ])
        self.mode_combo.setStyleSheet("""
            QComboBox {
                background-color: #353535;
                color: white;
                border: 1px solid #2E86AB;
                border-radius: 4px;
                padding: 5px;
                min-width: 120px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
            }
            QComboBox QAbstractItemView {
                background-color: #353535;
                color: white;
                selection-background-color: #2E86AB;
            }
        """)
        
        selector_layout.addWidget(self.mode_combo)
        selector_layout.addStretch()
        
        content_layout.addLayout(selector_layout)
        
        # Visualisation des sphères
        self.sphere_widget = SphereVisualizationWidget()
        content_layout.addWidget(self.sphere_widget, stretch=1)
        
        layout.addLayout(content_layout)
        
        # Connexions
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        
        # Initialisation
        self._on_mode_changed("Off")
    
    def _on_mode_changed(self, mode_text: str):
        """Gestion du changement de mode d'excitation"""
        
        # Mapping texte → code interne
        mode_mapping = {
            "Off": "off",
            "X Direction": "xdir", 
            "Y Direction": "ydir",
            "Circulaire +": "circ+",
            "Circulaire -": "circ-",
            "Custom": "custom"
        }
        
        mode_code = mode_mapping.get(mode_text, "off")
        
        # Mettre à jour la visualisation
        self.sphere_widget.set_excitation_mode(mode_code)
        
        # Calculer la configuration complète (phases + gains)
        complete_config = self._get_complete_config(mode_code)
        
        # Émettre le signal avec la configuration complète
        self.excitation_changed.emit(mode_code, complete_config)
    
    def _get_complete_config(self, mode: str) -> dict:
        """Utilise le module ExcitationConfig pour obtenir la configuration"""
        return ExcitationConfig.get_config(mode)
    
    def _get_phase_config(self, mode: str) -> dict:
        """Retourne la configuration de phases DDS pour le mode donné (DDS1 et DDS2 seulement)"""
        
        if mode == "xdir":
            # DDS1 et DDS2 en phase → excitation X
            return {
                'phase_dds1': 0,     # DDS1 : 0°
                'phase_dds2': 0      # DDS2 : 0° (en phase)
                # DDS3 et DDS4 non modifiés (détection synchrone)
            }
        elif mode == "ydir":
            # DDS1 et DDS2 en opposition → excitation Y
            return {
                'phase_dds1': 0,     # DDS1 : 0°
                'phase_dds2': 32768  # DDS2 : 180° (opposition de phase)
                # DDS3 et DDS4 non modifiés (détection synchrone)
            }
        elif mode == "circ+":
            # DDS2 en quadrature +90° par rapport à DDS1
            return {
                'phase_dds1': 0,     # DDS1 : 0°
                'phase_dds2': 16384  # DDS2 : 90° (quadrature +)
                # DDS3 et DDS4 non modifiés (détection synchrone)
            }
        elif mode == "circ-":
            # DDS2 en quadrature -90° par rapport à DDS1
            return {
                'phase_dds1': 0,     # DDS1 : 0°
                'phase_dds2': 49152  # DDS2 : 270° (quadrature -)
                # DDS3 et DDS4 non modifiés (détection synchrone)
            }
        else:  # "off"
            return {
                'phase_dds1': 0,
                'phase_dds2': 0
                # DDS3 et DDS4 non modifiés (détection synchrone)
            }
    
    def detect_mode_from_config(self, config: dict) -> str:
        """Utilise le module ExcitationConfig pour détecter le mode"""
        return ExcitationConfig.detect_mode(config)

    def sync_from_hardware_config(self, hardware_config: dict):
        """Synchronise l'UI avec la configuration hardware actuelle"""
        
        # Détection automatique du mode à partir de la config hardware
        detected_mode = self.detect_mode_from_config(hardware_config)
        
        # Mise à jour du sélecteur sans déclencher le signal
        self.mode_combo.blockSignals(True)
        try:
            reverse_mapping = {
                "off": "Off",
                "xdir": "X Direction",
                "ydir": "Y Direction", 
                "circ+": "Circulaire +",
                "circ-": "Circulaire -",
                "custom": "Custom"
            }
            
            if detected_mode in reverse_mapping:
                self.mode_combo.setCurrentText(reverse_mapping[detected_mode])
                
            # Mise à jour de la visualisation
            self.sphere_widget.set_excitation_mode(detected_mode)
            
        finally:
            self.mode_combo.blockSignals(False)

    def set_mode(self, mode: str):
        """Définit le mode d'excitation par programmation"""
        reverse_mapping = {
            "off": "Off",
            "xdir": "X Direction",
            "ydir": "Y Direction",
            "circ+": "Circulaire +",
            "circ-": "Circulaire -",
            "custom": "Custom" # Ajout du mode Custom
        }
        
        if mode in reverse_mapping:
            self.mode_combo.setCurrentText(reverse_mapping[mode]) 