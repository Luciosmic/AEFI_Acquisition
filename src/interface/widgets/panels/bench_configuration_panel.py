"""
Bench Configuration Panel

Composite dock for the bench configuration: the hardware component catalog
(declare a component, record its characterization, mount it), one tab per
component kind. Calibrations live in the Calibration panel. Pure
composition — no logic, no signals of its own: dashboard_wiring.py connects
directly to the sub-panels exposed as attributes.
"""

from typing import Dict

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from interface.widgets.panels.hardware_component_panel import HardwareComponentPanel

# HardwareComponentKindDTO.key -> group tab it lives under. A kind absent from
# both sets (the sensor) stays a top-level tab.
_MOTION_KEYS = frozenset({"motors", "stepper_driver"})
_ELECTRONICS_KEYS = frozenset(
    {"conditioning_electronics_board", "excitation_electronics_board", "signal_generation_chip", "adc", "microcontroller"}
)
_MOTION_GROUP_LABEL = "Mouvement"
_ELECTRONICS_GROUP_LABEL = "Électronique"


class BenchConfigurationPanel(QWidget):
    """Tabbed dock hosting one catalog tab per hardware component kind."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hardware_component_panels: Dict[str, HardwareComponentPanel] = {}

        self._tabs = QTabWidget()
        self._tabs.setUsesScrollButtons(True)
        # Groups are created with their first component tab (the kinds come from the wiring).
        self._group_tabs: Dict[str, QTabWidget] = {}
        # assembly key -> its tab inside "Électronique" (the DDS, the ADC and
        # the microcontroller form the digital-analog-signals-processing-unit).
        self._assembly_tabs: Dict[str, QTabWidget] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tabs)

    def add_hardware_component_tab(self, kind) -> HardwareComponentPanel:
        """One tab per hardware component kind (`HardwareComponentKindDTO`),
        added at wiring time since the kinds come from the application layer.
        A kind that belongs to an assembly goes under that assembly's tab."""
        panel = HardwareComponentPanel(kind)
        self.hardware_component_panels[kind.key] = panel
        if kind.key in _MOTION_KEYS:
            self._group(_MOTION_GROUP_LABEL).addTab(panel, kind.label)
        elif kind.key in _ELECTRONICS_KEYS:
            self._electronics_parent(kind).addTab(panel, kind.label)
        else:
            self._tabs.addTab(panel, kind.label)
        return panel

    def _electronics_parent(self, kind) -> QTabWidget:
        assembly_key = getattr(kind, "assembly_key", None)
        if assembly_key is None:
            return self._group(_ELECTRONICS_GROUP_LABEL)
        if assembly_key not in self._assembly_tabs:
            tabs = QTabWidget()
            tabs.setUsesScrollButtons(True)
            self._group(_ELECTRONICS_GROUP_LABEL).addTab(tabs, kind.assembly_label)
            self._assembly_tabs[assembly_key] = tabs
        return self._assembly_tabs[assembly_key]

    def _group(self, label: str) -> QTabWidget:
        if label not in self._group_tabs:
            tabs = QTabWidget()
            tabs.setUsesScrollButtons(True)
            self._tabs.addTab(tabs, label)
            self._group_tabs[label] = tabs
        return self._group_tabs[label]
