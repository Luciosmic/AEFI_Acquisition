from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, 
    QDoubleSpinBox, QFormLayout, QPushButton
)
from PySide6.QtCore import Signal, Slot, QProcess
import sys
import os
from PySide6.QtCore import Signal, Slot

class SensorTransformationPanel(QWidget):
    """
    Panel for configuring Sensor -> Source coordinate transformation.
    """
    
    # Signals
    angles_changed = Signal(float, float, float) # theta_x, theta_y, theta_z
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)
        
        # --- 1. Rotation Angles Configuration ---
        grp_angles = QGroupBox("Rotation Angles (Sensor -> Source)")
        l_angles = QFormLayout(grp_angles)
        
        self.spin_theta_x = self._create_angle_spinbox("35.26")
        self.spin_theta_y = self._create_angle_spinbox("-45.0")
        self.spin_theta_z = self._create_angle_spinbox("-7.20")
        
        l_angles.addRow("Theta X (deg):", self.spin_theta_x)
        l_angles.addRow("Theta Y (deg):", self.spin_theta_y)
        l_angles.addRow("Theta Z (deg):", self.spin_theta_z)
        
        main_layout.addWidget(grp_angles)
        
        # --- 2. 3D Visualization Tool Launch ---
        self.btn_launch_cube = QPushButton("Launch 3D Sensor Visualizer")
        self.btn_launch_cube.setStyleSheet("""
            QPushButton {
                background-color: #00897B;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #00796B;
            }
        """)
        self.btn_launch_cube.clicked.connect(self._launch_cube_visualizer)
        main_layout.addWidget(self.btn_launch_cube)
        
        main_layout.addStretch()
        
        # Process holder
        self.process = None
        
        # Connect internal signals
        self.spin_theta_x.valueChanged.connect(self._on_inputs_changed)
        self.spin_theta_y.valueChanged.connect(self._on_inputs_changed)
        self.spin_theta_z.valueChanged.connect(self._on_inputs_changed)
        
        # Initial emit
        # self._on_inputs_changed() # Defer to presenter

    def _create_angle_spinbox(self, default_val_str) -> QDoubleSpinBox:
        sb = QDoubleSpinBox()
        sb.setRange(-360.0, 360.0)
        sb.setSingleStep(1.0)
        sb.setDecimals(2)
        sb.setSuffix(" °")
        sb.setValue(float(default_val_str))
        return sb

    def _on_inputs_changed(self):
        """Aggregate changes and emit."""
        self.angles_changed.emit(
            self.spin_theta_x.value(),
            self.spin_theta_y.value(),
            self.spin_theta_z.value()
        )

    def _launch_cube_visualizer(self):
        """Lances the emerging 3D cube visualizer via QProcess."""
        if self.process is not None and self.process.state() == QProcess.Running:
            return # Already running
            
        python_exe = sys.executable
        # From src/interface/widgets/panels/sensor_transformation_panel.py -> ... -> root
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        script_path = os.path.join(root_dir, "external_modules", "cube_visualizer", "main.py")
        
        print(f"[SensorTransformationPanel] Launching Cube Visualizer: {python_exe} {script_path}")
        
        self.process = QProcess(self)
        self.process.start(python_exe, [script_path])
