"""
Generic hardware configuration tab with data-driven UI generation.

Responsibility:
- Generate UI widgets from ParameterSpec list
- Provide unified interface for all hardware configs
- Handle validation at widget level

Rationale:
- Single widget to maintain instead of many
- Adapters define their own UI requirements
- Automatic validation from specs

Design:
- Generates widgets from specs
- 3-level validation (Widget/Adapter/Domain)
- Type-safe configuration retrieval
"""

from PyQt5.QtWidgets import (QWidget, QFormLayout, QSpinBox, QSlider, 
                             QComboBox, QCheckBox, QLineEdit, QLabel,
                             QVBoxLayout, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal
from typing import Dict, List, Any, Tuple, Optional

from .parameter_spec import ParameterSpec


# Modern dark theme colors
COLORS = {
    'primary_blue': '#2E86AB',
    'success_green': '#2A9D8F',
    'dark_bg': '#353535',
    'darker_bg': '#252525',
    'text_white': '#FFFFFF',
    'border_gray': '#555555'
}


class GenericHardwareConfigTab(QWidget):
    """
    Generic widget that generates UI from parameter specifications.
    
    This widget automatically creates appropriate UI controls based on
    ParameterSpec definitions provided by hardware adapters.
    
    Example:
        >>> specs = [
        ...     ParameterSpec(name='freq_hz', label='Frequency', type='spinbox',
        ...                   default=1000, range=(100, 10000), unit='Hz'),
        ...     ParameterSpec(name='gain', label='Gain', type='combo',
        ...                   default='1', options=['1', '2', '4', '8'])
        ... ]
        >>> tab = GenericHardwareConfigTab(title="AD9106 Config", param_specs=specs)
    """
    
    # Signal emitted when configuration changes
    config_changed = pyqtSignal(dict)  # {param_name: value}
    
    def __init__(self, title: str, param_specs: List[ParameterSpec], parent=None):
        super().__init__(parent)
        self.title = title
        self._specs = {spec.name: spec for spec in param_specs}
        self._widgets: Dict[str, QWidget] = {}
        self._build_ui()
    
    def _build_ui(self):
        """Build UI from parameter specifications."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            font-weight: bold;
            font-size: 18px;
            color: {COLORS['text_white']};
            padding: 10px;
            border-bottom: 2px solid {COLORS['text_white']};
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Parameters group
        group = QGroupBox("Parameters")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLORS['text_white']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                color: {COLORS['text_white']};
                background-color: {COLORS['darker_bg']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)
        
        form_layout = QFormLayout(group)
        form_layout.setSpacing(10)
        
        # Create widgets from specs
        for spec in self._specs.values():
            widget = self._create_widget(spec)
            self._widgets[spec.name] = widget
            
            # Create label with unit
            label_text = f"{spec.label}"
            if spec.unit:
                label_text += f" ({spec.unit})"
            label = QLabel(label_text)
            label.setStyleSheet(f"color: {COLORS['text_white']};")
            
            if spec.tooltip:
                widget.setToolTip(spec.tooltip)
                label.setToolTip(spec.tooltip)
            
            form_layout.addRow(label, widget)
        
        layout.addWidget(group)
        layout.addStretch()
    
    def _create_widget(self, spec: ParameterSpec) -> QWidget:
        """Create appropriate widget based on spec type."""
        widget_style = f"""
            background-color: {COLORS['dark_bg']};
            color: {COLORS['text_white']};
            border: 1px solid {COLORS['text_white']};
            border-radius: 4px;
            padding: 5px;
            font-size: 14px;
        """
        
        if spec.type == 'spinbox':
            widget = QSpinBox()
            if spec.range:
                widget.setRange(spec.range[0], spec.range[1])
            widget.setValue(spec.default)
            widget.setMinimumWidth(120)
            widget.setStyleSheet(widget_style + f"""
                QSpinBox::up-button {{
                    subcontrol-origin: border;
                    subcontrol-position: top right;
                    width: 20px;
                    border-left: 1px solid {COLORS['text_white']};
                    background-color: {COLORS['primary_blue']};
                }}
                QSpinBox::up-button:hover {{
                    background-color: {COLORS['success_green']};
                }}
                QSpinBox::down-button {{
                    subcontrol-origin: border;
                    subcontrol-position: bottom right;
                    width: 20px;
                    border-left: 1px solid {COLORS['text_white']};
                    background-color: {COLORS['primary_blue']};
                }}
                QSpinBox::down-button:hover {{
                    background-color: {COLORS['success_green']};
                }}
                QSpinBox::up-arrow {{
                    image: none;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-bottom: 6px solid {COLORS['text_white']};
                    width: 0px;
                    height: 0px;
                }}
                QSpinBox::down-arrow {{
                    image: none;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-top: 6px solid {COLORS['text_white']};
                    width: 0px;
                    height: 0px;
                }}
            """)
            widget.valueChanged.connect(lambda: self._on_value_changed())
            
        elif spec.type == 'slider':
            widget = QSlider(Qt.Horizontal)
            if spec.range:
                widget.setRange(spec.range[0], spec.range[1])
            widget.setValue(spec.default)
            widget.setMinimumWidth(200)
            widget.setStyleSheet(widget_style)
            widget.valueChanged.connect(lambda: self._on_value_changed())
            
        elif spec.type == 'combo':
            widget = QComboBox()
            if spec.options:
                widget.addItems(spec.options)
                if spec.default in spec.options:
                    widget.setCurrentText(str(spec.default))
            widget.setMinimumWidth(120)
            widget.setStyleSheet(widget_style + f"""
                QComboBox::drop-down {{
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 25px;
                    border-left: 1px solid {COLORS['text_white']};
                    background-color: {COLORS['primary_blue']};
                }}
                QComboBox::drop-down:hover {{
                    background-color: {COLORS['success_green']};
                }}
                QComboBox::down-arrow {{
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 7px solid {COLORS['text_white']};
                    width: 0px;
                    height: 0px;
                }}
                QComboBox QAbstractItemView {{
                    background-color: {COLORS['darker_bg']};
                    color: {COLORS['text_white']};
                    selection-background-color: {COLORS['primary_blue']};
                    border: 1px solid {COLORS['text_white']};
                }}
            """)
            widget.currentTextChanged.connect(lambda: self._on_value_changed())
            
        elif spec.type == 'checkbox':
            widget = QCheckBox()
            widget.setChecked(bool(spec.default))
            widget.setStyleSheet(f"color: {COLORS['text_white']};")
            widget.stateChanged.connect(lambda: self._on_value_changed())
            
        elif spec.type == 'lineedit':
            widget = QLineEdit()
            widget.setText(str(spec.default))
            widget.setMinimumWidth(120)
            widget.setStyleSheet(widget_style)
            widget.textChanged.connect(lambda: self._on_value_changed())
            
        else:
            raise ValueError(f"Unknown widget type: {spec.type}")
        
        return widget
    
    def _get_widget_value(self, widget: QWidget) -> Any:
        """Extract value from widget."""
        if isinstance(widget, QSpinBox):
            return widget.value()
        elif isinstance(widget, QSlider):
            return widget.value()
        elif isinstance(widget, QComboBox):
            return widget.currentText()
        elif isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QLineEdit):
            return widget.text()
        else:
            raise ValueError(f"Unknown widget type: {type(widget)}")
    
    def _on_value_changed(self):
        """Emit signal when any value changes."""
        self.config_changed.emit(self.get_config())
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration as dictionary.
        
        Returns:
            Dictionary mapping parameter names to values
        """
        return {
            name: self._get_widget_value(widget)
            for name, widget in self._widgets.items()
        }
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """
        Set configuration programmatically.
        
        Args:
            config: Dictionary mapping parameter names to values
        """
        for name, value in config.items():
            if name in self._widgets:
                widget = self._widgets[name]
                
                # Block signals during programmatic update
                widget.blockSignals(True)
                
                if isinstance(widget, QSpinBox):
                    widget.setValue(value)
                elif isinstance(widget, QSlider):
                    widget.setValue(value)
                elif isinstance(widget, QComboBox):
                    widget.setCurrentText(str(value))
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))
                elif isinstance(widget, QLineEdit):
                    widget.setText(str(value))
                
                widget.blockSignals(False)
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        Validate current configuration against specs.
        
        This is Level 1 validation (Widget level) - syntactic validation.
        
        Returns:
            (is_valid, error_message)
        """
        config = self.get_config()
        
        for name, value in config.items():
            spec = self._specs[name]
            is_valid, error_msg = spec.validate_value(value)
            
            if not is_valid:
                return False, error_msg
        
        return True, None
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable/disable all widgets."""
        for widget in self._widgets.values():
            widget.setEnabled(enabled)
