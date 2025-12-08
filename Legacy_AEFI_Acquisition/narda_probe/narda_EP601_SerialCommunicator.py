#!/usr/bin/env python3
"""
Script de lecture des mesures de la sonde Narda EP 601
Auteur: Assistant IA
Date: 2025
"""

import serial
import serial.tools.list_ports
import time
import sys
from datetime import datetime

class NardaEP601:
    def __init__(self, port=None, baudrate=9600, timeout=2):
        """
        Initialise la connexion avec la sonde Narda EP 601
        
        Args:
            port: Port COM (ex: 'COM3'). Si None, détection automatique
            baudrate: Vitesse de communication (défaut: 9600)
            timeout: Timeout en secondes
        """
        self.ser = None
        self.connected = False
        
        if port is None:
            port = self.find_narda_port()
        
        if port:
            try:
                self.ser = serial.Serial(port, baudrate, timeout=timeout)
                time.sleep(2)  # Attendre stabilisation
                self.connected = True
                print(f"✓ Connecté au port {port} à {baudrate} bauds")
            except serial.SerialException as e:
                print(f"✗ Erreur de connexion sur {port}: {e}")
                self.connected = False
        else:
            print("✗ Aucun port série trouvé")
    
    def find_narda_port(self):
        """
        Tente de détecter automatiquement le port de la sonde
        """
        print("🔍 Recherche du port série...")
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            print(f"  - {port.device}: {port.description}")
            # Recherche des indices typiques Narda/Prolific
            if any(keyword in port.description.lower() for keyword in 
                   ['prolific', 'usb-serial', 'pl2303', 'narda']):
                print(f"  → Port candidat détecté: {port.device}")
                return port.device
        
        # Si aucun port candidat, prendre le premier disponible
        if ports:
            print(f"  → Utilisation du premier port: {ports[0].device}")
            return ports[0].device
        
        return None
    
    def send_command(self, command, retries=3, binary_response=False):
        """
        Envoie une commande et lit la réponse
        
        Args:
            command: Commande à envoyer
            retries: Nombre de tentatives
            binary_response: Si True, lit en binaire
            
        Returns:
            str/bytes: Réponse de la sonde ou None si erreur
        """
        if not self.connected:
            return None
            
        for attempt in range(retries):
            try:
                # Vider le buffer d'entrée
                self.ser.reset_input_buffer()
                
                # Envoyer la commande (terminaison par * seulement)
                cmd_bytes = command.encode()
                self.ser.write(cmd_bytes)
                print(f"    → Envoi: {command}")
                
                # Attendre un peu pour la réponse
                time.sleep(0.1)
                
                # Lire la réponse
                if binary_response:
                    # Pour les commandes binaires, lire un nombre fixe de bytes
                    response = self.ser.read(20)  # Lire jusqu'à 20 bytes
                else:
                    # Pour les commandes texte, lire jusqu'à ';' ou '*'
                    response = b''
                    timeout_count = 0
                    while timeout_count < 50:  # 5 secondes max
                        char = self.ser.read(1)
                        if char:
                            response += char
                            if char in [b'*', b';']:
                                break
                        else:
                            timeout_count += 1
                            time.sleep(0.1)
                    
                    response = response.decode('utf-8', errors='ignore')
                
                if response:
                    if binary_response:
                        print(f"    ← Réponse binaire: {response.hex()}")
                    else:
                        print(f"    ← Réponse: {response.strip()}")
                    return response
                else:
                    print(f"  Tentative {attempt + 1}: Pas de réponse")
                    time.sleep(0.5)
                    
            except serial.SerialException as e:
                print(f"  Erreur série (tentative {attempt + 1}): {e}")
                time.sleep(1)
        
        return None
    
    def test_communication(self):
        """
        Teste la communication avec différentes commandes
        """
        print("\n🔧 Test de communication...")
        
        # Tests de base avec différentes configurations
        basic_tests = [
            ('*IDN?', 'Test SCPI standard'),
            ('#00?v*', 'Version Narda'),  
            ('#00?p*', 'Date calibration'),
            ('#00?s*', 'Numéro série'),
        ]
        
        print("  Tests commandes texte:")
        for cmd, description in basic_tests:
            print(f"    {description}: ", end='')
            response = self.send_command(cmd)
            if response:
                print(f"✓ {response}")
                return True  # Au moins une commande fonctionne
            else:
                print("✗")
        
        # Tests commandes binaires
        print("  Tests commandes binaires:")
        binary_tests = [
            ('#00?b*', 'État batterie (binaire)'),
            ('#00?t*', 'Température (binaire)'),
            ('#00?T*', 'Mesure totale (binaire)'),
        ]
        
        for cmd, description in binary_tests:
            print(f"    {description}: ", end='')
            response = self.send_command(cmd, binary_response=True)
            if response and len(response) > 0:
                print(f"✓ {len(response)} bytes reçus")
                return True
            else:
                print("✗")
        
        # Test avec autres vitesses si rien ne fonctionne
        print("  Test avec autres vitesses...")
        other_bauds = [19200, 38400, 115200, 4800, 2400]
        
        for baud in other_bauds:
            print(f"    Test à {baud} bauds: ", end='')
            try:
                self.ser.baudrate = baud
                time.sleep(0.5)
                response = self.send_command('#00?v*')
                if response:
                    print(f"✓ Communication établie à {baud} bauds!")
                    return True
                else:
                    print("✗")
            except:
                print("✗ Erreur")
        
        # Remettre la vitesse originale
        self.ser.baudrate = 9600
        return False
    
    def get_measurement(self):
        """
        Obtient une mesure de champ électrique
        Utilise la commande #00?T* pour mesure totale (format IEEE float)
        
        Returns:
            dict: Dictionnaire avec les valeurs de mesure
        """
        # Essayer d'abord la mesure totale (format binaire)
        response = self.send_command('#00?T*', binary_response=True)
        if response and len(response) >= 5:
            try:
                # Décoder IEEE float Little Endian (5 bytes: 'T' + 4 bytes float)
                import struct
                if response[0:1] == b'T':
                    float_bytes = response[1:5]
                    total_field = struct.unpack('<f', float_bytes)[0]  # Little Endian
                    return {
                        'total': total_field,
                        'unit': 'V/m',
                        'timestamp': datetime.now(),
                        'type': 'total'
                    }
            except struct.error as e:
                print(f"Erreur décodage mesure totale: {e}")
        
        # Essayer la mesure par axes (format binaire)
        response = self.send_command('#00?A*', binary_response=True)
        if response and len(response) >= 13:
            try:
                import struct
                if response[0:1] == b'A':
                    # Décoder 3 floats IEEE (X, Y, Z)
                    x_bytes = response[1:5]
                    y_bytes = response[5:9] 
                    z_bytes = response[9:13]
                    
                    x_field = struct.unpack('<f', x_bytes)[0]
                    y_field = struct.unpack('<f', y_bytes)[0] 
                    z_field = struct.unpack('<f', z_bytes)[0]
                    
                    # Calculer le total
                    total = (x_field**2 + y_field**2 + z_field**2)**0.5
                    
                    return {
                        'x': x_field,
                        'y': y_field,
                        'z': z_field,
                        'total': total,
                        'unit': 'V/m',
                        'timestamp': datetime.now(),
                        'type': 'xyz'
                    }
            except struct.error as e:
                print(f"Erreur décodage mesure axes: {e}")
        
        # Si les commandes binaires échouent, essayer des commandes texte
        for cmd in ['#00?m*', '#00MEAS?*', 'MEAS?']:
            response = self.send_command(cmd)
            if response:
                return self.parse_measurement(response)
        
        return None
    
    def parse_measurement(self, response):
        """
        Parse la réponse de mesure
        Le format exact peut varier selon le firmware
        """
        try:
            # Exemple de parsing - à adapter selon le format réel
            # Format possible: "X:1.23,Y:4.56,Z:7.89,T:9.87,V/m"
            result = {
                'raw': response,
                'timestamp': datetime.now(),
                'x': None, 'y': None, 'z': None, 'total': None,
                'unit': 'V/m'
            }
            
            # Tentative de parsing de différents formats
            if ',' in response:
                parts = response.split(',')
                if len(parts) >= 4:
                    try:
                        result['x'] = float(parts[0])
                        result['y'] = float(parts[1])
                        result['z'] = float(parts[2])
                        result['total'] = float(parts[3])
                    except ValueError:
                        pass
            
            return result
            
        except Exception as e:
            print(f"Erreur parsing: {e}")
            return {'raw': response, 'timestamp': datetime.now(), 'error': str(e)}
    
    def get_info(self):
        """
        Récupère les informations de la sonde
        """
        info = {}
        
        version = self.send_command('#00?v*')
        if version:
            info['version'] = version
            
    def get_battery_info(self):
        """
        Récupère l'état de la batterie (format binaire)
        Retourne 3 bytes en Big Endian selon la doc
        """
        response = self.send_command('#00?b*', binary_response=True)
        if response and len(response) >= 3:
            try:
                import struct
                if response[0:1] == b'b':
                    # 2 bytes suivants en Big Endian
                    battery_raw = struct.unpack('>H', response[1:3])[0]  # Big Endian unsigned short
                    # Formule de la doc: V_battery = 3 * (nn / 1024 * 1.6)
                    battery_voltage = 3 * (battery_raw / 1024 * 1.6)
                    return {
                        'voltage': battery_voltage,
                        'raw': battery_raw,
                        'status': 'OK' if battery_voltage > 2.11 else 'LOW'
                    }
            except struct.error as e:
                print(f"Erreur décodage batterie: {e}")
        
        return None
            
        calib = self.send_command('#00?p*')
        if calib:
            info['calibration'] = calib
            
        freq = self.send_command('#00?f*')
        if freq:
            info['frequency'] = freq
            
        return info
    
    def monitor_continuous(self, interval=1.0, duration=None):
        """
        Monitoring continu des mesures
        
        Args:
            interval: Intervalle entre les mesures (secondes)
            duration: Durée totale (secondes). Si None, infini
        """
        print(f"\n📊 Démarrage du monitoring (Ctrl+C pour arrêter)")
        print(f"   Intervalle: {interval}s")
        if duration:
            print(f"   Durée: {duration}s")
        
        print("\n" + "="*80)
        print(f"{'Heure':<12} {'X (V/m)':<12} {'Y (V/m)':<12} {'Z (V/m)':<12} {'Total (V/m)':<15} {'Brut'}")
        print("="*80)
        
        start_time = time.time()
        measurement_count = 0
        
        try:
            while True:
                if duration and (time.time() - start_time) > duration:
                    break
                
                measurement = self.get_measurement()
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                if measurement:
                    x = measurement.get('x', 'N/A')
                    y = measurement.get('y', 'N/A')
                    z = measurement.get('z', 'N/A')
                    total = measurement.get('total', 'N/A')
                    raw = measurement.get('raw', '')
                    
                    print(f"{timestamp:<12} {str(x):<12} {str(y):<12} {str(z):<12} {str(total):<15} {raw}")
                    measurement_count += 1
                else:
                    print(f"{timestamp:<12} {'ERREUR':<12} {'COMM':<12} {'':<12} {'':<15} {''}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n\n⏹️  Monitoring arrêté par l'utilisateur")
            print(f"   {measurement_count} mesures effectuées")
    
    def close(self):
        """
        Ferme la connexion série
        """
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("🔌 Connexion fermée")

