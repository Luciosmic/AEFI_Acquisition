#!/usr/bin/env python3
"""
Simple UI launcher for testing data-driven hardware configuration.

Launches a PyQt5 window with auto-generated UI from adapter specs.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

from interface.hardware_configuration_tabs.generic_hardware_config_tab import GenericHardwareConfigTab
from infrastructure.adapters.ad9106_ui_adapter import AD9106UIAdapter


class TestWindow(QMainWindow):
    """Simple test window for data-driven UI."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EFImagingBench - Data-Driven UI Test")
        self.setGeometry(100, 100, 900, 700)
        
        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #252525;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #353535;
            }
            QTabBar::tab {
                background-color: #353535;
                color: #FFFFFF;
                padding: 10px 25px;
                border: 1px solid #555555;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #2E86AB;
                border-bottom: none;
            }
            QTabBar::tab:hover {
                background-color: #3A98BD;
            }
        """)
        
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Create tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Create AD9106 tab from adapter specs
        print("Creating AD9106 configuration tab...")
        ad9106_specs = AD9106UIAdapter.get_parameter_specs()
        print(f"  → {len(ad9106_specs)} parameters loaded")
        
        self.ad9106_tab = GenericHardwareConfigTab(
            title="AD9106 DDS Configuration",
            param_specs=ad9106_specs
        )
        
        # Connect to config changes
        self.ad9106_tab.config_changed.connect(self._on_config_changed)
        
        tabs.addTab(self.ad9106_tab, "AD9106 DDS")
        
        # Store adapter
        self.ad9106_adapter = AD9106UIAdapter()
        
        print("✅ UI ready!")
        print("\nTry changing parameters in the UI...")
        print("Configuration changes will be validated and printed to console.\n")
    
    def _on_config_changed(self, config: dict):
        """Handle configuration changes."""
        print("\n" + "="*60)
        print("📝 Configuration Changed:")
        print("="*60)
        
        # Show changed values (first 3 for brevity)
        for i, (key, value) in enumerate(config.items()):
            if i < 3:
                print(f"  {key}: {value}")
        if len(config) > 3:
            print(f"  ... and {len(config) - 3} more parameters")
        
        # Level 1: Widget validation
        is_valid, error = self.ad9106_tab.validate()
        if not is_valid:
            print(f"\n❌ Widget Validation Failed: {error}")
            return
        print("✅ Widget validation: PASSED")
        
        # Level 2: Adapter validation
        is_valid, error = self.ad9106_adapter.validate_config(config)
        if not is_valid:
            print(f"❌ Adapter Validation Failed: {error}")
            return
        print("✅ Adapter validation: PASSED")
        
        # Would apply to hardware here
        print("✅ Ready to apply to hardware")
        print("="*60 + "\n")


def main():
    """Launch the test UI."""
    print("\n" + "="*60)
    print("🚀 Launching Data-Driven UI Test")
    print("="*60 + "\n")
    
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    
    print("Close the window to exit.\n")
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
