"""
Test interactif pour isoler le problème de rendu.

Ce script trace progressivement différents éléments et demande à l'utilisateur
ce qu'il voit à chaque étape.
"""
import sys
import os
import moderngl
import numpy as np
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import QTimer

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from infrastructure.rendering.cube_visualizer_adapter_modern_gl import CubeVisualizerAdapterModernGL
from application.services.cube_visualizer_service import CubeVisualizerService
from infrastructure.messaging.event_bus import EventBus
from infrastructure.messaging.command_bus import CommandBus


class InteractiveTestWindow(QWidget):
    """Fenêtre de test interactive."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Interactif - Rendu Cube")
        self.setGeometry(100, 100, 1000, 700)
        
        layout = QVBoxLayout(self)
        
        # Label d'instructions
        self.instruction_label = QLabel("Cliquez sur 'Étape 1: Fond' pour commencer")
        layout.addWidget(self.instruction_label)
        
        # Widget OpenGL
        command_bus = CommandBus()
        event_bus = EventBus()
        self.service = CubeVisualizerService(command_bus=command_bus, event_bus=event_bus)
        
        self.adapter = CubeVisualizerAdapterModernGL(
            service=self.service,
            event_bus=event_bus,
            parent=self
        )
        layout.addWidget(self.adapter)
        
        # Boutons de test
        self.btn_step1 = QPushButton("Étape 1: Fond coloré (gris)")
        self.btn_step1.clicked.connect(self.test_background)
        layout.addWidget(self.btn_step1)
        
        self.btn_step2 = QPushButton("Étape 2: Triangle simple")
        self.btn_step2.clicked.connect(self.test_triangle)
        layout.addWidget(self.btn_step2)
        
        self.btn_step3 = QPushButton("Étape 3: Grille")
        self.btn_step3.clicked.connect(self.test_grid)
        layout.addWidget(self.btn_step3)
        
        self.btn_step4 = QPushButton("Étape 4: Axes")
        self.btn_step4.clicked.connect(self.test_axes)
        layout.addWidget(self.btn_step4)
        
        self.btn_step5 = QPushButton("Étape 5: Cube complet")
        self.btn_step5.clicked.connect(self.test_full_cube)
        layout.addWidget(self.btn_step5)
        
        self.current_step = 0
    
    def test_background(self):
        """Test 1: Fond coloré pour vérifier que le widget rend."""
        print("\n" + "="*60)
        print("ÉTAPE 1: FOND COLORÉ")
        print("="*60)
        print("Le fond devrait être GRIS CLAIR (pas blanc)")
        print("Question: Voyez-vous un fond GRIS dans la zone de visualisation ?")
        print("(Répondez 'oui' ou 'non' dans la console)")
        
        # Modifier le clear color dans paintGL
        # On va patcher temporairement
        original_paintGL = self.adapter.paintGL
        
        def paintGL_with_gray_background():
            self.adapter.makeCurrent()
            
            if not self.adapter.ctx or not self.adapter.prog:
                return
            width = self.adapter.width()
            height = self.adapter.height()
            if width > 0 and height > 0:
                self.adapter.ctx.viewport = (0, 0, width, height)
            # Fond GRIS pour être visible
            self.adapter.ctx.clear(0.7, 0.7, 0.7, 1.0)  # Gris moyen
        
        self.adapter.paintGL = paintGL_with_gray_background
        self.adapter.update()
        QApplication.processEvents()
        
        self.instruction_label.setText("Étape 1: Voyez-vous un fond GRIS ? (répondez dans la console)")
        self.current_step = 1
    
    def test_triangle(self):
        """Test 2: Triangle simple pour vérifier le pipeline OpenGL."""
        print("\n" + "="*60)
        print("ÉTAPE 2: TRIANGLE SIMPLE")
        print("="*60)
        print("Un triangle coloré (rouge, vert, bleu) devrait apparaître")
        print("Question: Voyez-vous un triangle coloré ?")
        
        # Attendre que le contexte soit initialisé
        if not self.adapter.ctx:
            print("ERREUR: Contexte OpenGL non initialisé! Attendez que initializeGL soit appelé.")
            self.instruction_label.setText("ERREUR: Contexte non initialisé. Fermez et rouvrez la fenêtre.")
            return
        
        # S'assurer que le contexte est actif
        self.adapter.makeCurrent()
        
        # Créer un triangle simple (plus grand et centré, proche de l'origine)
        # Triangle plus grand et bien positionné dans le frustum
        vertices = np.array([
            [0.0, 0.5, 0.0],    # Top (devant la caméra)
            [-0.5, -0.5, 0.0],  # Bottom left
            [0.5, -0.5, 0.0],   # Bottom right
        ], dtype='f4')
        
        colors = np.array([
            [1.0, 0.0, 0.0],  # Red
            [0.0, 1.0, 0.0],  # Green
            [0.0, 0.0, 1.0],  # Blue
        ], dtype='f4')
        
        vbo_v = self.adapter.ctx.buffer(vertices.tobytes())
        vbo_c = self.adapter.ctx.buffer(colors.tobytes())
        
        triangle_vao = self.adapter.ctx.vertex_array(
            self.adapter.prog,
            [(vbo_v, '3f', 'in_position'), (vbo_c, '3f', 'in_color')]
        )
        
        original_paintGL = self.adapter.paintGL
        
        def paintGL_with_triangle():
            # S'assurer que le contexte est actif
            self.adapter.makeCurrent()
            
            if not self.adapter.ctx or not self.adapter.prog:
                return
            width = self.adapter.width()
            height = self.adapter.height()
            if width > 0 and height > 0:
                self.adapter.ctx.viewport = (0, 0, width, height)
            self.adapter.ctx.clear(0.5, 0.5, 0.5, 1.0)  # Fond gris
            
            # Désactiver temporairement le depth test pour le triangle
            self.adapter.ctx.disable(moderngl.DEPTH_TEST)
            
            # Utiliser la même matrice MVP que pour le cube (avec projection)
            mvp = self.adapter._get_mvp_matrix()
            self.adapter.prog['mvp'].write(mvp.astype('f4').tobytes())
            
            triangle_vao.render(moderngl.TRIANGLES)
            
            # Réactiver le depth test
            self.adapter.ctx.enable(moderngl.DEPTH_TEST)
        
        self.adapter.paintGL = paintGL_with_triangle
        self.adapter.update()
        QApplication.processEvents()
        
        self.instruction_label.setText("Étape 2: Voyez-vous un triangle coloré ?")
        self.current_step = 2
    
    def test_grid(self):
        """Test 3: Grille seule."""
        print("\n" + "="*60)
        print("ÉTAPE 3: GRILLE")
        print("="*60)
        print("Une grille grise devrait apparaître")
        print("Question: Voyez-vous une grille ?")
        
        if not self.adapter.ctx:
            print("ERREUR: Contexte OpenGL non initialisé!")
            return
        
        self.adapter.makeCurrent()
        
        original_paintGL = self.adapter.paintGL
        
        def paintGL_with_grid():
            self.adapter.makeCurrent()
            
            if not self.adapter.ctx or not self.adapter.prog:
                return
            width = self.adapter.width()
            height = self.adapter.height()
            if width > 0 and height > 0:
                self.adapter.ctx.viewport = (0, 0, width, height)
            self.adapter.ctx.clear(1.0, 1.0, 1.0, 1.0)  # Fond blanc
            
            # MVP
            mvp = self.adapter._get_mvp_matrix()
            self.adapter.prog['mvp'].write(mvp.astype('f4').tobytes())
            
            if self.adapter.grid_vao:
                self.adapter.grid_vao.render(moderngl.LINES)
            else:
                print("[DEBUG] grid_vao est None!")
        
        self.adapter.paintGL = paintGL_with_grid
        self.adapter.update()
        QApplication.processEvents()
        
        self.instruction_label.setText("Étape 3: Voyez-vous une grille ?")
        self.current_step = 3
    
    def test_axes(self):
        """Test 4: Axes seuls."""
        print("\n" + "="*60)
        print("ÉTAPE 4: AXES")
        print("="*60)
        print("Des axes colorés (bleu, jaune, rouge) devraient apparaître")
        print("Question: Voyez-vous des axes colorés ?")
        
        if not self.adapter.ctx:
            print("ERREUR: Contexte OpenGL non initialisé!")
            return
        
        self.adapter.makeCurrent()
        
        original_paintGL = self.adapter.paintGL
        
        def paintGL_with_axes():
            self.adapter.makeCurrent()
            
            if not self.adapter.ctx or not self.adapter.prog:
                return
            width = self.adapter.width()
            height = self.adapter.height()
            if width > 0 and height > 0:
                self.adapter.ctx.viewport = (0, 0, width, height)
            self.adapter.ctx.clear(1.0, 1.0, 1.0, 1.0)
            
            mvp = self.adapter._get_mvp_matrix()
            self.adapter.prog['mvp'].write(mvp.astype('f4').tobytes())
            
            if not self.adapter.axes_vaos:
                print("[DEBUG] axes_vaos est vide!")
            else:
                for vao, _ in self.adapter.axes_vaos:
                    vao.render(moderngl.LINES)
        
        self.adapter.paintGL = paintGL_with_axes
        self.adapter.update()
        QApplication.processEvents()
        
        self.instruction_label.setText("Étape 4: Voyez-vous des axes colorés ?")
        self.current_step = 4
    
    def test_full_cube(self):
        """Test 5: Cube complet."""
        print("\n" + "="*60)
        print("ÉTAPE 5: CUBE COMPLET")
        print("="*60)
        print("Le cube complet avec grille et axes devrait apparaître")
        print("Question: Voyez-vous le cube coloré ?")
        
        if not self.adapter.ctx:
            print("ERREUR: Contexte OpenGL non initialisé!")
            return
        
        self.adapter.makeCurrent()
        
        # Utiliser le paintGL original de l'adapter
        original_paintGL = self.adapter.__class__.paintGL
        
        def paintGL_full():
            self.adapter.makeCurrent()
            
            if not self.adapter.ctx or not self.adapter.prog:
                return
            width = self.adapter.width()
            height = self.adapter.height()
            if width > 0 and height > 0:
                self.adapter.ctx.viewport = (0, 0, width, height)
            self.adapter.ctx.clear(1.0, 1.0, 1.0, 1.0)
            
            mvp = self.adapter._get_mvp_matrix()
            self.adapter.prog['mvp'].write(mvp.astype('f4').tobytes())
            
            if self.adapter.grid_vao:
                self.adapter.grid_vao.render(moderngl.LINES)
            else:
                print("[DEBUG] grid_vao est None!")
            if self.adapter.cube_vao:
                self.adapter.cube_vao.render(moderngl.TRIANGLES)
            else:
                print("[DEBUG] cube_vao est None!")
            if not self.adapter.axes_vaos:
                print("[DEBUG] axes_vaos est vide!")
            else:
                for vao, _ in self.adapter.axes_vaos:
                    vao.render(moderngl.LINES)
        
        self.adapter.paintGL = paintGL_full
        self.adapter.update()
        QApplication.processEvents()
        
        self.instruction_label.setText("Étape 5: Voyez-vous le cube complet ?")
        self.current_step = 5


def main():
    """Point d'entrée pour le test interactif."""
    app = QApplication(sys.argv)
    
    print("\n" + "="*60)
    print("TEST INTERACTIF - ISOLATION DU PROBLÈME DE RENDU")
    print("="*60)
    print("\nInstructions:")
    print("1. Cliquez sur chaque bouton dans l'ordre")
    print("2. Observez la zone de visualisation")
    print("3. Dites-moi ce que vous voyez pour chaque étape")
    print("\nFenêtre ouverte. Commencez par cliquer sur 'Étape 1: Fond'")
    
    window = InteractiveTestWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

