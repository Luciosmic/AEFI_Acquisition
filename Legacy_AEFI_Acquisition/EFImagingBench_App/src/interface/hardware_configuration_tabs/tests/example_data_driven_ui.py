"""
Example usage of data-driven UI generation.

Shows how to use GenericHardwareConfigTab with adapter specs.
"""

import sys
from pathlib import Path

# Add src to path (we're in src/interface/hardware_configuration_tabs/tests/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
from interface.hardware_configuration_tabs.generic_hardware_config_tab import GenericHardwareConfigTab
from infrastructure.adapters.ad9106_ui_adapter import AD9106UIAdapter


class ExampleMainWindow(QMainWindow):
    """Example main window with data-driven hardware tabs."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data-Driven UI Example")
        self.setGeometry(100, 100, 800, 600)
        
        # Create tab widget
        tabs = QTabWidget()
        self.setCentralWidget(tabs)
        
        # Create AD9106 tab from adapter specs
        ad9106_specs = AD9106UIAdapter.get_parameter_specs()
        ad9106_tab = GenericHardwareConfigTab(
            title="AD9106 DDS Configuration",
            param_specs=ad9106_specs
        )
        
        # Connect to config changes
        ad9106_tab.config_changed.connect(self._on_ad9106_config_changed)
        
        tabs.addTab(ad9106_tab, "AD9106 DDS")
        
        # Store reference
        self.ad9106_tab = ad9106_tab
        self.ad9106_adapter = AD9106UIAdapter()
    
    def _on_ad9106_config_changed(self, config: dict):
        """Handle AD9106 configuration changes."""
        print(f"[UI] Config changed: {config}")
        
        # Level 1: Widget validation (automatic)
        is_valid, error = self.ad9106_tab.validate()
        if not is_valid:
            print(f"[UI] Validation error: {error}")
            return
        
        # Level 2: Adapter validation (hardware constraints)
        is_valid, error = self.ad9106_adapter.validate_config(config)
        if not is_valid:
            print(f"[Adapter] Validation error: {error}")
            return
        
        # Apply to hardware
        try:
            self.ad9106_adapter.apply_config(config)
            print("[Hardware] Configuration applied successfully")
        except Exception as e:
            print(f"[Hardware] Error: {e}")


def main():
    """Run example application."""
    app = QApplication(sys.argv)
    
    # Apply dark theme
    app.setStyleSheet("""
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
            padding: 8px 20px;
            border: 1px solid #555555;
        }
        QTabBar::tab:selected {
            background-color: #2E86AB;
        }
    """)
    
    window = ExampleMainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
