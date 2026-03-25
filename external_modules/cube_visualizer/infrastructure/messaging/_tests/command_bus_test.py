"""Tests unitaires pour CommandBus."""
import sys
import unittest

from PySide6.QtWidgets import QApplication

from cube_visualizer.infrastructure.messaging.command_bus import (
    Command,
    CommandBus,
    CommandType,
)


class TestCommandBus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if QApplication.instance() is None:
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        self.command_bus = CommandBus()
        self.received_commands = []

    def test_register_and_receive_update_angles_command(self):
        def handler(command: Command):
            self.received_commands.append(command)

        self.command_bus.register_handler(CommandType.UPDATE_ANGLES, handler)
        cmd = Command(
            CommandType.UPDATE_ANGLES,
            {"theta_x": 10.0, "theta_y": 20.0, "theta_z": 30.0},
        )
        self.command_bus.send(cmd)
        QApplication.processEvents()

        self.assertEqual(len(self.received_commands), 1)
        self.assertEqual(self.received_commands[0].command_type, CommandType.UPDATE_ANGLES)
        self.assertEqual(self.received_commands[0].data["theta_x"], 10.0)
        self.assertEqual(self.received_commands[0].data["theta_y"], 20.0)
        self.assertEqual(self.received_commands[0].data["theta_z"], 30.0)

    def test_register_and_receive_reset_command(self):
        def handler(command: Command):
            self.received_commands.append(command)

        self.command_bus.register_handler(CommandType.RESET_TO_DEFAULT, handler)
        cmd = Command(CommandType.RESET_TO_DEFAULT, {})
        self.command_bus.send(cmd)
        QApplication.processEvents()

        self.assertEqual(len(self.received_commands), 1)
        self.assertEqual(self.received_commands[0].command_type, CommandType.RESET_TO_DEFAULT)

    def test_multiple_handlers(self):
        handler1_calls = []
        handler2_calls = []

        def handler1(command: Command):
            handler1_calls.append(command)

        def handler2(command: Command):
            handler2_calls.append(command)

        self.command_bus.register_handler(CommandType.UPDATE_ANGLES, handler1)
        self.command_bus.register_handler(CommandType.UPDATE_ANGLES, handler2)
        cmd = Command(
            CommandType.UPDATE_ANGLES,
            {"theta_x": 5.0, "theta_y": 10.0, "theta_z": 15.0},
        )
        self.command_bus.send(cmd)
        QApplication.processEvents()

        self.assertEqual(len(handler1_calls), 1)
        self.assertEqual(len(handler2_calls), 1)

    def test_unregister_handler(self):
        def handler(command: Command):
            self.received_commands.append(command)

        self.command_bus.register_handler(CommandType.UPDATE_ANGLES, handler)
        cmd = Command(CommandType.UPDATE_ANGLES, {"theta_x": 1.0, "theta_y": 2.0, "theta_z": 3.0})
        self.command_bus.send(cmd)
        QApplication.processEvents()
        self.assertEqual(len(self.received_commands), 1)

        self.command_bus.unregister_handler(CommandType.UPDATE_ANGLES, handler)
        self.received_commands.clear()
        cmd = Command(CommandType.UPDATE_ANGLES, {"theta_x": 4.0, "theta_y": 5.0, "theta_z": 6.0})
        self.command_bus.send(cmd)
        QApplication.processEvents()
        self.assertEqual(len(self.received_commands), 0)

    def test_reset_camera_view_command(self):
        def handler(command: Command):
            self.received_commands.append(command)

        self.command_bus.register_handler(CommandType.RESET_CAMERA_VIEW, handler)
        cmd = Command(CommandType.RESET_CAMERA_VIEW, {"view_name": "xy"})
        self.command_bus.send(cmd)
        QApplication.processEvents()

        self.assertEqual(len(self.received_commands), 1)
        self.assertEqual(self.received_commands[0].data["view_name"], "xy")


if __name__ == "__main__":
    unittest.main()
