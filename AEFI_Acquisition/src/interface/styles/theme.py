from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

from .stylesheets import APP_STYLESHEET

def apply_dark_theme(app: QApplication):
    """
    Applies a modern dark theme to the QApplication using Fusion style.
    This ensures consistent look across platforms (Windows, Linux, macOS).
    """
    app.setStyle("Fusion")
    
    dark_palette = QPalette()
    
    # Base colors
    dark_color = QColor(45, 45, 45)
    disabled_color = QColor(127, 127, 127)
    
    dark_palette.setColor(QPalette.Window, dark_color)
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(30, 30, 30)) # Slightly darker for inputs
    dark_palette.setColor(QPalette.AlternateBase, dark_color)
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, dark_color)
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    
    # Highlight colors (Blue-ish)
    link_color = QColor(42, 130, 218)
    dark_palette.setColor(QPalette.Link, link_color)
    dark_palette.setColor(QPalette.Highlight, link_color)
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    
    # Disabled state
    dark_palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled_color)
    dark_palette.setColor(QPalette.Disabled, QPalette.Text, disabled_color)
    dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_color)
    dark_palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
    dark_palette.setColor(QPalette.Disabled, QPalette.HighlightedText, disabled_color)
    
    app.setPalette(dark_palette)
    
    # Apply centralized stylesheet
    app.setStyleSheet(APP_STYLESHEET)
