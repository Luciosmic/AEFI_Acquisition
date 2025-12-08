import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QFormLayout
from PyQt5.QtCore import QTimer
from pymycobot.mycobot import MyCobot
import time

class MyCobotGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.mc = MyCobot("COM9", 115200)  # Initialisation du robot (ajustez le port si nécessaire)
        
        self.initUI()
        
        # Timer optionnel pour rafraîchissement automatique (toutes les 2 secondes, décommentez si voulu)
        # self.timer = QTimer(self)
        # self.timer.timeout.connect(self.refresh_angles)
        # self.timer.start(2000)

    def initUI(self):
        self.setWindowTitle("Contrôle des Angles myCobot")
        self.setGeometry(100, 100, 400, 300)
        
        layout = QVBoxLayout()
        
        # Section pour angles actuels
        self.current_angles_label = QLabel("Angles actuels : Non rafraîchis")
        layout.addWidget(self.current_angles_label)
        
        refresh_button = QPushButton("Rafraîchir angles actuels")
        refresh_button.clicked.connect(self.refresh_angles)
        layout.addWidget(refresh_button)
        
        # Section pour nouveaux angles
        form_layout = QFormLayout()
        
        self.angle_inputs = []
        for i in range(1, 7):
            label = QLabel(f"Joint {i} (degrés) :")
            input_field = QLineEdit()
            input_field.setPlaceholderText("Entrez un angle (ex: 0)")
            self.angle_inputs.append(input_field)
            form_layout.addRow(label, input_field)
        
        layout.addLayout(form_layout)
        
        # Bouton Valider
        validate_button = QPushButton("Valider et envoyer")
        validate_button.clicked.connect(self.send_angles)
        layout.addWidget(validate_button)
        
        self.setLayout(layout)

    def refresh_angles(self):
        try:
            angles = self.mc.get_angles()
            self.current_angles_label.setText(f"Angles actuels : {angles}")
        except Exception as e:
            self.current_angles_label.setText(f"Erreur : {e}")

    def send_angles(self):
        try:
            angles = []
            for input_field in self.angle_inputs:
                value = input_field.text().strip()
                if not value:
                    raise ValueError("Tous les champs doivent être remplis.")
                angles.append(float(value))
            
            if len(angles) != 6:
                raise ValueError("Il faut exactement 6 angles.")
            
            # Envoyer les angles avec vitesse 50
            self.mc.send_angles(angles, 50)
            time.sleep(3)  # Attente pour que le mouvement se termine
            
            # Rafraîchir automatiquement les angles actuels
            self.refresh_angles()
            
        except ValueError as ve:
            self.current_angles_label.setText(f"Erreur de saisie : {ve}")
        except Exception as e:
            self.current_angles_label.setText(f"Erreur pendant l'envoi : {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyCobotGUI()
    window.show()
    sys.exit(app.exec_())