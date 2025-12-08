#!/usr/bin/env python3
"""
Example: ADS131A04 ADC configuration with combo boxes.

Shows data-driven UI generation with combo boxes (dropdowns).
"""

import sys
from pathlib import Path

# Add src to path (we're in src/interface/hardware_configuration_tabs/tests/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

from interface.hardware_configuration_tabs.generic_hardware_config_tab import GenericHardwareConfigTab
from infrastructure.adapters.ads131a04_ui_adapter import ADS131A04UIAdapter


class ADS131A04TestWindow(QMainWindow):
    """Test window for ADS131A04 ADC configuration."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ADS131A04 ADC - Data-Driven UI Test")
        self.setGeometry(100, 100, 900, 800)
        
        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #252525;
            }
        """)
        
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Create ADS131A04 tab from adapter specs
        print("Creating ADS131A04 ADC configuration tab...")
        ads131a04_specs = ADS131A04UIAdapter.get_parameter_specs()
        print(f"  → {len(ads131a04_specs)} parameters loaded")
        print("\nParameters with COMBO boxes:")
        for spec in ads131a04_specs:
            if spec.type == 'combo':
                print(f"  - {spec.label}: {len(spec.options)} options")
        
        self.ads131a04_tab = GenericHardwareConfigTab(
            title="ADS131A04 ADC Configuration",
            param_specs=ads131a04_specs
        )
        
        # Connect to config changes
        self.ads131a04_tab.config_changed.connect(self._on_config_changed)
        
        layout.addWidget(self.ads131a04_tab)
        
        # Store adapter
        self.ads131a04_adapter = ADS131A04UIAdapter()
        
        print("✅ UI ready!\n")
        print("Try changing parameters - especially the COMBO boxes:")
        print("  - OSR (Oversampling Ratio)")
        print("  - Sampling Rate")
        print("  - Channel Gains")
        print("  - Reference Mode")
        print("  - Reference Voltage")
        print("  - Filter Type")
        print("\nConfiguration changes will be validated and printed to console.\n")
    
    def _on_config_changed(self, config: dict):
        """Handle configuration changes."""
        print("\n" + "="*70)
        print("📝 ADS131A04 Configuration Changed:")
        print("="*70)
        
        # Show all changed values
        for key, value in config.items():
            print(f"  {key}: {value}")
        
        # Level 1: Widget validation
        is_valid, error = self.ads131a04_tab.validate()
        if not is_valid:
            print(f"\n❌ Widget Validation Failed: {error}")
            return
        print("✅ Widget validation: PASSED")
        
        # Level 2: Adapter validation
        is_valid, error = self.ads131a04_adapter.validate_config(config)
        if not is_valid:
            print(f"❌ Adapter Validation Failed: {error}")
            return
        print("✅ Adapter validation: PASSED")
        
        # Would apply to hardware here
        print("✅ Ready to apply to ADS131A04 hardware")
        print("="*70 + "\n")


def main():
    """Launch the ADS131A04 configuration UI."""
    print("\n" + "="*70)
    print("🚀 Launching ADS131A04 ADC Configuration UI")
    print("="*70 + "\n")
    
    app = QApplication(sys.argv)
    window = ADS131A04TestWindow()
    window.show()
    
    print("Close the window to exit.\n")
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
