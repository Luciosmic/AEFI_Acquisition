"""
Standalone entry point: shows CubeSensorWidget in its own window.

The dashboard docks the same widget (see cube_sensor_widget_intention.md).
"""
import sys
from PySide6.QtWidgets import QApplication

from .cube_sensor_widget import CubeSensorWidget, configure_qt_opengl


def main():
    configure_qt_opengl()
    app = QApplication(sys.argv)
    window = CubeSensorWidget()
    window.setWindowTitle("Cube Sensor - Visualisation 3D")
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
