from PyQt5.QtWidgets import QGroupBox, QGridLayout, QLabel, QSpinBox, QPushButton

class SpeedParametersWidget(QGroupBox):
    """Widget pour les paramètres de vitesse et accélération"""
    def __init__(self):
        super().__init__("⚙️ Paramètres de Vitesse & Accélération")
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #A23B72;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        layout = QGridLayout()
        # En-têtes
        headers = ["", "Low Speed", "High Speed", "Acceleration", "Deceleration"]
        for i, header in enumerate(headers):
            if header:
                label = QLabel(header)
                label.setStyleSheet("font-weight: bold; color: #A23B72;")
                layout.addWidget(label, 0, i)
        # Paramètres pour X et Y
        self.params = {}
        colors = ["#0000FF", "#FFA500"]  # Bleu pour X, Orange pour Y
        for row, (axis, color) in enumerate([("X", colors[0]), ("Y", colors[1])]):
            axis_key = axis.lower()
            # Label de l'axe
            axis_label = QLabel(f"Axe {axis}")
            axis_label.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 14px;")
            layout.addWidget(axis_label, row + 1, 0)
            # Paramètres
            self.params[axis_key] = {}
            param_names = ["ls", "hs", "acc", "dec"]
            default_values = [10, 1500, 300, 300]
            for col, (param, default) in enumerate(zip(param_names, default_values)):
                spinbox = QSpinBox()
                spinbox.setRange(1, 10000)
                spinbox.setValue(default)
                spinbox.setStyleSheet("font-size: 12px; padding: 3px;")
                layout.addWidget(spinbox, row + 1, col + 1)
                self.params[axis_key][param] = spinbox
        # Bouton d'application
        self.apply_btn = QPushButton("🚀 Appliquer Paramètres")
        self.apply_btn.setStyleSheet("QPushButton { background-color: #2E86AB; font-weight: bold; padding: 10px; }")
        layout.addWidget(self.apply_btn, 3, 0, 1, 5)
        self.setLayout(layout)
    def get_params(self, axis):
        """Retourne les paramètres d'un axe"""
        return {
            'ls': self.params[axis]['ls'].value(),
            'hs': self.params[axis]['hs'].value(),
            'acc': self.params[axis]['acc'].value(),
            'dec': self.params[axis]['dec'].value()
        }
    def set_params(self, axis, params):
        """Met à jour les paramètres affichés"""
        for param_name, value in params.items():
            if param_name in self.params[axis]:
                self.params[axis][param_name].setValue(value) 