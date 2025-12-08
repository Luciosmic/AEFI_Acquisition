from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QGridLayout, QSpinBox, QDoubleSpinBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QMessageBox

class MainParametersConfigWidget(QWidget):
    """Widget de configuration 3 paramètres (Gain DDS, Fréq Hz, N_avg)"""
    configuration_changed = pyqtSignal(dict)
    GAIN_MIN, GAIN_MAX = 0, 5500 #Max Gain experimentally determined before saturation
    FREQ_MIN, FREQ_MAX = 0.1, 1_000_000.0
    NAVG_MIN, NAVG_MAX = 1, 127 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        #title = QLabel("Configuration Acquisition")
        #title.setStyleSheet("font-weight: bold; font-size: 16px; padding: 10px;")
        #title.setAlignment(Qt.AlignCenter)
        #layout.addWidget(title)
        config_group = QGroupBox()
        config_layout = QGridLayout(config_group)
        config_layout.setSpacing(15)
        gain_label = QLabel("DDS Excitation Gain (%): ")
        self.gain_spinbox = QSpinBox()
        self.gain_spinbox.setRange(0, 100)  # UI en %
        self.gain_spinbox.setValue(int(5000 * 100 / self.GAIN_MAX))  # conversion vers %
        self.gain_spinbox.setSingleStep(1)
        self.gain_spinbox.setToolTip("Gain en % (0-100%), converti automatiquement vers 0-5500")
        self.gain_spinbox.editingFinished.connect(self._on_config_changed)
        self.gain_warning_label = QLabel("")
        self.gain_warning_label.setVisible(False)
        freq_label = QLabel("Frequency (Hz):")
        self.freq_spinbox = QDoubleSpinBox()
        self.freq_spinbox.setRange(self.FREQ_MIN, self.FREQ_MAX)
        self.freq_spinbox.setValue(1000)
        self.freq_spinbox.setDecimals(0)
        self.freq_spinbox.editingFinished.connect(self._on_config_changed)
        navg_label = QLabel("ADC Acquisition Avg:")
        self.navg_spinbox = QSpinBox()
        self.navg_spinbox.setRange(self.NAVG_MIN, self.NAVG_MAX)
        self.navg_spinbox.setValue(10)
        self.navg_spinbox.editingFinished.connect(self._on_config_changed)
        config_layout.addWidget(gain_label, 0, 0)
        config_layout.addWidget(self.gain_spinbox, 0, 1)
        config_layout.addWidget(self.gain_warning_label, 1, 0, 1, 3)
        config_layout.addWidget(freq_label, 2, 0)
        config_layout.addWidget(self.freq_spinbox, 2, 1)
        config_layout.addWidget(navg_label, 3, 0)
        config_layout.addWidget(self.navg_spinbox, 3, 1)
        layout.addWidget(config_group)
    
    def _percent_to_gain(self, percent: int) -> int:
        """Convertit % (0-100) vers valeur directe (0-5500)"""
        return int(percent * self.GAIN_MAX / 100)
    
    def _gain_to_percent(self, gain: int) -> int:
        """Convertit valeur directe (0-5500) vers % (0-100)"""
        return int(gain * 100 / self.GAIN_MAX)
    
    def _on_config_changed(self):
        config = {
            'gain_dds': self._percent_to_gain(self.gain_spinbox.value()),  # conversion % -> valeur directe
            'freq_hz': self.freq_spinbox.value(),
            'n_avg': self.navg_spinbox.value()
        }
        if self.validate_config(config):
            self.configuration_changed.emit(config)
    def set_configuration(self, config: dict):
        if 'gain_dds' in config:
            self.gain_spinbox.setValue(self._gain_to_percent(config['gain_dds']))  # conversion valeur directe -> %
        if 'freq_hz' in config:
            self.freq_spinbox.setValue(config['freq_hz'])
        if 'n_avg' in config:
            self.navg_spinbox.setValue(config['n_avg'])
    def set_enabled(self, enabled: bool):
        self.gain_spinbox.setEnabled(enabled)
        self.freq_spinbox.setEnabled(enabled)
        self.navg_spinbox.setEnabled(enabled)
    def show_gain_warning(self, show: bool):
        if show:
            self.gain_warning_label.setText("Les gains DDS1 et DDS2 sont différents !")
            self.gain_warning_label.setVisible(True)
        else:
            self.gain_warning_label.setVisible(False)
    def validate_config(self, config: dict) -> bool:
        gain = config.get('gain_dds', self._percent_to_gain(self.gain_spinbox.value()))  # conversion pour validation
        freq = config.get('freq_hz', self.freq_spinbox.value())
        n_avg = config.get('n_avg', self.navg_spinbox.value())
        if not (self.GAIN_MIN <= gain <= self.GAIN_MAX):
            QMessageBox.critical(self, "Erreur configuration", f"Gain DDS hors bornes [{self.GAIN_MIN}, {self.GAIN_MAX}] : {gain}")
            return False
        if not (self.FREQ_MIN <= freq <= self.FREQ_MAX):
            QMessageBox.critical(self, "Erreur configuration", f"Fréquence hors bornes [{self.FREQ_MIN}, {self.FREQ_MAX}] : {freq}")
            return False
        if not (self.NAVG_MIN <= n_avg <= self.NAVG_MAX):
            QMessageBox.critical(self, "Erreur configuration", f"N_avg hors bornes [{self.NAVG_MIN}, {self.NAVG_MAX}] : {n_avg}")
            return False
        return True
    def get_configuration(self) -> dict:
        return {
            'gain_dds': self._percent_to_gain(self.gain_spinbox.value()),  # conversion % -> valeur directe
            'freq_hz': self.freq_spinbox.value(),
            'n_avg': self.navg_spinbox.value()
        } 