def main():
    """
    Fonction principale
    """
    print("🌐 Narda EP 601 - Lecteur de mesures de champ électrique")
    print("=" * 60)
    
    # Initialisation
    narda = NardaEP601()
    
    if not narda.connected:
        print("\n❌ Impossible de se connecter à la sonde")
        print("Vérifiez:")
        print("  - La sonde est allumée")
        print("  - Le convertisseur 8053-OC est connecté")
        print("  - Le port COM dans le gestionnaire de périphériques")
        print("  - Que ProbesManager est fermé")
        return
    
    try:
        # Test de communication
        if not narda.test_communication():
            print("\n❌ Aucune communication établie")
            print("Causes possibles:")
            print("  - Mauvais port série")
            print("  - Vitesse de communication incorrecte")
            print("  - Protocole différent")
            return
        
        # Affichage des informations
        print("\n📋 Informations de la sonde:")
        info = narda.get_info()
        if info:
            for key, value in info.items():
                print(f"  {key.capitalize()}: {value}")
        else:
            print("  Erreur récupération des informations")
        
        # Mesure unique
        print("\n🔬 Mesure unique:")
        measurement = narda.get_measurement()
        if measurement:
            print(f"  Résultat: {measurement}")
        
        # Proposer le monitoring continu
        response = input("\n▶️  Lancer le monitoring continu? (o/N): ")
        if response.lower() in ['o', 'oui', 'y', 'yes']:
            try:
                interval = float(input("  Intervalle entre mesures (secondes) [1.0]: ") or "1.0")
            except ValueError:
                interval = 1.0
            
            narda.monitor_continuous(interval=interval)
    
    finally:
        narda.close()

if __name__ == "__main__":
    main()