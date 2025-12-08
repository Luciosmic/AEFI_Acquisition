MOC :
Source : [[Luis Saluden]]
Projets : [[PROJET ASSOCE]] [[PROJET Banc de Test Python]]
Simulation :
Tags : #NoteAtomique
Date : 2025-06-10
***

# LSM9D - Capteur Multi-Axes avec Interface Backend

## 📋 Vue d'Ensemble

Le **LSM9D** est un capteur multifonctionnel combinant plusieurs technologies de mesure dans un seul dispositif :
- **🧲 Magnétomètre 3 axes** (X, Y, Z) - Mesure du champ magnétique
- **📐 Accéléromètre 3 axes** (X, Y, Z) - Mesure de l'accélération
- **🌀 Gyroscope 3 axes** (X, Y, Z) - Mesure de la vitesse angulaire
- **📏 LIDAR** - Mesure de distance

## 🏗️ Architecture du Système

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Application   │◄──►│  LSM9D_Backend   │◄──►│   Capteur LSM9D │
│   Utilisateur   │    │                  │    │   (Série COM)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                       │
         │                       ▼
    ┌─────────┐            ┌──────────┐
    │Callbacks│            │  Thread  │
    │         │            │ Lecture  │
    └─────────┘            └──────────┘
```

## ⚙️ Modes de Fonctionnement

Le capteur LSM9D propose **4 modes prédéfinis** optimisés pour différents usages :

### 1. **MAG_ONLY** 🧲
- **Capteurs actifs** : Magnétomètre uniquement
- **Fréquence** : 25 Hz
- **Utilisation** : Détection de champ magnétique, boussole
- **Données** : [Mx, My, Mz]

### 2. **ACC_GYR** 📐🌀
- **Capteurs actifs** : Accéléromètre + Gyroscope
- **Fréquence** : 25 Hz
- **Utilisation** : Analyse de mouvement, IMU basique
- **Données** : [Ax, Ay, Az, Gx, Gy, Gz]

### 3. **MAG_ACC_GYR** 🧲📐🌀
- **Capteurs actifs** : Magnétomètre + Accéléromètre + Gyroscope
- **Fréquence** : 15 Hz
- **Utilisation** : IMU complète, navigation
- **Données** : [Mx, My, Mz, Ax, Ay, Az, Gx, Gy, Gz]

### 4. **ALL_SENSORS** 🧲📐🌀📏
- **Capteurs actifs** : Tous (avec LIDAR)
- **Fréquence** : 20 Hz
- **Utilisation** : Applications complètes, robotique
- **Données** : [Mx, My, Mz, Ax, Ay, Az, Gx, Gy, Gz, Distance]

## 🔧 Installation et Configuration

### Prérequis
```bash
pip install pyserial
```

### Configuration Matérielle
- **Port série** : COM5 (par défaut, configurable)
- **Vitesse** : 256000 bauds
- **Format** : 8 bits, 1 stop bit, pas de parité

## 📚 Documentation de la Classe LSM9D_Backend

### Initialisation

```python
from LSM9D_Backend import LSM9D_Backend

# Initialisation avec paramètres par défaut
backend = LSM9D_Backend()

# Initialisation avec paramètres personnalisés
backend = LSM9D_Backend(
    port='COM3',           # Port série
    baudrate=256000,       # Vitesse de communication
    max_data_points=5000   # Taille du buffer de données
)
```

### Méthodes Principales

#### Connexion et Communication

```python
# Connexion au capteur
success = backend.connect()
if success:
    print("Capteur connecté avec succès")

# Déconnexion
backend.disconnect()

# Vérifier l'état
status = backend.get_status()
print(f"Connecté: {status['connected']}")
print(f"Mode actuel: {status['mode']}")
```

#### Configuration et Contrôle

```python
# Initialiser un mode spécifique
backend.initialize_sensor_mode('ALL_SENSORS')

# Démarrer l'acquisition de données
backend.start_streaming()

# Arrêter l'acquisition
backend.stop_streaming()

# Effacer les données stockées
backend.clear_data()
```

#### Accès aux Données

```python
# Données actuelles
current_data = backend.get_current_data()
print(f"Magnétomètre: {current_data['magnetometer']}")
print(f"Accéléromètre: {current_data['accelerometer']}")
print(f"Gyroscope: {current_data['gyroscope']}")
print(f"LIDAR: {current_data['lidar']}")

# Données historiques
mag_history = backend.get_historical_data('magnetometer', max_points=100)
all_history = backend.get_historical_data()  # Toutes les données
timestamps = backend.get_historical_data('timestamps')
```

### Système de Callbacks

Le backend utilise un système de callbacks pour notifier les applications des changements d'état et nouvelles données.

#### Callbacks de Données
```python
def on_new_data():
    """Appelé à chaque nouvelle donnée reçue"""
    data = backend.get_current_data()
    print(f"Nouvelle donnée reçue: {data['timestamp']}")

