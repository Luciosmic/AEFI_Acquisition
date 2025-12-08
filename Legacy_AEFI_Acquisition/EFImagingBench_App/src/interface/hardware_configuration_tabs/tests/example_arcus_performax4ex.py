#!/usr/bin/env python3
"""
Example: Arcus Performax 4EX motor controller configuration.

Shows data-driven UI generation for motor control parameters.
"""

import sys
from pathlib import Path

# Add src to path (we're in src/interface/hardware_configuration_tabs/tests/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

from interface.hardware_configuration_tabs.generic_hardware_config_tab import GenericHardwareConfigTab
from infrastructure.arcus_performax_4EX.ui_adapter_arcus_performax4EX import ArcusPerformax4EXUIAdapter


class ArcusPerformax4EXTestWindow(QMainWindow):
    """Test window for Arcus Performax 4EX motor configuration."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arcus Performax 4EX - Motor Configuration")
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
        
        # Create Arcus Performax 4EX tab from adapter specs
        print("Creating Arcus Performax 4EX motor configuration tab...")
        arcus_specs = ArcusPerformax4EXUIAdapter.get_parameter_specs()
        print(f"  → {len(arcus_specs)} parameters loaded")
        print("\nParameter types:")
        spinbox_count = sum(1 for spec in arcus_specs if spec.type == 'spinbox')
        combo_count = sum(1 for spec in arcus_specs if spec.type == 'combo')
        print(f"  - Spinbox: {spinbox_count}")
        print(f"  - Combo: {combo_count}")
        
        self.arcus_tab = GenericHardwareConfigTab(
            title="Arcus Performax 4EX Motor Configuration",
            param_specs=arcus_specs
        )
        
        # Connect to config changes
        self.arcus_tab.config_changed.connect(self._on_config_changed)
        
        layout.addWidget(self.arcus_tab)
        
        # Store adapter
        self.arcus_adapter = ArcusPerformax4EXUIAdapter()
        
        print("✅ UI ready!\n")
        print("Motor control parameters:")
        print("  - Speed: Max Velocity, Acceleration, Deceleration")
        print("  - Jog: Jog Velocity, Jog Acceleration")
        print("  - Limits: Min/Max Position")
        print("  - Homing: Direction, Velocity")
        print("  - Current: Run Current, Hold Current")
        print("  - Microstepping: Resolution")
        print("\nConfiguration changes will be validated and printed to console.\n")
    
    def _on_config_changed(self, config: dict):
        """Handle configuration changes."""
        print("\n" + "="*70)
        print("🎛️  Arcus Performax 4EX Configuration Changed:")
        print("="*70)
        
        # Group parameters by category
        speed_params = ['max_velocity', 'acceleration', 'deceleration']
        jog_params = ['jog_velocity', 'jog_acceleration']
        limit_params = ['min_position', 'max_position']
        homing_params = ['homing_direction', 'homing_velocity']
        current_params = ['run_current', 'hold_current']
        microstep_params = ['microstep_resolution']
        
        print("\n📊 Speed Parameters:")
        for key in speed_params:
            if key in config:
                print(f"  {key}: {config[key]}")
        
        print("\n🎮 Jog Parameters:")
        for key in jog_params:
            if key in config:
                print(f"  {key}: {config[key]}")
        
        print("\n🚧 Position Limits:")
        for key in limit_params:
            if key in config:
                print(f"  {key}: {config[key]}")
        
        print("\n🏠 Homing:")
        for key in homing_params:
            if key in config:
                print(f"  {key}: {config[key]}")
        
        print("\n⚡ Current Settings:")
        for key in current_params:
            if key in config:
                print(f"  {key}: {config[key]}")
        
        print("\n🔧 Microstepping:")
        for key in microstep_params:
            if key in config:
                print(f"  {key}: {config[key]}")
        
        # Level 1: Widget validation
        is_valid, error = self.arcus_tab.validate()
        if not is_valid:
            print(f"\n❌ Widget Validation Failed: {error}")
            return
        print("\n✅ Widget validation: PASSED")
        
        # Level 2: Adapter validation
        is_valid, error = self.arcus_adapter.validate_config(config)
        if not is_valid:
            print(f"❌ Adapter Validation Failed: {error}")
            return
        print("✅ Adapter validation: PASSED")
        
        # Calculate some useful info
        max_vel = config.get('max_velocity', 0)
        accel = config.get('acceleration', 1)
        time_to_max = max_vel / accel
        print(f"\n📈 Performance:")
        print(f"  Time to reach max velocity: {time_to_max:.2f}s")
        print(f"  Distance to reach max velocity: {0.5 * accel * time_to_max**2:.0f} steps")
        
        # Would apply to hardware here
        print("\n✅ Ready to apply to Arcus Performax 4EX motor controller")
        print("="*70 + "\n")


def main():
    """Launch the Arcus Performax 4EX configuration UI."""
    print("\n" + "="*70)
    print("🚀 Launching Arcus Performax 4EX Motor Configuration UI")
    print("="*70 + "\n")
    
    app = QApplication(sys.argv)
    window = ArcusPerformax4EXTestWindow()
    window.show()
    
    print("Close the window to exit.\n")
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
