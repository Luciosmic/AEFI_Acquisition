#!/usr/bin/env python3
"""
Example: Using both AD9106 and ADS131A04 UI adapters.

Shows data-driven UI generation for both hardware components.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

from interface.hardware_configuration_tabs.generic_hardware_config_tab import GenericHardwareConfigTab
from infrastructure.adapters.ad9106_ui_adapter import AD9106UIAdapter
from infrastructure.adapters.ads131a04_ui_adapter import ADS131A04UIAdapter


class HardwareConfigWindow(QMainWindow):
    """Hardware configuration window with data-driven UI."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EFImagingBench - Hardware Configuration")
        self.setGeometry(100, 100, 1000, 800)
        
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
                padding: 12px 30px;
                border: 1px solid #555555;
                margin-right: 2px;
                font-size: 14px;
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
        
        # AD9106 DDS Tab
        print("Creating AD9106 DDS configuration tab...")
        ad9106_specs = AD9106UIAdapter.get_parameter_specs()
        print(f"  → {len(ad9106_specs)} parameters loaded")
        
        self.ad9106_tab = GenericHardwareConfigTab(
            title="AD9106 DDS Configuration",
            param_specs=ad9106_specs
        )
        self.ad9106_tab.config_changed.connect(
            lambda cfg: self._on_config_changed("AD9106", cfg, AD9106UIAdapter())
        )
        tabs.addTab(self.ad9106_tab, "🎛️ AD9106 DDS")
        
        # ADS131A04 ADC Tab
        print("Creating ADS131A04 ADC configuration tab...")
        ads131a04_specs = ADS131A04UIAdapter.get_parameter_specs()
        print(f"  → {len(ads131a04_specs)} parameters loaded")
        
        self.ads131a04_tab = GenericHardwareConfigTab(
            title="ADS131A04 ADC Configuration",
            param_specs=ads131a04_specs
        )
        self.ads131a04_tab.config_changed.connect(
            lambda cfg: self._on_config_changed("ADS131A04", cfg, ADS131A04UIAdapter())
        )
        tabs.addTab(self.ads131a04_tab, "📊 ADS131A04 ADC")
        
        print("✅ UI ready!\n")
        print("Try changing parameters in the tabs...")
        print("Configuration changes will be validated and printed to console.\n")
    
    def _on_config_changed(self, hardware_name: str, config: dict, adapter):
        """Handle configuration changes."""
        print("\n" + "="*70)
        print(f"📝 {hardware_name} Configuration Changed:")
        print("="*70)
        
        # Show first 3 changed values
        for i, (key, value) in enumerate(config.items()):
            if i < 3:
                print(f"  {key}: {value}")
        if len(config) > 3:
            print(f"  ... and {len(config) - 3} more parameters")
        
        # Level 1: Widget validation
        if hardware_name == "AD9106":
            tab = self.ad9106_tab
        else:
            tab = self.ads131a04_tab
        
        is_valid, error = tab.validate()
        if not is_valid:
            print(f"\n❌ Widget Validation Failed: {error}")
            return
        print("✅ Widget validation: PASSED")
        
        # Level 2: Adapter validation
        is_valid, error = adapter.validate_config(config)
        if not is_valid:
            print(f"❌ Adapter Validation Failed: {error}")
            return
        print("✅ Adapter validation: PASSED")
        
        # Would apply to hardware here
        print(f"✅ Ready to apply to {hardware_name} hardware")
        print("="*70 + "\n")


def main():
    """Launch the hardware configuration UI."""
    print("\n" + "="*70)
    print("🚀 Launching Hardware Configuration UI")
    print("="*70 + "\n")
    
    app = QApplication(sys.argv)
    window = HardwareConfigWindow()
    window.show()
    
    print("Close the window to exit.\n")
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
