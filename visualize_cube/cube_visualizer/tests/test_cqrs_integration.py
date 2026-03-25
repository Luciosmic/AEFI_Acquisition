"""
Tests d'intégration CQRS.

Valide le flux complet : UI → CommandBus → Presenter → EventBus → Adapter
"""
import unittest
import sys
import os
from PySide6.QtWidgets import QApplication
from unittest.mock import Mock

# Ajouter le répertoire parent au path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from command_bus import CommandBus
from event_bus import EventBus, EventType
from cube_visualizer_presenter import CubeVisualizerPresenter
from commands import UpdateAnglesCommand, ResetToDefaultCommand


class TestCQRSIntegration(unittest.TestCase):
    """Tests d'intégration pour valider le flux CQRS complet."""
    
    @classmethod
    def setUpClass(cls):
        """Créer QApplication une seule fois pour tous les tests."""
        if QApplication.instance() is None:
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Créer CommandBus, EventBus, Presenter pour chaque test."""
        self.command_bus = CommandBus()
        self.event_bus = EventBus()
        self.presenter = CubeVisualizerPresenter(
            command_bus=self.command_bus,
            event_bus=self.event_bus
        )
        
        # Collecteurs pour vérifier le flux
        self.commands_received = []
        self.events_published = []
        
        # S'abonner aux événements pour vérifier
        def event_handler(event):
            self.events_published.append(event)
        self.event_bus.subscribe(EventType.ANGLES_CHANGED, event_handler)
    
    def test_full_cqrs_flow_update_angles(self):
        """Test du flux complet CQRS pour UPDATE_ANGLES."""
        # 1. UI envoie une commande via CommandBus
        cmd = UpdateAnglesCommand(15.0, 25.0, 35.0)
        self.command_bus.send(cmd.to_command())
        
        # 2. Attendre que la commande soit traitée (plusieurs fois pour être sûr)
        for _ in range(5):
            QApplication.processEvents()
        
        # 3. Vérifier que le Presenter a reçu et traité la commande
        theta_x, theta_y, theta_z = self.presenter.get_angles()
        self.assertEqual(theta_x, 15.0)
        self.assertEqual(theta_y, 25.0)
        self.assertEqual(theta_z, 35.0)
        
        # 4. Vérifier qu'un événement a été publié via EventBus
        self.assertEqual(len(self.events_published), 1)
        self.assertEqual(self.events_published[0].event_type, EventType.ANGLES_CHANGED)
        self.assertEqual(self.events_published[0].data['theta_x'], 15.0)
        self.assertEqual(self.events_published[0].data['theta_y'], 25.0)
        self.assertEqual(self.events_published[0].data['theta_z'], 35.0)
    
    def test_full_cqrs_flow_reset(self):
        """Test du flux complet CQRS pour RESET_TO_DEFAULT."""
        # 1. D'abord, changer les angles
        cmd1 = UpdateAnglesCommand(45.0, 60.0, 90.0)
        self.command_bus.send(cmd1.to_command())
        QApplication.processEvents()
        self.events_published.clear()
        
        # 2. UI envoie une commande RESET via CommandBus
        cmd2 = ResetToDefaultCommand()
        self.command_bus.send(cmd2.to_command())
        QApplication.processEvents()
        
        # 3. Vérifier que le Presenter a réinitialisé
        theta_x, theta_y, theta_z = self.presenter.get_angles()
        self.assertEqual(theta_x, 0.0)
        self.assertEqual(theta_z, 0.0)
        
        # 4. Vérifier qu'un événement a été publié
        self.assertEqual(len(self.events_published), 1)
        self.assertEqual(self.events_published[0].event_type, EventType.ANGLES_CHANGED)
    
    def test_decoupling_ui_presenter_adapter(self):
        """Test que UI, Presenter et Adapter sont bien découplés."""
        # UI ne connaît que CommandBus et EventBus
        # Presenter ne connaît que CommandBus (pour recevoir) et EventBus (pour publier)
        # Adapter ne connaît que EventBus (pour s'abonner)
        
        # Vérifier que le Presenter est bien enregistré comme handler
        # (on ne peut pas vérifier directement, mais on peut vérifier qu'il réagit)
        cmd = UpdateAnglesCommand(1.0, 2.0, 3.0)
        self.command_bus.send(cmd.to_command())
        for _ in range(5):
            QApplication.processEvents()
        
        # Le Presenter devrait avoir traité la commande
        theta_x, theta_y, theta_z = self.presenter.get_angles()
        self.assertEqual(theta_x, 1.0)
        
        # Et un événement devrait avoir été publié
        self.assertEqual(len(self.events_published), 1)
    
    def test_multiple_commands_sequence(self):
        """Test qu'une séquence de commandes fonctionne correctement."""
        commands = [
            UpdateAnglesCommand(10.0, 20.0, 30.0),
            UpdateAnglesCommand(40.0, 50.0, 60.0),
            UpdateAnglesCommand(70.0, 80.0, 90.0),
        ]
        
        for cmd in commands:
            self.command_bus.send(cmd.to_command())
            for _ in range(5):
                QApplication.processEvents()
        
        # Vérifier que les angles sont à la dernière valeur
        theta_x, theta_y, theta_z = self.presenter.get_angles()
        self.assertEqual(theta_x, 70.0)
        self.assertEqual(theta_y, 80.0)
        self.assertEqual(theta_z, 90.0)
        
        # Vérifier que 3 événements ont été publiés
        self.assertEqual(len(self.events_published), 3)


if __name__ == '__main__':
    unittest.main()

