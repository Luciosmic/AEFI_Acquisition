"""
Hardware Advanced Configuration Panel - Interface V2

Generic panel for hardware advanced configuration.
Generates UI widgets from HardwareAdvancedParameterSchema with grouping support.
"""

from dataclasses import replace
from typing import Dict, List, Any, Optional, Tuple
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

from domain.shared_kernel.value_objects.hardware_configuration.hardware_advanced_parameter_schema import (
    HardwareAdvancedParameterSchema,
    NumberParameterSchema,
    EnumParameterSchema,
    BooleanParameterSchema,
)

# AD9106 scales used only for the optional display conversion
# (raw register <-> % / °); the emitted config stays raw.
# Register value shown as 100 % (and max settable in % mode), per channel:
# ch1/ch2 (excitation) = 5500, same as the Excitation panel's level
# (AdapterExcitationConfigurationAD9106.MAX_EXCITATION_GAIN — excitation
# board saturates above); ch3/ch4 (lock-in reference) = 10000.
_AD9106_GAIN_100_PERCENT = {"ch1_gain": 5500, "ch2_gain": 5500, "ch3_gain": 10000, "ch4_gain": 10000}
_AD9106_PHASE_FULL_SCALE = 65536  # 16-bit phase word over 360°


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
    save_default_requested = Signal(dict) # full config dict
    reset_default_requested = Signal()  # no payload — reset always uses the stored default file
    # Hardcoded deviation from the schema-generic pattern above — explicitly
    # accepted (see plan): synchronous detection calibration/compensation
    # controls, not part of HardwareAdvancedParameterSchema.
    save_calibration_point_requested = Signal()
    compensation_toggle_requested = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_hardware_id: Optional[str] = None
        self._specs: List[HardwareAdvancedParameterSchema] = []
        self._widgets: Dict[str, QWidget] = {}
        self._group_boxes: Dict[str, QGroupBox] = {}
        # Unit mode the current widgets were BUILT with — read by
        # _display_conversion, so toggling can still read the old widgets
        # back to raw before rebuilding.
        self._physical_units_active = False

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
        # Display-only: gain in % (see _AD9106_GAIN_100_PERCENT), phase in degrees. The
        # config emitted to the presenter stays in raw register units.
        self._physical_units_checkbox = QCheckBox("Gain en % / Phase en °")
        self._physical_units_checkbox.setToolTip(
            "Affiche les gains en % (DDS1/DDS2 : 100 % = 5500, comme le panel Excitation ; "
            "DDS3/DDS4 : 100 % = 10000) et les phases en degrés (65536 = 360°). "
            "Les valeurs appliquées restent les registres bruts."
        )
        self._physical_units_checkbox.setVisible(False)
        self._physical_units_checkbox.toggled.connect(self._on_physical_units_toggled)
        hw_layout.addWidget(self._physical_units_checkbox)
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
        
        # Buttons layout
        btn_layout = QHBoxLayout()

        # No "Apply Configuration" button: each field auto-applies on commit
        # (arrow click / Enter / focus-loss for spinboxes — see
        # _wire_spinbox_commit — immediately for combo/checkbox).
        # apply_requested is still emitted, just triggered
        # per-field instead of by a manual click.

        # Save Default button
        self._save_default_btn = QPushButton("Save as Default")
        self._save_default_btn.setEnabled(False)
        self._save_default_btn.clicked.connect(self._on_save_default_clicked)
        btn_layout.addWidget(self._save_default_btn)

        # Reset to Default button — counterpart to Save as Default: that
        # captures a baseline, this discards the current applied/last state
        # and reverts to it.
        self._reset_default_btn = QPushButton("Reset to Default")
        self._reset_default_btn.setEnabled(False)
        self._reset_default_btn.clicked.connect(self.reset_default_requested.emit)
        btn_layout.addWidget(self._reset_default_btn)

        # Synchronous detection calibration/compensation controls — hardcoded
        # deviation from the schema-generic buttons above, explicitly
        # accepted, and specific to the "ad9106_dds" hardware only (see
        # _update_synchronous_detection_controls_visibility): hidden for any
        # other hardware selection.
        self._save_calibration_point_btn = QPushButton("Enregistrer comme point de calibration")
        self._save_calibration_point_btn.clicked.connect(self.save_calibration_point_requested.emit)
        self._save_calibration_point_btn.setVisible(False)
        btn_layout.addWidget(self._save_calibration_point_btn)

        # A toggle, not an action button — QCheckBox rather than a checkable
        # QPushButton, so it reads unambiguously as on/off state.
        self._compensation_toggle_checkbox = QCheckBox("Compensation active")
        self._compensation_toggle_checkbox.toggled.connect(self._on_compensation_toggle_clicked)
        self._compensation_toggle_checkbox.setVisible(False)
        btn_layout.addWidget(self._compensation_toggle_checkbox)

        main_layout.addLayout(btn_layout)
    
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
                conversion = self._display_conversion(spec.key)
                if conversion:
                    label_text += f" ({conversion[0]})"
                elif isinstance(spec, NumberParameterSchema) and spec.unit:
                    label_text += f" ({spec.unit})"
                
                label = QLabel(label_text)
                if spec.description:
                    label.setToolTip(spec.description)
                    widget.setToolTip(spec.description)
                
                group_layout.addRow(label, widget)
            
            self._content_layout.addWidget(group_box)
        
        self._content_layout.addStretch()
        self._save_default_btn.setEnabled(True)
        self._reset_default_btn.setEnabled(True)
        self._update_synchronous_detection_controls_visibility()

    _SYNCHRONOUS_DETECTION_HARDWARE_ID = "ad9106_dds"

    def _update_synchronous_detection_controls_visibility(self) -> None:
        """Calibration point / compensation controls only make sense for the
        AD9106 DDS hardware — hidden for any other hardware selection."""
        is_ad9106 = self._current_hardware_id == self._SYNCHRONOUS_DETECTION_HARDWARE_ID
        self._save_calibration_point_btn.setVisible(is_ad9106)
        self._compensation_toggle_checkbox.setVisible(is_ad9106)
        self._physical_units_checkbox.setVisible(is_ad9106)

    def _display_conversion(self, key: str) -> Optional[Tuple[str, float, Optional[float]]]:
        """(unit, display units per register LSB, display max or None) for an
        AD9106 gain/phase register while the physical-units display is
        active, else None."""
        if not self._physical_units_active or self._current_hardware_id != self._SYNCHRONOUS_DETECTION_HARDWARE_ID:
            return None
        if key in _AD9106_GAIN_100_PERCENT:
            return "%", 100.0 / _AD9106_GAIN_100_PERCENT[key], 100.0
        if key.startswith("ch") and key.endswith("_phase"):
            return "°", 360.0 / _AD9106_PHASE_FULL_SCALE, None
        return None

    def _on_physical_units_toggled(self, checked: bool) -> None:
        """Rebuild the widgets in the other unit, carrying over what they
        currently show (read back to raw with the OLD unit mode first)."""
        raw = self._get_current_config()
        self._physical_units_active = checked
        if self._current_hardware_id is None:
            return
        # Keep each spec's original value type — _create_widget picks
        # QSpinBox vs QDoubleSpinBox from it.
        specs = [
            replace(s, default_value=type(s.default_value)(raw[s.key])) if s.key in raw else s
            for s in self._specs
        ]
        self.set_parameter_specs(self._current_hardware_id, specs)

    def _wire_spinbox_commit(self, widget) -> None:
        """Apply on arrow click / arrow key, Enter, or focus-loss — but not
        on every typed keystroke: with keyboard tracking off, valueChanged
        only fires on those commits. Called AFTER the initial setValue, so
        building the panel never applies anything."""
        widget.setKeyboardTracking(False)
        # Mouse wheel disabled: the panel scrolls, and a wheel passing over
        # a spinbox would otherwise silently write a hardware register.
        widget.wheelEvent = lambda event: event.ignore()
        widget.valueChanged.connect(lambda _: self._on_parameter_changed())
        widget.valueChanged.connect(lambda _: self._auto_apply())

    def _create_widget(self, spec: HardwareAdvancedParameterSchema) -> QWidget:
        """Create appropriate widget based on spec type."""
        conversion = self._display_conversion(spec.key)
        if isinstance(spec, NumberParameterSchema) and conversion:
            # 3 decimals is finer than 1 LSB for both (0.006 % / 0.0055 °),
            # so raw -> display -> raw round-trips exactly.
            unit, per_lsb, display_max = conversion
            widget = QDoubleSpinBox()
            widget.setDecimals(3)
            widget.setSingleStep(1.0)
            widget.setWrapping(unit == "°")
            widget.setRange(spec.min_value * per_lsb, display_max or spec.max_value * per_lsb)
            widget.setValue(spec.default_value * per_lsb)
            self._wire_spinbox_commit(widget)

        elif isinstance(spec, NumberParameterSchema):
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
            self._wire_spinbox_commit(widget)

        elif isinstance(spec, EnumParameterSchema):
            widget = QComboBox()
            widget.addItems(spec.choices)
            if spec.default_value in spec.choices:
                widget.setCurrentText(str(spec.default_value))
            widget.currentTextChanged.connect(lambda: self._on_parameter_changed())
            # A combo selection is itself a complete, discrete commit.
            widget.currentTextChanged.connect(lambda _: self._auto_apply())

        elif isinstance(spec, BooleanParameterSchema):
            widget = QCheckBox()
            widget.setChecked(bool(spec.default_value))
            widget.toggled.connect(lambda: self._on_parameter_changed())
            # A checkbox toggle is itself a complete, discrete commit.
            widget.toggled.connect(lambda _: self._auto_apply())
            
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
    
    def _auto_apply(self):
        """Apply the current full config — triggered per-field on commit
        (spinbox Enter/focus-loss, combo selection, checkbox toggle), not by
        a manual button."""
        config = self._get_current_config()
        self.apply_requested.emit(config)

    def _on_save_default_clicked(self):
        """Handle save default button click."""
        config = self._get_current_config()
        self.save_default_requested.emit(config)

    def _on_compensation_toggle_clicked(self, checked: bool):
        """Handle the compensation checkbox being toggled by the user. Not
        called by set_compensation_enabled_state (blockSignals guards
        against that)."""
        self.compensation_toggle_requested.emit(checked)
    
    def _get_current_config(self) -> Dict[str, Any]:
        """Get current configuration from widgets — always in raw register
        units, whatever the display unit mode."""
        config = {}
        for key, widget in self._widgets.items():
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                conversion = self._display_conversion(key)
                config[key] = int(round(widget.value() / conversion[1])) if conversion else widget.value()
            elif isinstance(widget, QComboBox):
                config[key] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                config[key] = widget.isChecked()
        return config
    
    def set_status_message(self, message: str):
        """Update status label."""
        self._status_label.setText(message)

    def set_compensation_enabled_state(self, enabled: bool):
        """Update the compensation checkbox from external state (service
        refresh_state / other panel) without re-emitting
        compensation_toggle_requested — same blockSignals pattern as
        ExcitationPanel.set_link_state."""
        if self._compensation_toggle_checkbox.isChecked() == enabled:
            return
        self._compensation_toggle_checkbox.blockSignals(True)
        self._compensation_toggle_checkbox.setChecked(enabled)
        self._compensation_toggle_checkbox.blockSignals(False)
    
    def clear_parameters(self):
        """Clear parameter widgets."""
        self._specs = []
        self._widgets.clear()
        self._group_boxes.clear()
        while self._content_layout.count():
            child = self._content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._save_default_btn.setEnabled(False)
        self._reset_default_btn.setEnabled(False)
        self._current_hardware_id = None
        self._update_synchronous_detection_controls_visibility()



