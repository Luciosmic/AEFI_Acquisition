import sys
import serial
import time
import threading
from collections import deque
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QInputDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal, QObject
import pyqtgraph as pg
import numpy as np

PORT = 'COM10'
BAUDRATE = 1500000
TIMEOUT = 10
WINDOW_SIZE = 100  # Nombre de points affichés

class DataSignal(QObject):
    new_data = pyqtSignal(list)

class AcquisitionThread(threading.Thread):
    def __init__(self, m, data_signal):
        super().__init__()
        self.m = m
        self.data_signal = data_signal
        self.running = False
        self.ser = None

    def run(self):
        try:
            self.ser = serial.Serial(
                port=PORT,
                baudrate=BAUDRATE,
                bytesize=8,
                stopbits=serial.STOPBITS_ONE,
                parity=serial.PARITY_NONE,
                timeout=TIMEOUT
            )
            self.running = True
            while self.running:
                command = f"m{self.m}*"
                self.ser.write(command.encode())
                r1 = self.ser.readline().decode(errors='ignore').strip()
                r2 = self.ser.readline().decode(errors='ignore').strip()
                valeurs = r2.split('\t')
                if len(valeurs) >= 8:
                    try:
                        x_imag = int(valeurs[0])
                        y_imag = int(valeurs[1])
                        y_reel = int(valeurs[2])
                        x_reel = int(valeurs[3])
                        z_imag = int(valeurs[4])
                        z_reel = int(valeurs[5])
                        self.data_signal.new_data.emit([
                            x_reel, y_reel, z_reel, x_imag, y_imag, z_imag
                        ])
                    except Exception:
                        pass
                time.sleep(0.1)
        except Exception as e:
            self.data_signal.new_data.emit([None, None, None, None, None, None])
        finally:
            if self.ser:
                try:
                    self.ser.write("S*".encode())
                except Exception:
                    pass
                self.ser.close()

    def stop(self):
        self.running = False

class ElectricFieldGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Acquisition Champ Électrique (PyQtGraph)")
        self.setGeometry(100, 100, 900, 700)
        self.m = self.ask_m_value()
        if self.m is None:
            sys.exit(0)
        self.data_signal = DataSignal()
        self.data_signal.new_data.connect(self.update_data)
        self.acq_thread = None
        self.init_ui()
        self.show()

    def ask_m_value(self):
        m, ok = QInputDialog.getInt(self, "Paramètre m", "Entrez la valeur de m (1-127) :", 10, 1, 127, 1)
        if ok:
            return m
        return None

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        # Graphique valeurs réelles
        self.plot_reel = pg.PlotWidget(title="Valeurs réelles (X, Y, Z)")
        self.plot_reel.setLabel('left', 'Amplitude')
        self.plot_reel.setLabel('bottom', 'Temps')
        self.plot_reel.addLegend()  # Ajouter la légende
        self.curve_x_reel = self.plot_reel.plot(pen=pg.mkPen('b', width=2), name='X réel')
        self.curve_y_reel = self.plot_reel.plot(pen=pg.mkPen('y', width=2), name='Y réel')
        self.curve_z_reel = self.plot_reel.plot(pen=pg.mkPen('r', width=2), name='Z réel')
        layout.addWidget(self.plot_reel)
        # Graphique valeurs imaginaires
        self.plot_imag = pg.PlotWidget(title="Valeurs imaginaires (X, Y, Z)")
        self.plot_imag.setLabel('left', 'Amplitude')
        self.plot_imag.setLabel('bottom', 'Temps')
        self.plot_imag.addLegend()  # Ajouter la légende
        self.curve_x_imag = self.plot_imag.plot(pen=pg.mkPen('b', width=2), name='X imag')
        self.curve_y_imag = self.plot_imag.plot(pen=pg.mkPen('y', width=2), name='Y imag')
        self.curve_z_imag = self.plot_imag.plot(pen=pg.mkPen('r', width=2), name='Z imag')
        layout.addWidget(self.plot_imag)
        # Bouton démarrer/arrêter
        self.btn_start = QPushButton("Démarrer l'acquisition")
        self.btn_start.clicked.connect(self.toggle_acquisition)
        layout.addWidget(self.btn_start)
        
        # Boutons d'offset
        self.btn_offset_electronique = QPushButton("📍 Offset Électronique (excitation OFF)")
        self.btn_offset_electronique.clicked.connect(self.set_offset_electronique)
        layout.addWidget(self.btn_offset_electronique)
        
        self.btn_offset_phase = QPushButton("🔄 Offset Phase (à implémenter)")
        self.btn_offset_phase.clicked.connect(self.set_offset_phase)
        self.btn_offset_phase.setEnabled(False)  # Désactivé pour l'instant
        layout.addWidget(self.btn_offset_phase)
        
        self.btn_offset_excitation = QPushButton("⚡ Offset Excitation (excitation ON)")
        self.btn_offset_excitation.clicked.connect(self.set_offset_excitation)
        layout.addWidget(self.btn_offset_excitation)
        
        # Bouton pour appliquer/désactiver les offsets
        self.btn_apply_offset = QPushButton("Appliquer les offsets")
        self.btn_apply_offset.setCheckable(True)
        self.btn_apply_offset.setChecked(False)
        self.btn_apply_offset.clicked.connect(self.update_data)
        layout.addWidget(self.btn_apply_offset)
        # Buffers de données
        self.x_reel = deque(maxlen=WINDOW_SIZE)
        self.y_reel = deque(maxlen=WINDOW_SIZE)
        self.z_reel = deque(maxlen=WINDOW_SIZE)
        self.x_imag = deque(maxlen=WINDOW_SIZE)
        self.y_imag = deque(maxlen=WINDOW_SIZE)
        self.z_imag = deque(maxlen=WINDOW_SIZE)
        self.running = False
        
        # Variables d'offset
        self.offset_electronique = {'x_reel': 0, 'y_reel': 0, 'z_reel': 0, 
                                   'x_imag': 0, 'y_imag': 0, 'z_imag': 0}
        self.offset_phase = {'x_reel': 0, 'y_reel': 0, 'z_reel': 0, 
                            'x_imag': 0, 'y_imag': 0, 'z_imag': 0}
        self.offset_excitation = {'x_reel': 0, 'y_reel': 0, 'z_reel': 0, 
                                 'x_imag': 0, 'y_imag': 0, 'z_imag': 0}

    def toggle_acquisition(self):
        if not self.running:
            self.acq_thread = AcquisitionThread(self.m, self.data_signal)
            self.acq_thread.start()
            self.btn_start.setText("Arrêter l'acquisition")
            self.running = True
        else:
            if self.acq_thread:
                self.acq_thread.stop()
                self.acq_thread.join()
            self.btn_start.setText("Démarrer l'acquisition")
            self.running = False
    
    def set_offset_electronique(self):
        """Définit l'offset électronique basé sur les valeurs actuelles (excitation OFF)"""
        if len(self.x_reel) > 0:
            # Calculer la moyenne des dernières valeurs comme offset
            self.offset_electronique = {
                'x_reel': np.mean(list(self.x_reel)[-10:]) if len(self.x_reel) >= 10 else np.mean(list(self.x_reel)),
                'y_reel': np.mean(list(self.y_reel)[-10:]) if len(self.y_reel) >= 10 else np.mean(list(self.y_reel)),
                'z_reel': np.mean(list(self.z_reel)[-10:]) if len(self.z_reel) >= 10 else np.mean(list(self.z_reel)),
                'x_imag': np.mean(list(self.x_imag)[-10:]) if len(self.x_imag) >= 10 else np.mean(list(self.x_imag)),
                'y_imag': np.mean(list(self.y_imag)[-10:]) if len(self.y_imag) >= 10 else np.mean(list(self.y_imag)),
                'z_imag': np.mean(list(self.z_imag)[-10:]) if len(self.z_imag) >= 10 else np.mean(list(self.z_imag))
            }
            self.btn_offset_electronique.setText("📍 Offset Électronique (défini)")
            self.btn_offset_electronique.setStyleSheet("background-color: lightgreen")
            QMessageBox.information(self, "Offset Électronique", 
                                  f"Offset électronique défini !\n"
                                  f"X réel: {self.offset_electronique['x_reel']:.1f}\n"
                                  f"Y réel: {self.offset_electronique['y_reel']:.1f}\n"
                                  f"Z réel: {self.offset_electronique['z_reel']:.1f}")
        else:
            QMessageBox.warning(self, "Erreur", "Aucune donnée disponible pour définir l'offset électronique.")
    
    def set_offset_phase(self):
        """Définit l'offset de phase (à implémenter plus tard)"""
        QMessageBox.information(self, "Offset Phase", "Fonctionnalité à implémenter ultérieurement.")
    
    def set_offset_excitation(self):
        """Définit l'offset d'excitation basé sur les valeurs actuelles (excitation ON)"""
        if len(self.x_reel) > 0:
            # Calculer la moyenne des dernières valeurs comme offset
            self.offset_excitation = {
                'x_reel': np.mean(list(self.x_reel)[-10:]) if len(self.x_reel) >= 10 else np.mean(list(self.x_reel)),
                'y_reel': np.mean(list(self.y_reel)[-10:]) if len(self.y_reel) >= 10 else np.mean(list(self.y_reel)),
                'z_reel': np.mean(list(self.z_reel)[-10:]) if len(self.z_reel) >= 10 else np.mean(list(self.z_reel)),
                'x_imag': np.mean(list(self.x_imag)[-10:]) if len(self.x_imag) >= 10 else np.mean(list(self.x_imag)),
                'y_imag': np.mean(list(self.y_imag)[-10:]) if len(self.y_imag) >= 10 else np.mean(list(self.y_imag)),
                'z_imag': np.mean(list(self.z_imag)[-10:]) if len(self.z_imag) >= 10 else np.mean(list(self.z_imag))
            }
            self.btn_offset_excitation.setText("⚡ Offset Excitation (défini)")
            self.btn_offset_excitation.setStyleSheet("background-color: lightblue")
            QMessageBox.information(self, "Offset Excitation", 
                                  f"Offset excitation défini !\n"
                                  f"X réel: {self.offset_excitation['x_reel']:.1f}\n"
                                  f"Y réel: {self.offset_excitation['y_reel']:.1f}\n"
                                  f"Z réel: {self.offset_excitation['z_reel']:.1f}")
        else:
            QMessageBox.warning(self, "Erreur", "Aucune donnée disponible pour définir l'offset excitation.")

    def update_data(self, data=None):
        if data is not None:
            if data[0] is None:
                QMessageBox.warning(self, "Erreur", "Erreur de communication ou port série inaccessible.")
                self.toggle_acquisition()
                return
            x_reel, y_reel, z_reel, x_imag, y_imag, z_imag = data
            self.x_reel.append(x_reel)
            self.y_reel.append(y_reel)
            self.z_reel.append(z_reel)
            self.x_imag.append(x_imag)
            self.y_imag.append(y_imag)
            self.z_imag.append(z_imag)
        # Application des offsets si demandé
        if self.btn_apply_offset.isChecked():
            x_reel = np.array(self.x_reel)
            y_reel = np.array(self.y_reel)
            z_reel = np.array(self.z_reel)
            x_imag = np.array(self.x_imag)
            y_imag = np.array(self.y_imag)
            z_imag = np.array(self.z_imag)
            
            # Application des offsets cumulatifs
            # Offset électronique (bruit de l'électronique)
            x_reel = x_reel - self.offset_electronique['x_reel']
            y_reel = y_reel - self.offset_electronique['y_reel']
            z_reel = z_reel - self.offset_electronique['z_reel']
            x_imag = x_imag - self.offset_electronique['x_imag']
            y_imag = y_imag - self.offset_electronique['y_imag']
            z_imag = z_imag - self.offset_electronique['z_imag']
            
            # Offset de phase (pour plus tard)
            # x_reel = x_reel - self.offset_phase['x_reel']
            # y_reel = y_reel - self.offset_phase['y_reel']
            # z_reel = z_reel - self.offset_phase['z_reel']
            # x_imag = x_imag - self.offset_phase['x_imag']
            # y_imag = y_imag - self.offset_phase['y_imag']
            # z_imag = z_imag - self.offset_phase['z_imag']
            
            # Offset d'excitation
            x_reel = x_reel - self.offset_excitation['x_reel']
            y_reel = y_reel - self.offset_excitation['y_reel']
            z_reel = z_reel - self.offset_excitation['z_reel']
            x_imag = x_imag - self.offset_excitation['x_imag']
            y_imag = y_imag - self.offset_excitation['y_imag']
            z_imag = z_imag - self.offset_excitation['z_imag']
        else:
            x_reel = list(self.x_reel)
            y_reel = list(self.y_reel)
            z_reel = list(self.z_reel)
            x_imag = list(self.x_imag)
            y_imag = list(self.y_imag)
            z_imag = list(self.z_imag)
        x = list(range(len(x_reel)))
        self.curve_x_reel.setData(x, x_reel)
        self.curve_y_reel.setData(x, y_reel)
        self.curve_z_reel.setData(x, z_reel)
        self.curve_x_imag.setData(x, x_imag)
        self.curve_y_imag.setData(x, y_imag)
        self.curve_z_imag.setData(x, z_imag)

    def closeEvent(self, event):
        if self.running and self.acq_thread:
            self.acq_thread.stop()
            self.acq_thread.join()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ElectricFieldGUI()
    sys.exit(app.exec_()) 