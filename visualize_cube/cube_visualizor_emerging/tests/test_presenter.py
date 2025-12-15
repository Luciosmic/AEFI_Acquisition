"""
Tests unitaires pour CubeVisualizerPresenter.

Valide le découplage CQRS : réception de commandes via CommandBus et publication d'événements via EventBus.
"""
import unittest
import sys
import os
from PySide6.QtWidgets import QApplication

# Ajouter le répertoire parent au path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from cube_visualizer_presenter import CubeVisualizerPresenter
from command_bus import CommandBus, CommandType
from event_bus import EventBus, EventType
from commands import UpdateAnglesCommand, ResetToDefaultCommand


class TestCubeVisualizerPresenter(unittest.TestCase):
    """Tests pour CubeVisualizerPresenter avec CQRS."""
    
    @classmethod
    def setUpClass(cls):
        """Créer QApplication une seule fois pour tous les tests."""
        if QApplication.instance() is None:
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Créer CommandBus, EventBus et Presenter pour chaque test."""
        self.command_bus = CommandBus()
        self.event_bus = EventBus()
        self.presenter = CubeVisualizerPresenter(
            command_bus=self.command_bus,
            event_bus=self.event_bus
        )
        self.received_events = []
        
        # S'abonner aux événements pour vérifier
        def event_handler(event):
            self.received_events.append(event)
        self.event_bus.subscribe(EventType.ANGLES_CHANGED, event_handler)
    
    def test_update_angles_via_command(self):
        """Test que UPDATE_ANGLES commande met à jour les angles et publie un événement."""
        # Envoyer une commande
        cmd = UpdateAnglesCommand(10.0, 20.0, 30.0)
        self.command_bus.send(cmd.to_command())
        
        # Attendre que la commande soit traitée (plusieurs fois pour être sûr)
        for _ in range(5):
            QApplication.processEvents()
        
        # Vérifier que les angles ont été mis à jour
        theta_x, theta_y, theta_z = self.presenter.get_angles()
        self.assertEqual(theta_x, 10.0)
        self.assertEqual(theta_y, 20.0)
        self.assertEqual(theta_z, 30.0)
        
        # Vérifier qu'un événement a été publié
        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(self.received_events[0].event_type, EventType.ANGLES_CHANGED)
        self.assertEqual(self.received_events[0].data['theta_x'], 10.0)
        self.assertEqual(self.received_events[0].data['theta_y'], 20.0)
        self.assertEqual(self.received_events[0].data['theta_z'], 30.0)
    
    def test_reset_to_default_via_command(self):
        """Test que RESET_TO_DEFAULT commande réinitialise et publie un événement."""
        # D'abord, changer les angles
        cmd1 = UpdateAnglesCommand(45.0, 60.0, 90.0)
        self.command_bus.send(cmd1.to_command())
        QApplication.processEvents()
        self.received_events.clear()
        
        # Envoyer la commande reset
        cmd2 = ResetToDefaultCommand()
        self.command_bus.send(cmd2.to_command())
        QApplication.processEvents()
        
        # Vérifier que les angles sont réinitialisés
        theta_x, theta_y, theta_z = self.presenter.get_angles()
        self.assertEqual(theta_x, 0.0)
        # theta_y devrait être la valeur par défaut
        from cube_geometry import get_default_theta_y
        self.assertAlmostEqual(theta_y, get_default_theta_y(), places=1)
        self.assertEqual(theta_z, 0.0)
        
        # Vérifier qu'un événement a été publié
        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(self.received_events[0].event_type, EventType.ANGLES_CHANGED)
    
    def test_get_rotation_query(self):
        """Test que get_rotation() retourne la bonne rotation (Query - pas de modification)."""
        # Mettre à jour les angles
        cmd = UpdateAnglesCommand(90.0, 0.0, 0.0)
        self.command_bus.send(cmd.to_command())
        QApplication.processEvents()
        
        # Vérifier que get_rotation() retourne la bonne rotation
        rotation = self.presenter.get_rotation()
        self.assertIsNotNone(rotation)
        
        # Vérifier que la rotation appliquée à un vecteur unitaire fonctionne
        import numpy as np
        vector = np.array([1, 0, 0])
        rotated = rotation.apply(vector)
        # Après rotation de 90° autour de X, [1,0,0] devrait rester [1,0,0]
        np.testing.assert_array_almost_equal(rotated, [1, 0, 0], decimal=5)
    
    def test_multiple_commands(self):
        """Test que plusieurs commandes successives fonctionnent correctement."""
        # Première commande
        cmd1 = UpdateAnglesCommand(10.0, 20.0, 30.0)
        self.command_bus.send(cmd1.to_command())
        for _ in range(5):
            QApplication.processEvents()
        
        # Deuxième commande
        cmd2 = UpdateAnglesCommand(40.0, 50.0, 60.0)
        self.command_bus.send(cmd2.to_command())
        for _ in range(5):
            QApplication.processEvents()
        
        # Vérifier que les angles sont à la dernière valeur
        theta_x, theta_y, theta_z = self.presenter.get_angles()
        self.assertEqual(theta_x, 40.0)
        self.assertEqual(theta_y, 50.0)
        self.assertEqual(theta_z, 60.0)
        
        # Vérifier que deux événements ont été publiés
        self.assertEqual(len(self.received_events), 2)


if __name__ == '__main__':
    unittest.main()