# Enregistrer le callback
backend.add_data_callback(on_new_data)
```

#### Callbacks de Statut
```python
def on_status_change(status, message):
    """Appelé lors des changements d'état"""
    print(f"Statut: {status} - {message}")

# Enregistrer le callback
backend.add_status_callback(on_status_change)
```

## 🚀 Exemples d'Utilisation

### Exemple 1 : Application Simple

```python
#!/usr/bin/env python3
from LSM9D_Backend import LSM9D_Backend
import time

def main():
    # Créer le backend
    backend = LSM9D_Backend(port='COM5')
    
    # Callback pour afficher les nouvelles données
    def display_data():
        data = backend.get_current_data()
        mag = data['magnetometer']
        print(f"Magnétomètre - X: {mag['x']:.2f}, Y: {mag['y']:.2f}, Z: {mag['z']:.2f}")
    
    # Enregistrer le callback
    backend.add_data_callback(display_data)
    
    try:
        # Connexion et initialisation
        if backend.connect():
            print("✅ Capteur connecté")
            
            if backend.initialize_sensor_mode('MAG_ONLY'):
                print("✅ Mode MAG_ONLY initialisé")
                
                if backend.start_streaming():
                    print("✅ Streaming démarré")
                    
                    # Acquisition pendant 10 secondes
                    time.sleep(10)
                    
                    # Arrêter et récupérer les données
                    backend.stop_streaming()
                    
                    # Analyser les données collectées
                    mag_data = backend.get_historical_data('magnetometer')
                    print(f"📊 {len(mag_data)} points collectés")
    
    except KeyboardInterrupt:
        print("Arrêt demandé par l'utilisateur")
    
    finally:
        backend.disconnect()
        print("🔌 Capteur déconnecté")

if __name__ == "__main__":
    main()
```

### Exemple 2 : Application avec Interface Graphique

```python
#!/usr/bin/env python3
from LSM9D_Backend import LSM9D_Backend
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
import sys

class SensorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.backend = LSM9D_Backend()
        self.init_ui()
        self.setup_backend()
    
    def init_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        self.mag_label = QLabel("Magnétomètre: --")
        self.acc_label = QLabel("Accéléromètre: --")
        self.gyr_label = QLabel("Gyroscope: --")
        
        layout.addWidget(self.mag_label)
        layout.addWidget(self.acc_label)
        layout.addWidget(self.gyr_label)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Timer pour mise à jour régulière
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(100)  # 10 Hz
    
    def setup_backend(self):
        # Callbacks
        self.backend.add_data_callback(self.on_new_data)
        self.backend.add_status_callback(self.on_status_change)
        
        # Connexion et démarrage
        if self.backend.connect():
            self.backend.initialize_sensor_mode('MAG_ACC_GYR')
            self.backend.start_streaming()
    
    def on_new_data(self):
        # Les données seront mises à jour par le timer
        pass
    
    def on_status_change(self, status, message):
        print(f"Statut capteur: {status} - {message}")
    
    def update_display(self):
        data = self.backend.get_current_data()
        
        mag = data['magnetometer']
        acc = data['accelerometer']
        gyr = data['gyroscope']
        
        self.mag_label.setText(f"🧲 Mag: X={mag['x']:.1f}, Y={mag['y']:.1f}, Z={mag['z']:.1f}")
        self.acc_label.setText(f"📐 Acc: X={acc['x']:.1f}, Y={acc['y']:.1f}, Z={acc['z']:.1f}")
        self.gyr_label.setText(f"🌀 Gyr: X={gyr['x']:.1f}, Y={gyr['y']:.1f}, Z={gyr['z']:.1f}")
    
    def closeEvent(self, event):
        self.backend.disconnect()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = SensorGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
```

### Exemple 3 : Logging de Données

```python
#!/usr/bin/env python3
from LSM9D_Backend import LSM9D_Backend
import csv
import datetime
import time

