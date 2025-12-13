import sys
import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import time

from interface.main_window import DashBoard
from infrastructure.tests.diagram_friendly_test import DiagramFriendlyTest

# Ensure one QApplication instance
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

class TestUIIntegration(DiagramFriendlyTest):
    def setUp(self):
        super().setUp()
        self.log_interaction("Test", "CREATE", "MainWindow", "Setup UI")
        self.window = DashBoard()
        
        # Access components for verification
        self.presenter = self.window.presenter
        self.service = self.window.scan_service
        self.control = self.window.control_widget
        self.colormap = self.window.colormap_widget
        
    def test_start_scan_flow(self):
        self.log_interaction("Test", "START", "UI", "Start scan flow test")
        
        # 1. Configure via UI (programmatically setting text)
        self.log_interaction("Test", "ACTION", "ScanControlWidget", "Set scan parameters")
        self.control.input_x_nb.setText("2")
        self.control.input_y_nb.setText("2")
        self.control.combo_pattern.setCurrentText("RASTER")
        
        # 2. Click Start
        self.log_interaction("Test", "CLICK", "ScanControlWidget", "Click Start Button")
        self.control.btn_start.click()
        
        # 3. Wait for scan to complete (it runs in a thread)
        # We use a loop to process events
        self.log_interaction("Test", "WAIT", "ScanApplicationService", "Waiting for scan completion")
        
        max_wait = 2.0 # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            app.processEvents() # Process Qt signals
            if not self.control.btn_stop.isEnabled() and not self.control.btn_start.isEnabled():
                 # Running
                 pass
            if self.control.btn_start.isEnabled() and "Completed" in self.control.lbl_status.text():
                break
            time.sleep(0.1)
            
        # 4. Verify UI State
        status_text = self.control.lbl_status.text()
        self.log_interaction("Test", "ASSERT", "ScanControlWidget", "Check status text", expect="Completed", got=status_text)
        self.assertIn("Completed", status_text)
        
        # 5. Verify Colormap Data
        points_plotted = len(self.colormap.positions)
        self.log_interaction("Test", "ASSERT", "Scan2DColormapWidget", "Check plotted points", expect=4, got=points_plotted)
        self.assertEqual(points_plotted, 4)

if __name__ == '__main__':
    unittest.main()
