from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QGridLayout
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import numpy as np
from typing import List, Dict

# DTO pour config canal (domain value object)
class ChannelConfigDTO:
    def __init__(self, name: str, index: int, color: str, attr: str, is_dotted: bool = False):
        self.name = name
        self.index = index
        self.color = color
        self.attr = attr
        self.is_dotted = is_dotted  # Pour style pointillé si needed

# Service application pour orchestration visualisation
class VisualizationService:
    def __init__(self, acquisition_port):  # Port pour infrastructure
        self.acquisition_port = acquisition_port
        self.current_unit = "µV"
        self.v_to_vm_factor = 63600.0

    def convert_value(self, raw: float, channel_index: int, unit: str) -> float:
        if unit == "Codes ADC":
            return raw
        voltage = self.acquisition_port.convert_adc_to_voltage(raw, channel_index)
        if unit == "V/m":
            return voltage * self.v_to_vm_factor
        elif unit == "mV":
            return voltage * 1000
        elif unit == "µV":
            return voltage * 1_000_000
        return voltage  # Default V

    def get_stats(self, values: List[float]) -> Dict[str, float]:
        if not values:
            return {"mean": 0, "std": 0}
        return {"mean": np.mean(values), "std": np.std(values) if len(values) > 1 else 0}

# === 1. Abstract Factory (construction UI) ===
class SignalViewerFactory:
    """Construit visualiseurs selon type de signal"""
    
    @staticmethod
    def create_viewer(signal_type: str, config: dict):
        viewers = {
            'time_series': SignalViewerWidget,  # Utilise le widget existant
            'vector_field': SignalViewerWidget,  # À implémenter si needed
            'spectrum': SignalViewerWidget       # À implémenter si needed
        }
        viewer_class = viewers.get(signal_type, SignalViewerWidget)
        # Injection des dépendances via config
        adapter = config.get('data_adapter')
        strategy = config.get('display_strategy')
        service = config.get('display_service')
        return viewer_class(adapter, strategy, service, config.get('channels', []))

# === 2. Strategy (rendu adaptatif) ===
from abc import ABC, abstractmethod

class SignalDisplayStrategy(ABC):
    """Stratégie de rendu graphique"""
    
    @abstractmethod
    def render(self, data, canvas):
        pass

class TimeSeriesDisplayStrategy(SignalDisplayStrategy):
    def render(self, data, canvas):
        # Rendu existant adapté
        for ch in data.channels:
            vals = data.get_values(ch)
            canvas.plot(data.times, vals, pen=pg.mkPen(ch.color, width=2, style=Qt.DotLine if ch.is_dotted else Qt.SolidLine), name=ch.name)

# Ajouter d'autres strategies si needed (ex. VectorFieldDisplayStrategy)

# === 3. Adapter (source de données) ===
class SignalDataAdapter(ABC):
    """Adapte différentes sources → format unifié"""
    
    @abstractmethod
    def fetch_data(self) -> dict:  # Retourne dict avec 'times', 'values', etc.
        pass

class AcquisitionManagerAdapter(SignalDataAdapter):
    def __init__(self, manager):
        self.manager = manager
    
    def fetch_data(self) -> dict:
        samples = self.manager.get_latest_samples(100)  # Exemple
        times = [s.timestamp.timestamp() for s in samples]
        values = {}  # Dict par channel
        # ... logique d'adaptation ...
        return {'times': times, 'values': values}

# === 4. DisplayService (formatage) ===
class DisplayConversionService:
    def __init__(self, visualization_service):
        self.service = visualization_service
    
    def format_for_display(self, raw_data: dict) -> dict:
        formatted = {}
        for ch in raw_data['channels']:
            raw_vals = raw_data['values'].get(ch.name, [])
            formatted[ch.name] = [self.service.convert_value(r, ch.index, self.service.current_unit) for r in raw_vals]
        return formatted

# === 5. Widget Composite (adapté de l'existant) ===
class SignalViewerWidget(QWidget):
    """Widget générique de visualisation"""
    
    def __init__(self, data_adapter, display_strategy, display_service, channels: List[ChannelConfigDTO], parent=None):
        super().__init__(parent)
        self.data_adapter = data_adapter
        self.display_strategy = display_strategy
        self.display_service = display_service
        self.channels = channels  # Du config existant
        self._build_ui()  # Réutilise _build_ui existant
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addLayout(self._build_controls())
        layout.addWidget(self._build_graph())
        layout.addLayout(self._build_numeric_display())

    def _build_controls(self):
        hl = QHBoxLayout()
        self.checkboxes = {}
        for ch in self.channels:
            cb = QCheckBox(ch.name)
            cb.setChecked(True)
            cb.setStyleSheet(f"color:{ch.color};font-weight:bold;")
            cb.stateChanged.connect(self._update_visibility)
            self.checkboxes[ch.name] = cb
            hl.addWidget(cb)
        hl.addStretch()
        return hl

    def _build_graph(self):
        self.plot = pg.PlotWidget()
        self.plot.setBackground('#353535')
        self.plot.showGrid(x=True, y=True, alpha=0.2)
        self.plot.setLabel('left', f'Valeur ({self.display_service.service.current_unit})')
        self.plot.setLabel('bottom', 'Temps (s)')
        self.plot.addLegend()
        self.curves = {}
        for ch in self.channels:
            style = Qt.DotLine if ch.is_dotted else Qt.SolidLine
            pen = pg.mkPen(ch.color, width=2, style=style)
            c = self.plot.plot([], [], pen=pen, name=ch.name)
            self.curves[ch.name] = c
        self._update_visibility()
        return self.plot

    def _update_visibility(self):
        for name, cb in self.checkboxes.items():
            self.curves[name].setVisible(cb.isChecked())

    def _build_numeric_display(self):
        grid = QGridLayout()
        self.value_labels = {}
        self.stats_labels = {}
        for idx, ch in enumerate(self.channels):
            row = idx // 3
            col = idx % 3
            name_lbl = QLabel(ch.name)
            name_lbl.setStyleSheet(f"color:{ch.color};font-weight:bold;")
            val_lbl = QLabel("0.000")
            val_lbl.setStyleSheet(f"color:{ch.color};")
            stats_lbl = QLabel("μ: --\nσ: --")
            stats_lbl.setStyleSheet(f"color:{ch.color};")
            grid.addWidget(name_lbl, row * 3, col)
            grid.addWidget(val_lbl, row * 3 + 1, col)
            grid.addWidget(stats_lbl, row * 3 + 2, col)
            self.value_labels[ch.name] = val_lbl
            self.stats_labels[ch.name] = stats_lbl
        return grid

    def update_visualization(self):
        raw_data = self.data_adapter.fetch_data()
        raw_data['channels'] = self.channels  # Inject channels
        formatted_data = self.display_service.format_for_display(raw_data)
        self.display_strategy.render(formatted_data, self.plot)  # self.plot du _build_graph

# Factory pour créer le visualiseur UI avec injection de dépendances
def create_temporal_signal_visualizer(visualization_service, channels: List[ChannelConfigDTO], parent=None) -> TemporalSignalVisualizer:
    """Factory pour instancier le widget UI avec service et configs injectés."""
    return TemporalSignalVisualizer(visualization_service, channels, parent)