class DataLogger:
    def __init__(self, filename=None):
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lsm9d_data_{timestamp}.csv"
        
        self.filename = filename
        self.backend = LSM9D_Backend()
        self.file_handle = None
        self.csv_writer = None
        
        # Configurer les callbacks
        self.backend.add_data_callback(self.log_data)
        self.backend.add_status_callback(self.log_status)
    
    def start_logging(self, mode='ALL_SENSORS', duration=60):
        """Démarre l'enregistrement pour une durée donnée (en secondes)"""
        print(f"📝 Démarrage du logging vers {self.filename}")
        
        # Ouvrir le fichier CSV
        self.file_handle = open(self.filename, 'w', newline='')
        
        if mode == 'ALL_SENSORS':
            fieldnames = ['timestamp', 'mag_x', 'mag_y', 'mag_z', 
                         'acc_x', 'acc_y', 'acc_z', 
                         'gyr_x', 'gyr_y', 'gyr_z', 'lidar']
        else:
            fieldnames = ['timestamp', 'mag_x', 'mag_y', 'mag_z', 
                         'acc_x', 'acc_y', 'acc_z', 
                         'gyr_x', 'gyr_y', 'gyr_z']
        
        self.csv_writer = csv.DictWriter(self.file_handle, fieldnames=fieldnames)
        self.csv_writer.writeheader()
        
        try:
            # Connexion et configuration
            if self.backend.connect():
                print("✅ Capteur connecté")
                
                if self.backend.initialize_sensor_mode(mode):
                    print(f"✅ Mode {mode} initialisé")
                    
                    if self.backend.start_streaming():
                        print(f"✅ Streaming démarré pour {duration}s")
                        
                        # Attendre la durée spécifiée
                        time.sleep(duration)
                        
                        # Arrêter
                        self.backend.stop_streaming()
                        print("⏹️ Streaming arrêté")
                        
                        # Statistiques
                        total_points = len(self.backend.get_historical_data('timestamps'))
                        print(f"📊 {total_points} points enregistrés")
        
        except KeyboardInterrupt:
            print("Arrêt demandé par l'utilisateur")
        
        finally:
            self.backend.disconnect()
            if self.file_handle:
                self.file_handle.close()
            print(f"💾 Données sauvegardées dans {self.filename}")
    
    def log_data(self):
        """Callback appelé à chaque nouvelle donnée"""
        if self.csv_writer:
            data = self.backend.get_current_data()
            
            row = {
                'timestamp': data['timestamp'],
                'mag_x': data['magnetometer']['x'],
                'mag_y': data['magnetometer']['y'],
                'mag_z': data['magnetometer']['z'],
                'acc_x': data['accelerometer']['x'],
                'acc_y': data['accelerometer']['y'],
                'acc_z': data['accelerometer']['z'],
                'gyr_x': data['gyroscope']['x'],
                'gyr_y': data['gyroscope']['y'],
                'gyr_z': data['gyroscope']['z']
            }
            
            # Ajouter LIDAR si disponible
            if data['lidar'] != 0:
                row['lidar'] = data['lidar']
            
            self.csv_writer.writerow(row)
    
    def log_status(self, status, message):
        """Callback pour les changements de statut"""
        print(f"📡 {status}: {message}")

# Utilisation
if __name__ == "__main__":
    logger = DataLogger()
    logger.start_logging(mode='ALL_SENSORS', duration=30)  # 30 secondes
```

## 🔍 Gestion d'Erreurs et Débogage

### Vérification de l'État
```python
status = backend.get_status()
print(f"Connecté: {status['connected']}")
print(f"En streaming: {status['streaming']}")
print(f"Mode actuel: {status['mode']}")
print(f"Port: {status['port']}")
print(f"Points de données: {status['data_points']}")
```

### Gestion des Erreurs Communes
```python
# Vérifier la connexion avant utilisation
if not backend.is_connected:
    print("❌ Capteur non connecté")
    return

# Vérifier que le mode est initialisé
if backend.current_mode is None:
    print("❌ Aucun mode initialisé")
    return

# Gestion des erreurs de port série
try:
    backend.connect()
except Exception as e:
    print(f"❌ Erreur de connexion: {e}")
```

## 📈 Performance et Optimisation

### Recommandations
- **Fréquence d'acquisition** : Respecter les limites des modes (15-25 Hz)
- **Taille du buffer** : Ajuster `max_data_points` selon la mémoire disponible
- **Thread safety** : La classe est thread-safe, pas besoin de verrous externes
- **Callbacks** : Éviter les traitements lourds dans les callbacks

### Monitoring
```python
# Surveiller la performance
import time

start_time = time.time()
initial_count = len(backend.get_historical_data('timestamps'))

time.sleep(5)  # Attendre 5 secondes

final_count = len(backend.get_historical_data('timestamps'))
actual_rate = (final_count - initial_count) / 5

print(f"Fréquence réelle: {actual_rate:.1f} Hz")
```

## 🛠️ Intégration dans d'Autres Applications

La classe `LSM9D_Backend` est conçue pour être facilement intégrée dans d'autres projets :

1. **Interface graphique** : Utilisation des callbacks pour mise à jour temps réel
2. **Acquisition de données** : Buffers thread-safe pour collecte continue
3. **Traitement de signal** : Accès aux données brutes et filtrées
4. **Applications robotiques** : IMU complète avec LIDAR
5. **Recherche scientifique** : Logging et analyse de données

## 📄 Licence et Support

Ce code est fourni pour usage éducatif et recherche. Pour toute question ou amélioration, consulter la documentation technique du capteur LSM9D.

---

**Développé pour l'interface graphique moderne du capteur LSM9D** 🎛️ 