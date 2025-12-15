from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QLabel, QDoubleSpinBox, QFormLayout
)
from PySide6.QtCore import Signal, Slot, Qt

class SensorTransformationPanel(QWidget):
    """
    Panel for configuring Sensor -> Source coordinate transformation.
    """
    
    # Signals
    angles_changed = Signal(float, float, float) # theta_x, theta_y, theta_z
    test_vector_changed = Signal(float, float, float) # vx, vy, vz
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)
        
        # --- 1. Rotation Angles Configuration ---
        grp_angles = QGroupBox("Rotation Angles (Sensor -> Source)")
        l_angles = QFormLayout(grp_angles)
        
        self.spin_theta_x = self._create_angle_spinbox("35.26")
        self.spin_theta_y = self._create_angle_spinbox("45.0")
        self.spin_theta_z = self._create_angle_spinbox("0.0")
        
        l_angles.addRow("Theta X (deg):", self.spin_theta_x)
        l_angles.addRow("Theta Y (deg):", self.spin_theta_y)
        l_angles.addRow("Theta Z (deg):", self.spin_theta_z)
        
        main_layout.addWidget(grp_angles)
        
        # --- 2. Test Vector ---
        grp_test = QGroupBox("Vector Transformation Test")
        l_test = QVBoxLayout(grp_test)
        
        # Input
        l_in = QHBoxLayout()
        l_in.addWidget(QLabel("Input (Sensor):"))
        self.spin_vx = self._create_vector_spinbox(1.0)
        self.spin_vy = self._create_vector_spinbox(0.0)
        self.spin_vz = self._create_vector_spinbox(0.0)
        l_in.addWidget(self.spin_vx)
        l_in.addWidget(self.spin_vy)
        l_in.addWidget(self.spin_vz)
        l_test.addLayout(l_in)
        
        # Output
        l_out = QHBoxLayout()
        l_out.addWidget(QLabel("Output (Source):"))
        self.lbl_out_x = self._create_output_label()
        self.lbl_out_y = self._create_output_label()
        self.lbl_out_z = self._create_output_label()
        l_out.addWidget(self.lbl_out_x)
        l_out.addWidget(self.lbl_out_y)
        l_out.addWidget(self.lbl_out_z)
        l_test.addLayout(l_out)
        
        main_layout.addWidget(grp_test)
        main_layout.addStretch()
        
        # Connect internal signals
        self.spin_theta_x.valueChanged.connect(self._on_inputs_changed)
        self.spin_theta_y.valueChanged.connect(self._on_inputs_changed)
        self.spin_theta_z.valueChanged.connect(self._on_inputs_changed)
        
        self.spin_vx.valueChanged.connect(self._on_inputs_changed)
        self.spin_vy.valueChanged.connect(self._on_inputs_changed)
        self.spin_vz.valueChanged.connect(self._on_inputs_changed)
        
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

    def _create_vector_spinbox(self, val) -> QDoubleSpinBox:
        sb = QDoubleSpinBox()
        sb.setRange(-1000.0, 1000.0)
        sb.setSingleStep(0.1)
        sb.setDecimals(3)
        sb.setValue(val)
        return sb
        
    def _create_output_label(self) -> QLabel:
        l = QLabel("0.000")
        l.setStyleSheet("font-weight: bold; color: #2E86C1; border: 1px solid #ccc; padding: 2px; min-width: 60px;")
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return l

    def _on_inputs_changed(self):
        """Aggregate changes and emit."""
        self.angles_changed.emit(
            self.spin_theta_x.value(),
            self.spin_theta_y.value(),
            self.spin_theta_z.value()
        )
        self.test_vector_changed.emit(
            self.spin_vx.value(),
            self.spin_vy.value(),
            self.spin_vz.value()
        )

    @Slot(tuple)
    def update_output_vector(self, vector: tuple):
        """Update the read-only output labels."""
        vx, vy, vz = vector
        self.lbl_out_x.setText(f"{vx:.3f}")
        self.lbl_out_y.setText(f"{vy:.3f}")
        self.lbl_out_z.setText(f"{vz:.3f}")
