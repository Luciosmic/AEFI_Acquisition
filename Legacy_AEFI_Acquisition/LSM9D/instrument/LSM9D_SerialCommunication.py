import serial
import time
import threading
from datetime import datetime
from collections import deque
import queue

class LSM9D_SerialCommunicator:
    """Backend pour la gestion du capteur LSM9D - Interface graphique"""
    
    def __init__(self, port='COM5', baudrate=256000, max_data_points=1000):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.is_connected = False
        self.is_streaming = False
        self.max_data_points = max_data_points
        
        # Buffers de données pour chaque capteur (thread-safe)
        self.data_lock = threading.Lock()
        self.magnetometer_data = deque(maxlen=max_data_points)
        self.accelerometer_data = deque(maxlen=max_data_points)
        self.gyroscope_data = deque(maxlen=max_data_points)
        self.lidar_data = deque(maxlen=max_data_points)
        self.timestamps = deque(maxlen=max_data_points)
        
        # État actuel des capteurs
        self.current_mag = {'x': 0, 'y': 0, 'z': 0}
        self.current_acc = {'x': 0, 'y': 0, 'z': 0}
        self.current_gyr = {'x': 0, 'y': 0, 'z': 0}
        self.current_lidar = 0
        
        # Thread de lecture
        self.read_thread = None
        self.stop_reading = threading.Event()
        
        # Mode de capteur actuel
        self.current_mode = None
        self.sensor_modes = {
            'MAG_ONLY': ['S', 'M9', 'F25'],
            'ACC_GYR': ['S', 'A9', 'G9', 'F25'],
            'MAG_ACC_GYR': ['S', 'A9', 'G9', 'M9', 'F15'],
            'ALL_SENSORS': ['S', 'A9', 'G9', 'M9', 'L9', 'F20']
        }
        
        # Callbacks pour notifier l'interface
        self.data_callbacks = []
        self.status_callbacks = []
    
    def add_data_callback(self, callback):
        """Ajoute un callback appelé à chaque nouvelle donnée"""
        self.data_callbacks.append(callback)
    
    def add_status_callback(self, callback):
        """Ajoute un callback appelé lors des changements d'état"""
        self.status_callbacks.append(callback)
    
    def notify_data_callbacks(self):
        """Notifie tous les callbacks de données"""
        for callback in self.data_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Erreur callback données: {e}")
    
    def notify_status_callbacks(self, status, message=""):
        """Notifie tous les callbacks de statut"""
        for callback in self.status_callbacks:
            try:
                callback(status, message)
            except Exception as e:
                print(f"Erreur callback statut: {e}")
    
    def connect(self):
        print("[DEBUG] Communicateur.connect() appelé")
        try:
            if self.ser and self.ser.is_open:
                print("[DEBUG] Port déjà ouvert, fermeture...")
                self.ser.close()
            print(f"[DEBUG] Tentative d'ouverture du port {self.port} à {self.baudrate} bauds")
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            self.ser.flushInput()
            self.ser.flushOutput()
            time.sleep(0.5)
            self.is_connected = True
            print("[DEBUG] Connexion série réussie")
            self.notify_status_callbacks("connected", f"Connecté sur {self.port}")
            return True
        except serial.SerialException as e:
            self.is_connected = False
            print(f"[DEBUG] Erreur connexion série: {e}")
            self.notify_status_callbacks("error", f"Erreur connexion: {e}")
            return False
        except Exception as e:
            self.is_connected = False
            print(f"[DEBUG] Exception inattendue: {e}")
            self.notify_status_callbacks("error", f"Erreur connexion inattendue: {e}")
            return False
    
    def disconnect(self):
        """Ferme la connexion série"""
        self.stop_streaming()
        
        if self.ser and self.ser.is_open:
            self.ser.close()
            
        self.is_connected = False
        self.current_mode = None
        self.notify_status_callbacks("disconnected", "Déconnecté")
    
    def send_command(self, command):
        """Envoie une commande au capteur"""
        if not self.is_connected or not self.ser:
            return False
            
        try:
            if not command.endswith('*'):
                command += '*'
            self.ser.write(command.encode())
            return True
        except Exception as e:
            self.notify_status_callbacks("error", f"Erreur envoi commande: {e}")
            return False
    
    def read_response(self):
        """Lit une réponse du capteur"""
        if not self.is_connected or not self.ser:
            return ""
            
        try:
            response = self.ser.readline().decode().strip()
            return response
        except Exception as e:
            return ""
    
    def initialize_sensor_mode(self, mode):
        """Initialise le capteur dans un mode spécifique"""
        if mode not in self.sensor_modes:
            self.notify_status_callbacks("error", f"Mode inconnu: {mode}")
            return False
            
        if not self.is_connected:
            self.notify_status_callbacks("error", "Pas de connexion")
            return False
        
        # Arrêter le streaming actuel
        self.stop_streaming()
        time.sleep(0.5)
        
        # Exécuter la séquence d'initialisation
        commands = self.sensor_modes[mode]
        self.notify_status_callbacks("initializing", f"Initialisation mode {mode}...")
        
        for i, cmd in enumerate(commands[:-1]):  # Tous sauf le dernier
            if not self.send_command(cmd):
                self.notify_status_callbacks("error", f"Échec commande {cmd}")
                return False
            time.sleep(0.1)
            response = self.read_response()
            print(f"Init {cmd}: {response}")
        
        # La dernière commande démarre le streaming
        final_cmd = commands[-1]
        if not self.send_command(final_cmd):
            self.notify_status_callbacks("error", f"Échec commande finale {final_cmd}")
            return False
        
        self.current_mode = mode
        self.notify_status_callbacks("initialized", f"Mode {mode} initialisé")
        return True
    
    def start_streaming(self):
        """Démarre la lecture continue des données"""
        if not self.is_connected or not self.current_mode:
            self.notify_status_callbacks("error", "Capteur non initialisé")
            return False
        
        if self.is_streaming:
            return True
        
        # Démarrer le thread de lecture
        self.stop_reading.clear()
        self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.read_thread.start()
        
        self.is_streaming = True
        self.notify_status_callbacks("streaming", f"Streaming {self.current_mode} démarré")
        return True
    
    def stop_streaming(self):
        """Arrête la lecture continue"""
        if not self.is_streaming:
            return
        
        self.stop_reading.set()
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=2)
        
        self.is_streaming = False
        self.notify_status_callbacks("stopped", "Streaming arrêté")
    
    def _read_loop(self):
        """Boucle de lecture dans un thread séparé"""
        while not self.stop_reading.is_set():
            try:
                if self.ser and self.ser.in_waiting > 0:
                    response = self.read_response()
                    if response:
                        self._parse_and_store_data(response)
                
                time.sleep(0.01)  # 100Hz max
                
            except Exception as e:
                print(f"Erreur lecture: {e}")
                time.sleep(0.1)
    
    def _parse_and_store_data(self, response):
        """Parse et stocke les données reçues"""
        try:
            values = response.split()
            if not values:
                return
            
            # Convertir en nombres
            num_values = [float(v) for v in values]
            timestamp = time.time()
            
            with self.data_lock:
                self.timestamps.append(timestamp)
                
                # Parser selon le mode actuel
                if self.current_mode == 'MAG_ONLY' and len(num_values) >= 3:
                    # Magnétomètre seul [Mx, My, Mz]
                    self.current_mag = {'x': num_values[0], 'y': num_values[1], 'z': num_values[2]}
                    self.magnetometer_data.append(self.current_mag.copy())
                    
                elif self.current_mode == 'ACC_GYR' and len(num_values) >= 6:
                    # Accéléromètre + Gyroscope [Ax, Ay, Az, Gx, Gy, Gz]
                    self.current_acc = {'x': num_values[0], 'y': num_values[1], 'z': num_values[2]}
                    self.current_gyr = {'x': num_values[3], 'y': num_values[4], 'z': num_values[5]}
                    self.accelerometer_data.append(self.current_acc.copy())
                    self.gyroscope_data.append(self.current_gyr.copy())
                    
                elif self.current_mode == 'MAG_ACC_GYR' and len(num_values) >= 9:
                    # Tous [Mx, My, Mz, Ax, Ay, Az, Gx, Gy, Gz]
                    self.current_mag = {'x': num_values[0], 'y': num_values[1], 'z': num_values[2]}
                    self.current_acc = {'x': num_values[3], 'y': num_values[4], 'z': num_values[5]}
                    self.current_gyr = {'x': num_values[6], 'y': num_values[7], 'z': num_values[8]}
                    self.magnetometer_data.append(self.current_mag.copy())
                    self.accelerometer_data.append(self.current_acc.copy())
                    self.gyroscope_data.append(self.current_gyr.copy())
                    
                elif self.current_mode == 'ALL_SENSORS' and len(num_values) >= 10:
                    # Tous + LIDAR [Mx, My, Mz, Ax, Ay, Az, Gx, Gy, Gz, L]
                    self.current_mag = {'x': num_values[0], 'y': num_values[1], 'z': num_values[2]}
                    self.current_acc = {'x': num_values[3], 'y': num_values[4], 'z': num_values[5]}
                    self.current_gyr = {'x': num_values[6], 'y': num_values[7], 'z': num_values[8]}
                    self.current_lidar = num_values[9]
                    self.magnetometer_data.append(self.current_mag.copy())
                    self.accelerometer_data.append(self.current_acc.copy())
                    self.gyroscope_data.append(self.current_gyr.copy())
                    self.lidar_data.append(self.current_lidar)
            
            # Notifier les callbacks
            self.notify_data_callbacks()
            
        except Exception as e:
            print(f"Erreur parsing données: {e}")
    
    def get_current_data(self):
        """Retourne les données actuelles de tous les capteurs"""
        with self.data_lock:
            return {
                'magnetometer': self.current_mag.copy(),
                'accelerometer': self.current_acc.copy(),
                'gyroscope': self.current_gyr.copy(),
                'lidar': self.current_lidar,
                'timestamp': time.time()
            }
    
    def get_historical_data(self, sensor=None, max_points=None):
        """Retourne les données historiques d'un capteur"""
        with self.data_lock:
            if max_points is None:
                max_points = len(self.timestamps)
            
            if sensor == 'magnetometer':
                return list(self.magnetometer_data)[-max_points:]
            elif sensor == 'accelerometer':
                return list(self.accelerometer_data)[-max_points:]
            elif sensor == 'gyroscope':
                return list(self.gyroscope_data)[-max_points:]
            elif sensor == 'lidar':
                return list(self.lidar_data)[-max_points:]
            elif sensor == 'timestamps':
                return list(self.timestamps)[-max_points:]
            else:
                return {
                    'magnetometer': list(self.magnetometer_data)[-max_points:],
                    'accelerometer': list(self.accelerometer_data)[-max_points:],
                    'gyroscope': list(self.gyroscope_data)[-max_points:],
                    'lidar': list(self.lidar_data)[-max_points:],
                    'timestamps': list(self.timestamps)[-max_points:]
                }
    
    def clear_data(self):
        """Efface toutes les données stockées"""
        with self.data_lock:
            self.magnetometer_data.clear()
            self.accelerometer_data.clear()
            self.gyroscope_data.clear()
            self.lidar_data.clear()
            self.timestamps.clear()
    
    def get_status(self):
        """Retourne l'état actuel du backend"""
        return {
            'connected': self.is_connected,
            'streaming': self.is_streaming,
            'mode': self.current_mode,
            'port': self.port,
            'data_points': len(self.timestamps)
        } 