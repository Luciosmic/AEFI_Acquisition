from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QGridLayout, QLabel, QDoubleSpinBox, QPushButton
from PyQt5.QtCore import Qt
from .AD9106_AdvancedControl_Widget import DDSControlAdvanced
from .ADS131A04_AdvancedControl_Widget import ADCControlAdvanced

class AdvancedSettingsWidget(QWidget):
    def __init__(self, acquisition_manager, parent=None):
        super().__init__(parent)
        self.acquisition_manager = acquisition_manager
        self.dds_controls = {}
        self.init_ui()
    def init_ui(self):
        layout = QHBoxLayout(self)
        dds_group = QGroupBox("Configuration AD9106")
        dds_vlayout = QVBoxLayout(dds_group)
        freq_bar = self._create_control_bar()
        dds_vlayout.addWidget(freq_bar)
        dds_layout = QGridLayout()
        for i in range(1, 5):
            dds_control = DDSControlAdvanced(i, self.acquisition_manager)
            self.dds_controls[i] = dds_control
            row = (i - 1) // 2
            col = (i - 1) % 2
            dds_layout.addWidget(dds_control, row, col)
        dds_vlayout.addLayout(dds_layout)
        layout.addWidget(dds_group, 2)
        adc_group = QGroupBox("Configuration ADS131A04")
        adc_vlayout = QVBoxLayout(adc_group)
        self.adc_control = ADCControlAdvanced(self.acquisition_manager)
        adc_vlayout.addWidget(self.adc_control)
        layout.addWidget(adc_group, 1)
    def _create_control_bar(self):
        group = QGroupBox("🎮 Contrôles Principaux")
        layout = QHBoxLayout(group)
        freq_label = QLabel("📡 Fréquence globale:")
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(0.1, 1_000_000)
        self.freq_spin.setValue(1000)
        self.set_freq_button = QPushButton("✅ Appliquer à tous DDS")
        layout.addWidget(freq_label)
        layout.addWidget(self.freq_spin)
        layout.addWidget(self.set_freq_button)
        layout.addStretch()
        return group
    def set_frequency(self, freq_hz: float):
        self.freq_spin.setValue(freq_hz)
    def set_enabled(self, enabled: bool):
        self.freq_spin.setEnabled(enabled)
        self.set_freq_button.setEnabled(enabled) 