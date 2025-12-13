# This file is kept for backward compatibility
# The new implementation is in widget_excitation.py
from .widget_excitation import ExcitationWidget

__all__ = ['ExcitationWidget']
    """
    Passive UI Widget for configuring Excitation Parameters.
    Does NOT know about Presenter. Communicates via Signals/Slots.
    """
    
    # OUTPUT: Emitted when user changes values
    # Args: mode_name (str), level_percent (float), frequency_hz (float)
    excitation_changed = pyqtSignal(str, float, float)

    def __init__(self):
        super().__init__()
        self._init_ui()
        
    def _init_ui(self):
        """Build the UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        
        group = QGroupBox("Excitation Configuration")
        form_layout = QVBoxLayout()
        form_layout.setSpacing(4)
        form_layout.setContentsMargins(8, 8, 8, 8)

        # 1. Mode Selection
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Mode:")
        self.mode_combo = QComboBox()
        # Populate with ExcitationMode names
        for mode in ExcitationMode:
            self.mode_combo.addItem(mode.name)
        
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)
        form_layout.addLayout(mode_layout)

        # 2. Level Selection (Slider + SpinBox)
        level_layout = QHBoxLayout()
        level_label = QLabel("Level (%):")
        
        self.level_slider = QSlider(Qt.Orientation.Horizontal)
        self.level_slider.setRange(0, 100)
        self.level_slider.setValue(0)
        
        self.level_spin = QDoubleSpinBox()
        self.level_spin.setRange(0.0, 100.0)
        self.level_spin.setSingleStep(1.0)
        self.level_spin.setValue(0.0)

        # Synchronize Slider and SpinBox (Internal Widget Logic)
        self.level_slider.valueChanged.connect(lambda v: self.level_spin.setValue(float(v)))
        self.level_spin.valueChanged.connect(lambda v: self.level_slider.setValue(int(v)))

        level_layout.addWidget(level_label)
        level_layout.addWidget(self.level_slider)
        level_layout.addWidget(self.level_spin)
        form_layout.addLayout(level_layout)

        # 3. Frequency Input
        freq_layout = QHBoxLayout()
        freq_label = QLabel("Frequency (Hz):")
        self.freq_spin = QSpinBox()
        self.freq_spin.setRange(0, 1000000) 
        self.freq_spin.setValue(100)
        
        freq_layout.addWidget(freq_label)
        freq_layout.addWidget(self.freq_spin)
        form_layout.addLayout(freq_layout)

        # 4. Signal Connections
        self.mode_combo.currentTextChanged.connect(self._on_user_interaction)
        self.level_spin.valueChanged.connect(self._on_user_interaction)
        self.freq_spin.valueChanged.connect(self._on_user_interaction)

        group.setLayout(form_layout)
        layout.addWidget(group)
        # Remove stretch to avoid wasted space
        self.setLayout(layout)

    def _on_user_interaction(self):
        """Propagate user changes to the world via Signal."""
        mode_name = self.mode_combo.currentText()
        level = self.level_spin.value()
        freq = self.freq_spin.value()
        
        # Emit signal to parent/controller
        self.excitation_changed.emit(mode_name, level, float(freq))

    @pyqtSlot(str, float, float)
    def set_state(self, mode_name: str, level: float, freq: float):
        """
        INPUT: Update UI widgets based on external state (e.g. from Presenter).
        Blocks signals to prevent feedback loops.
        """
        self.blockSignals(True)
        # We also need to block internal children connection or just the widget's own custom signal?
        # Ideally, we block the children triggering _on_user_interaction.
        self.mode_combo.blockSignals(True)
        self.level_spin.blockSignals(True)
        self.level_slider.blockSignals(True)
        self.freq_spin.blockSignals(True)
        
        try:
            # Mode
            idx = self.mode_combo.findText(mode_name)
            if idx >= 0:
                self.mode_combo.setCurrentIndex(idx)
                
            # Level
            self.level_spin.setValue(level)
            self.level_slider.setValue(int(level))
            
            # Frequency
            self.freq_spin.setValue(int(freq))
            
        finally:
            self.mode_combo.blockSignals(False)
            self.level_spin.blockSignals(False)
            self.level_slider.blockSignals(False)
            self.freq_spin.blockSignals(False)
            self.blockSignals(False)
