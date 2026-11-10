from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDoubleSpinBox, QGridLayout
from PyQt5.QtCore import Qt

class NumericDisplayWidget(QWidget):
    DEFAULT_UNIT = "µV"
    DEFAULT_V_TO_VM_FACTOR = 63_600.0
    CHANNELS = [
        dict(name="Ex In-Phase", index=1, color="#4A90E2", attr="adc1_ch1"),        # Bleu pour Ex
        dict(name="Ex Quadrature", index=2, color="#4A90E2", attr="adc1_ch2"),     # Bleu pour Ex
        dict(name="Ey In-Phase", index=3, color="#F4D03F", attr="adc1_ch3"),       # Jaune pour Ey
        dict(name="Ey Quadrature", index=4, color="#F4D03F", attr="adc1_ch4"),     # Jaune pour Ey
        dict(name="Ez In-Phase", index=5, color="#E74C3C", attr="adc2_ch1"),       # Rouge pour Ez
        dict(name="Ez Quadrature", index=6, color="#E74C3C", attr="adc2_ch2"),     # Rouge pour Ez
        dict(name="ADC2_Ch3", index=7, color="#95A5A6", attr="adc2_ch3"),          # Gris neutre
        dict(name="ADC2_Ch4", index=8, color="#95A5A6", attr="adc2_ch4"),          # Gris neutre
    ]
    UNITS = ["Codes ADC", "V", "mV", "µV", "V/m"]
    def __init__(self, acquisition_manager, parent=None, hidden_channels=None):
        super().__init__(parent)
        self.acquisition_manager = acquisition_manager
        self.current_unit = self.DEFAULT_UNIT
        self.v_to_vm_factor = self.DEFAULT_V_TO_VM_FACTOR
        self.sync_callback = None  # Callback pour synchronisation externe
        
        # 🔄 ADAPTATION LARGEUR : Widget plus étroit pour faire place au FrameRotationWidget
        self.setMaximumWidth(400)  # Réduit de ~600px à 400px pour optimiser l'espace
        # Filtrer les canaux à afficher (exclure les canaux masqués)
        if hidden_channels is None:
            hidden_channels = []
        self.displayed_channels = [ch for ch in self.CHANNELS if ch["name"] not in hidden_channels]
        self._build_ui()
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addLayout(self._build_header())
        layout.addLayout(self._build_grid())
    def _build_header(self):
        title = QLabel("Unités")
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(self.UNITS)
        self.unit_combo.setCurrentText(self.current_unit)
        self.unit_combo.currentTextChanged.connect(self._on_unit_changed)
        factor_label = QLabel("Facteur V→V/m:")
        self.factor_spinbox = QDoubleSpinBox()
        self.factor_spinbox.setRange(1.0, 1_000_000.0)
        self.factor_spinbox.setValue(self.v_to_vm_factor)
        self.factor_spinbox.valueChanged.connect(self._on_factor_changed)
        h_layout = QHBoxLayout()
        for w in (title, self.unit_combo, factor_label, self.factor_spinbox):
            h_layout.addWidget(w)
        h_layout.addStretch()
        return h_layout
    def _build_grid(self):
        grid = QGridLayout()
        grid.setSpacing(10)
        self.channel_labels = {}
        self.channel_stats_labels = {}
        for idx, ch in enumerate(self.displayed_channels):
            # Ajustement pour une meilleure disposition avec 6 canaux (2 lignes de 3)
            cols_per_row = 6 if len(self.displayed_channels) <= 6 else 4
            row, col = divmod(idx, cols_per_row)
            name_lbl = QLabel(ch["name"])
            name_lbl.setAlignment(Qt.AlignCenter)
            name_lbl.setStyleSheet(f"color: {ch['color']}; font-weight: bold;")  # Application de la couleur
            val_lbl = QLabel("0.000")
            val_lbl.setAlignment(Qt.AlignCenter)
            val_lbl.setStyleSheet(f"color: {ch['color']}; font-weight: bold;")   # Application de la couleur
            self.channel_labels[ch["name"]] = val_lbl
            stats_lbl = QLabel("μ: --\nσ: --")
            stats_lbl.setAlignment(Qt.AlignCenter)
            stats_lbl.setWordWrap(True)
            stats_lbl.setStyleSheet(f"color: {ch['color']};")                    # Application de la couleur
            self.channel_stats_labels[ch["name"]] = stats_lbl
            grid.addWidget(name_lbl, row * 3, col)
            grid.addWidget(val_lbl, row * 3 + 1, col)
            grid.addWidget(stats_lbl, row * 3 + 2, col)
        return grid
    def _on_unit_changed(self, unit):
        print(f"[DEBUG NumericDisplay COMPONENTS] _on_unit_changed: {unit}")
        print(f"[DEBUG NumericDisplay COMPONENTS] sync_callback status: {self.sync_callback}")
        self.current_unit = unit
        # 🔄 SYNCHRONISATION EXTERNE: Appelle le callback si défini
        if self.sync_callback:
            print(f"[DEBUG NumericDisplay COMPONENTS] Calling sync_callback for unit: {unit}")
            self.sync_callback()
        else:
            print(f"[DEBUG NumericDisplay COMPONENTS] No sync_callback defined!")
    def _on_factor_changed(self, factor):
        self.v_to_vm_factor = factor
        # 🔄 SYNCHRONISATION EXTERNE: Appelle le callback si défini
        if self.sync_callback:
            print(f"[DEBUG NumericDisplay COMPONENTS] Calling sync_callback for factor: {factor}")
            self.sync_callback()
    
    # === API PUBLIQUE pour synchronisation externe ===
    def get_current_unit(self) -> str:
        """🔄 API PUBLIQUE: Retourne l'unité actuelle"""
        return self.current_unit
    
    def get_v_to_vm_factor(self) -> float:
        """🔄 API PUBLIQUE: Retourne le facteur de conversion V→V/m actuel"""
        return self.v_to_vm_factor
    
    def set_conversion_parameters(self, unit: str, v_to_vm_factor: float):
        """🔄 API PUBLIQUE: Met à jour les paramètres de conversion (sans émettre de callback)"""
        self.current_unit = unit
        self.v_to_vm_factor = v_to_vm_factor
        self.unit_combo.setCurrentText(unit)
        self.factor_spinbox.setValue(v_to_vm_factor)
    def update_values(self, adc_values: dict):
        buffer = self.acquisition_manager.get_latest_samples(100) if self.acquisition_manager else []
        import numpy as np
        for ch in self.displayed_channels:
            raw = adc_values.get(ch["name"], 0)
            display = self._convert(raw, ch["index"])
            self.channel_labels[ch["name"]].setText(f"{display:.3f}")
            self._update_stats(ch, buffer, np)
    def _convert(self, raw, channel_index):
        if self.current_unit == "Codes ADC":
            return raw
        voltage = self.acquisition_manager.convert_adc_to_voltage(raw, channel=channel_index)
        if self.current_unit == "V/m":
            return voltage * self.v_to_vm_factor
        if self.current_unit == "mV":
            return voltage * 1000
        if self.current_unit == "µV":
            return voltage * 1_000_000
        return voltage
    def _update_stats(self, ch, buffer, np):
        stats_lbl = self.channel_stats_labels[ch["name"]]
        if not buffer:
            stats_lbl.setText("μ: --\nσ: --")
            return
        raw_vals = [getattr(s, ch["attr"], 0) for s in buffer]
        vals = [self._convert(v, ch["index"]) for v in raw_vals]
        if len(vals) > 1:
            mu = np.mean(vals)
            sigma = np.std(vals, ddof=1)
            stats_lbl.setText(f"μ: {mu:.2f}\nσ: {sigma:.2f}")
        else:
            stats_lbl.setText("μ: --\nσ: --") 