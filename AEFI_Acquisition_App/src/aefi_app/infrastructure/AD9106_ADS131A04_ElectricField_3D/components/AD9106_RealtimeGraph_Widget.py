from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QSpinBox
from PyQt5.QtCore import Qt
import pyqtgraph as pg

class RealtimeGraphWidget(QWidget):
    WINDOW_DURATION = 2.0
    DEFAULT_PERIOD  = 0.1
    MAX_POINTS_EXTRA = 10
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
    def __init__(self, acquisition_manager, parent=None):
        super().__init__(parent)
        self.acquisition_manager = acquisition_manager
        self.current_unit = "µV"
        self.v_to_vm_factor = 63600.0
        self._build_ui()
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addLayout(self._build_controls())
        layout.addWidget(self._build_plot())
    def _build_controls(self):
        hl = QHBoxLayout()
        self.checkboxes = {}
        for ch in self.CHANNELS:
            cb = QCheckBox(ch["name"])
            # Décocher par défaut ADC2_Ch3 et ADC2_Ch4
            if ch["name"] in ["ADC2_Ch3", "ADC2_Ch4"]:
                cb.setChecked(False)
            else:
                cb.setChecked(True)
            cb.setStyleSheet(f"color:{ch['color']};font-weight:bold;")
            cb.stateChanged.connect(self._on_checkbox_changed)
            self.checkboxes[ch["name"]] = cb
            hl.addWidget(cb)
        hl.addStretch()
        return hl
    def _build_plot(self):
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#353535')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.2)
        self.plot_widget.setLabel('left', f'Valeur ({self.current_unit})')
        self.plot_widget.setLabel('bottom', 'Temps (s)')
        self.plot_widget.addLegend()
        self.curves = {}
        for ch in self.CHANNELS:
            # Style pointillé pour les signaux Quadrature
            style = Qt.DotLine if "Quadrature" in ch['name'] else Qt.SolidLine
            pen = pg.mkPen(ch['color'], width=2, style=style)
            c = self.plot_widget.plot([], [], pen=pen, name=ch['name'])
            self.curves[ch['name']] = c
        
        # Synchronisation initiale de la visibilité avec les checkboxes
        self._sync_initial_visibility()
        
        return self.plot_widget
    def _sync_initial_visibility(self):
        """Synchronise la visibilité initiale des courbes avec l'état des checkboxes"""
        for name, cb in self.checkboxes.items():
            self.curves[name].setVisible(cb.isChecked())

    def _on_checkbox_changed(self):
        for name, cb in self.checkboxes.items():
            self.curves[name].setVisible(cb.isChecked())
    def set_conversion_parameters(self, unit: str, v_to_vm_factor: float):
        """
        🔄 API PUBLIQUE pour synchronisation externe des unités
        Permet de changer l'unité et le facteur de conversion depuis l'UI globale
        """
        #print(f"[DEBUG RealtimeGraph COMPONENTS] set_conversion_parameters: unit={unit}, factor={v_to_vm_factor}")
        self.current_unit = unit
        self.v_to_vm_factor = v_to_vm_factor
        # 🔄 SYNCHRONISATION: Mise à jour du label Y-axis avec nouvelle unité
        self.plot_widget.setLabel('left', f'Valeur RMS ({unit})')
        #print(f"[DEBUG RealtimeGraph COMPONENTS] Y-axis label mis à jour: 'Valeur ({unit})'")
    
    def get_current_unit(self) -> str:
        """🔄 API PUBLIQUE: Retourne l'unité actuelle"""
        return self.current_unit
    
    def get_v_to_vm_factor(self) -> float:
        """🔄 API PUBLIQUE: Retourne le facteur de conversion V→V/m actuel"""
        return self.v_to_vm_factor
    def _convert(self, raw, ch_index):
        if self.current_unit == "Codes ADC":
            return raw
        v = self.acquisition_manager.convert_adc_to_voltage(raw, channel=ch_index)
        return {
            "V/m": v * self.v_to_vm_factor,
            "mV":  v * 1000,
            "µV":  v * 1_000_000,
        }.get(self.current_unit, v)
    def update_graph(self):
        samples = self.acquisition_manager.get_latest_samples(
            int(self.WINDOW_DURATION / self.DEFAULT_PERIOD + self.MAX_POINTS_EXTRA)
        )
        times = [s.timestamp.timestamp() for s in samples]
        t0 = times[0] if times else 0
        times = [t - t0 for t in times]
        for ch in self.CHANNELS:
            raw = [getattr(s, ch["attr"]) for s in samples]
            vals = [self._convert(r, ch["index"]) for r in raw]
            self.curves[ch["name"]].setData(times, vals) 