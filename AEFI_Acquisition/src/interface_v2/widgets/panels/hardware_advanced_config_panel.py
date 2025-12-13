"""
Hardware Advanced Configuration Panel - Interface V2

Generic panel for hardware advanced configuration.
Generates UI widgets from HardwareAdvancedParameterSchema with grouping support.
"""

from typing import Dict, List, Any, Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QLabel,
    QPushButton,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal

from domain.value_objects.hardware_configuration.hardware_advanced_parameter_schema import (
    HardwareAdvancedParameterSchema,
    NumberParameterSchema,
    EnumParameterSchema,
    BooleanParameterSchema,
)


class HardwareAdvancedConfigPanel(QWidget):
    """
    Generic panel for hardware advanced configuration.
    
    Features:
    - Hardware selection dropdown
    - Parameter widgets organized by groups
    - Apply button
    - Status messages
    """
    
    # Signals (passive view pattern)
    hardware_selected = Signal(str)  # hardware_id
    config_changed = Signal(dict)  # {param_key: value}
    apply_requested = Signal(dict)  # full config dict
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_hardware_id: Optional[str] = None
        self._specs: List[HardwareAdvancedParameterSchema] = []
        self._widgets: Dict[str, QWidget] = {}
        self._group_boxes: Dict[str, QGroupBox] = {}
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the UI structure."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Hardware Selection
        hw_layout = QHBoxLayout()
        hw_label = QLabel("Hardware:")
        self._hw_combo = QComboBox()
        self._hw_combo.currentTextChanged.connect(self._on_hardware_selected)
        hw_layout.addWidget(hw_label)
        hw_layout.addWidget(self._hw_combo, 1)
        main_layout.addLayout(hw_layout)
        
        # Scroll area for parameters
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setSpacing(10)
        self._content_layout.setContentsMargins(5, 5, 5, 5)
        
        scroll.setWidget(self._content_widget)
        main_layout.addWidget(scroll, 1)
        
        # Status label
        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet("color: gray; font-size: 10px;")
        main_layout.addWidget(self._status_label)
        
        # Apply button
        self._apply_btn = QPushButton("Apply Configuration")
        self._apply_btn.setEnabled(False)
        self._apply_btn.clicked.connect(self._on_apply_clicked)
        main_layout.addWidget(self._apply_btn)
    
    def set_hardware_list(self, hardware_ids: List[str]):
        """Update hardware selection dropdown."""
        self._hw_combo.clear()
        self._hw_combo.addItems(hardware_ids)
    
    def set_parameter_specs(self, hardware_id: str, specs: List[HardwareAdvancedParameterSchema]):
        """Set parameter specifications and rebuild UI."""
        self._current_hardware_id = hardware_id
        self._specs = specs
        self._widgets.clear()
        self._group_boxes.clear()
        
        # Clear existing content
        while self._content_layout.count():
            child = self._content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Group specs by group name
        groups: Dict[str, List[HardwareAdvancedParameterSchema]] = {}
        for spec in specs:
            group_name = spec.group or "General"
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append(spec)
        
        # Create group boxes and widgets
        for group_name, group_specs in sorted(groups.items()):
            group_box = QGroupBox(group_name)
            group_layout = QFormLayout(group_box)
            group_layout.setSpacing(8)
            group_layout.setContentsMargins(10, 15, 10, 10)
            
            self._group_boxes[group_name] = group_box
            
            for spec in group_specs:
                widget = self._create_widget(spec)
                self._widgets[spec.key] = widget
                
                label_text = spec.display_name
                if isinstance(spec, NumberParameterSchema) and spec.unit:
                    label_text += f" ({spec.unit})"
                
                label = QLabel(label_text)
                if spec.description:
                    label.setToolTip(spec.description)
                    widget.setToolTip(spec.description)
                
                group_layout.addRow(label, widget)
            
            self._content_layout.addWidget(group_box)
        
        self._content_layout.addStretch()
        self._apply_btn.setEnabled(True)
    
    def _create_widget(self, spec: HardwareAdvancedParameterSchema) -> QWidget:
        """Create appropriate widget based on spec type."""
        if isinstance(spec, NumberParameterSchema):
            # Determine if float or int
            has_decimals = (
                isinstance(spec.default_value, float) or
                (spec.min_value != int(spec.min_value)) or
                (spec.max_value != int(spec.max_value))
            )
            
            if has_decimals:
                widget = QDoubleSpinBox()
                widget.setDecimals(3)
                widget.setSingleStep(spec.step)
            else:
                widget = QSpinBox()
                widget.setSingleStep(int(spec.step))
            
            widget.setRange(spec.min_value, spec.max_value)
            widget.setValue(spec.default_value)
            widget.valueChanged.connect(lambda: self._on_parameter_changed())
            
        elif isinstance(spec, EnumParameterSchema):
            widget = QComboBox()
            widget.addItems(spec.choices)
            if spec.default_value in spec.choices:
                widget.setCurrentText(str(spec.default_value))
            widget.currentTextChanged.connect(lambda: self._on_parameter_changed())
            
        elif isinstance(spec, BooleanParameterSchema):
            widget = QCheckBox()
            widget.setChecked(bool(spec.default_value))
            widget.toggled.connect(lambda: self._on_parameter_changed())
            
        else:
            # Fallback to label
            widget = QLabel("Unknown type")
        
        return widget
    
    def _on_hardware_selected(self, hardware_id: str):
        """Handle hardware selection change."""
        if hardware_id:
            self.hardware_selected.emit(hardware_id)
    
    def _on_parameter_changed(self):
        """Handle parameter value change."""
        config = self._get_current_config()
        self.config_changed.emit(config)
    
    def _on_apply_clicked(self):
        """Handle apply button click."""
        config = self._get_current_config()
        self.apply_requested.emit(config)
    
    def _get_current_config(self) -> Dict[str, Any]:
        """Get current configuration from widgets."""
        config = {}
        for key, widget in self._widgets.items():
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                config[key] = widget.value()
            elif isinstance(widget, QComboBox):
                config[key] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                config[key] = widget.isChecked()
        return config
    
    def set_status_message(self, message: str):
        """Update status label."""
        self._status_label.setText(message)
    
    def clear_parameters(self):
        """Clear parameter widgets."""
        self._specs = []
        self._widgets.clear()
        self._group_boxes.clear()
        while self._content_layout.count():
            child = self._content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._apply_btn.setEnabled(False)

