from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QDoubleSpinBox, QCheckBox, QComboBox, QGroupBox, QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt
from typing import List, Dict, Any, Optional

from domain.value_objects.hardware_configuration.hardware_advanced_parameter_schema import (
    HardwareAdvancedParameterSchema,
    NumberParameterSchema,
    BooleanParameterSchema,
    EnumParameterSchema,
    ParameterType
)

class HardwareConfigFormWidget(QWidget):
    """
    Passive Generic Form Widget.
    
    Responsibility:
    - Receive a list of `HardwareAdvancedParameterSchema`.
    - Dynamically generate UI controls (SpinBox, CheckBox, ComboBox).
    - Emit `config_changed` signal when user modifies values.
    
    Design:
    - Passive View: No business logic, just rendering and signal forwarding.
    - Uses a dictionary to track current state locally before emitting full delta or state.
    """
    
    # Emits full configuration dictionary on every change
    config_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self._current_config: Dict[str, Any] = {}
        self._schema_map: Dict[str, HardwareAdvancedParameterSchema] = {}
        self._init_ui()
        
    def _init_ui(self):
        main_layout = QVBoxLayout()
        
        # Scroll Area for potentially long lists
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.form_layout = QVBoxLayout()
        self.scroll_content.setLayout(self.form_layout)
        self.scroll.setWidget(self.scroll_content)
        
        main_layout.addWidget(self.scroll)
        self.setLayout(main_layout)

    def set_schema(self, schemas: List[HardwareAdvancedParameterSchema]):
        """
        Rebuild the form based on the provided schemas.
        """
        # Clear existing
        self._clear_layout(self.form_layout)
        self._current_config.clear()
        self._schema_map.clear()
        
        # Group parameters
        groups: Dict[str, List[HardwareAdvancedParameterSchema]] = {}
        for schema in schemas:
            groups.setdefault(schema.group or "General", []).append(schema)
            self._schema_map[schema.key] = schema
            self._current_config[schema.key] = schema.default_value

        # Build UI
        for group_name, group_schemas in groups.items():
            group_box = QGroupBox(group_name)
            group_layout = QVBoxLayout()
            
            for schema in group_schemas:
                row = self._create_widget_for_schema(schema)
                group_layout.addLayout(row)
                
            group_box.setLayout(group_layout)
            self.form_layout.addWidget(group_box)
            
        self.form_layout.addStretch()

    def _create_widget_for_schema(self, schema: HardwareAdvancedParameterSchema) -> QHBoxLayout:
        layout = QHBoxLayout()
        label = QLabel(schema.display_name)
        label.setToolTip(schema.description)
        layout.addWidget(label)
        
        widget = None
        
        if isinstance(schema, NumberParameterSchema):
            widget = QDoubleSpinBox()
            widget.setRange(schema.min_value, schema.max_value)
            widget.setSingleStep(schema.step)
            if schema.default_value is not None:
                widget.setValue(float(schema.default_value))
            if schema.unit:
                widget.setSuffix(f" {schema.unit}")
            
            # Connect
            widget.valueChanged.connect(lambda v, k=schema.key: self._on_value_changed(k, v))
            
        elif isinstance(schema, BooleanParameterSchema):
            widget = QCheckBox()
            if schema.default_value:
                widget.setChecked(True)
                
            widget.toggled.connect(lambda v, k=schema.key: self._on_value_changed(k, v))
            
        elif isinstance(schema, EnumParameterSchema):
            widget = QComboBox()
            widget.addItems(schema.choices)
            if schema.default_value and schema.default_value in schema.choices:
                widget.setCurrentText(str(schema.default_value))
                
            widget.currentTextChanged.connect(lambda v, k=schema.key: self._on_value_changed(k, v))
            
        if widget:
            widget.setToolTip(schema.description)
            layout.addWidget(widget)
        else:
            layout.addWidget(QLabel("Unsupported Type"))
            
        return layout

    def _on_value_changed(self, key: str, value: Any):
        self._current_config[key] = value
        # Emit a copy to be safe
        self.config_changed.emit(self._current_config.copy())

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
                item.layout().deleteLater()
