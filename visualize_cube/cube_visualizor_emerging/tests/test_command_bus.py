"""
Tests unitaires pour CommandBus.

Valide le découplage et la communication via commandes.
"""
import unittest
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QEventLoop

# Ajouter le répertoire parent au path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from command_bus import CommandBus, Command, CommandType
from commands import UpdateAnglesCommand, ResetToDefaultCommand, ResetCameraViewCommand


class TestCommandBus(unittest.TestCase):
    """Tests pour CommandBus."""
    
    @classmethod
    def setUpClass(cls):
        """Créer QApplication une seule fois pour tous les tests."""
        if QApplication.instance() is None:
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Créer un CommandBus pour chaque test."""
        self.command_bus = CommandBus()
        self.received_commands = []
    
    def test_register_and_receive_update_angles_command(self):
        """Test d'enregistrement et réception d'une commande UPDATE_ANGLES."""
        def handler(command: Command):
            self.received_commands.append(command)
        
        self.command_bus.register_handler(CommandType.UPDATE_ANGLES, handler)
        
        # Envoyer une commande
        cmd = UpdateAnglesCommand(10.0, 20.0, 30.0)
        self.command_bus.send(cmd.to_command())
        
        # Attendre que le signal soit traité
        QApplication.processEvents()
        
        self.assertEqual(len(self.received_commands), 1)
        self.assertEqual(self.received_commands[0].command_type, CommandType.UPDATE_ANGLES)
        self.assertEqual(self.received_commands[0].data['theta_x'], 10.0)
        self.assertEqual(self.received_commands[0].data['theta_y'], 20.0)
        self.assertEqual(self.received_commands[0].data['theta_z'], 30.0)
    
    def test_register_and_receive_reset_command(self):
        """Test d'enregistrement et réception d'une commande RESET_TO_DEFAULT."""
        def handler(command: Command):
            self.received_commands.append(command)
        
        self.command_bus.register_handler(CommandType.RESET_TO_DEFAULT, handler)
        
        # Envoyer une commande
        cmd = ResetToDefaultCommand()
        self.command_bus.send(cmd.to_command())
        
        # Attendre que le signal soit traité
        QApplication.processEvents()
        
        self.assertEqual(len(self.received_commands), 1)
        self.assertEqual(self.received_commands[0].command_type, CommandType.RESET_TO_DEFAULT)
    
    def test_multiple_handlers(self):
        """Test que plusieurs handlers peuvent recevoir la même commande."""
        handler1_calls = []
        handler2_calls = []
        
        def handler1(command: Command):
            handler1_calls.append(command)
        
        def handler2(command: Command):
            handler2_calls.append(command)
        
        self.command_bus.register_handler(CommandType.UPDATE_ANGLES, handler1)
        self.command_bus.register_handler(CommandType.UPDATE_ANGLES, handler2)
        
        cmd = UpdateAnglesCommand(5.0, 10.0, 15.0)
        self.command_bus.send(cmd.to_command())
        
        QApplication.processEvents()
        
        self.assertEqual(len(handler1_calls), 1)
        self.assertEqual(len(handler2_calls), 1)
    
    def test_unregister_handler(self):
        """Test de désenregistrement d'un handler."""
        def handler(command: Command):
            self.received_commands.append(command)
        
        self.command_bus.register_handler(CommandType.UPDATE_ANGLES, handler)
        
        # Envoyer une commande
        cmd = UpdateAnglesCommand(1.0, 2.0, 3.0)
        self.command_bus.send(cmd.to_command())
        QApplication.processEvents()
        self.assertEqual(len(self.received_commands), 1)
        
        # Désenregistrer
        self.command_bus.unregister_handler(CommandType.UPDATE_ANGLES, handler)
        
        # Envoyer une autre commande
        self.received_commands.clear()
        cmd = UpdateAnglesCommand(4.0, 5.0, 6.0)
        self.command_bus.send(cmd.to_command())
        QApplication.processEvents()
        
        # Le handler ne devrait plus recevoir la commande
        self.assertEqual(len(self.received_commands), 0)
    
    def test_reset_camera_view_command(self):
        """Test de la commande RESET_CAMERA_VIEW."""
        def handler(command: Command):
            self.received_commands.append(command)
        
        self.command_bus.register_handler(CommandType.RESET_CAMERA_VIEW, handler)
        
        cmd = ResetCameraViewCommand('xy')
        self.command_bus.send(cmd.to_command())
        
        QApplication.processEvents()
        
        self.assertEqual(len(self.received_commands), 1)
        self.assertEqual(self.received_commands[0].data['view_name'], 'xy')


if __name__ == '__main__':
    unittest.main()

