"""
Demo launcher for Interface V2 Dashboard.
"""
import sys
import os

# Ensure src is in pythonpath
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication
from interface.shell.dashboard import Dashboard

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    window = Dashboard()
    window.show()
    
    print("Dashboard launched.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
