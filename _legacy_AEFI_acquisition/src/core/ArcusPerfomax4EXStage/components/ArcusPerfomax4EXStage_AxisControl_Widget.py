from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QPushButton

class AxisControlWidget(QGroupBox):
    """Widget de contrôle pour un axe (X ou Y)"""
    def __init__(self, axis_name, axis_key, color='#2E86AB', emoji='📐'):
        super().__init__(f"{emoji} Axe {axis_name}")
        self.axis_key = axis_key
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {color};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)
        main_layout = QVBoxLayout()
        # Ligne horizontale pour Cible uniquement
        cible_layout = QHBoxLayout()
        self.target_label = QLabel("Cible:")
        self.target_input = QDoubleSpinBox()
        # Permettre la saisie de toute valeur, mais corriger après édition
        self._target_min = 0
        self._target_max = 127.07 if axis_key == "x" else 122.78
        self.target_input.setMinimum(-9999)
        self.target_input.setMaximum(9999)
        self.target_input.setValue(60)
        self.target_input.setDecimals(3)
        self.target_input.setSuffix(" cm")
        self.target_input.setStyleSheet("font-size: 14px; padding: 5px;")
        self.target_input.editingFinished.connect(self._clamp_target_input)
        cible_layout.addWidget(self.target_label)
        cible_layout.addWidget(self.target_input)
        main_layout.addLayout(cible_layout)
        # Boutons
        self.move_btn = QPushButton("🎯 Move To")
        self.home_btn = QPushButton("🏠 Home")
        self.stop_btn = QPushButton("⏸️ Stop")
        self.emergency_btn = QPushButton("🛑 STOP!")
        self.move_btn.setStyleSheet("QPushButton { background-color: #2E86AB; color: white; font-weight: bold; padding: 10px; }")
        self.home_btn.setStyleSheet("QPushButton { background-color: #2E86AB; color: white; font-weight: bold; padding: 10px; }")
        self.stop_btn.setStyleSheet("QPushButton { background-color: #8B0000; color: white; font-weight: bold; padding: 10px; }")
        self.emergency_btn.setStyleSheet("QPushButton { background-color: #8B0000; color: white; font-weight: bold; padding: 10px; }")
        btn_row1 = QHBoxLayout()
        btn_row1.addWidget(self.move_btn)
        btn_row1.addWidget(self.home_btn)
        btn_row2 = QHBoxLayout()
        btn_row2.addWidget(self.stop_btn)
        btn_row2.addWidget(self.emergency_btn)
        main_layout.addLayout(btn_row1)
        main_layout.addLayout(btn_row2)
        main_layout.addStretch()
        self.setMaximumHeight(200)  # Ajuste la valeur selon le rendu souhaité
        self.setMaximumWidth(300)
        self.setLayout(main_layout)
    def update_position(self, position_inc):
        pass  # Plus d'affichage de la position ici
    
    def get_target_position(self):
        """Retourne la position cible saisie en cm (pour conversion)"""
        return self.target_input.value()

    def _clamp_target_input(self):
        """Force la valeur dans les bornes si l'utilisateur entre une valeur hors borne (comportement explicite)"""
        val = self.target_input.value()
        minv = self._target_min
        maxv = self._target_max
        if val < minv:
            self.target_input.setValue(minv)
        elif val > maxv:
            self.target_input.setValue(maxv) 