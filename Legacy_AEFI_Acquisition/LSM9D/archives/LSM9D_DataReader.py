import serial
import time
import sys
import struct
import csv
from datetime import datetime

class LSM9D_DataReader:
    def __init__(self, port='COM5', baudrate=256000):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.data_buffer = []
        
        # Configuration des données selon le fichier d'informations
        self.data_config = {
            'M': [-4, -3, 5],    # Magnétomètre [X, Y, Z] --> colonnes 4,5,6 (avec signe inversé pour X,Y)
            'A': [-7, -6, 8],    # Accéléromètre [X, Y, Z] --> colonnes 7,8,9 (avec signe inversé pour X,Y)
            'G': [-10, -9, 11],  # Gyroscope [X, Y, Z] --> colonnes 10,11,12 (avec signe inversé pour X,Y)
            'L': 12,             # LIDAR --> colonne 12
            't': 13,             # Temps --> colonne 13
            's': 14              # État de scan --> colonne 14
        }
        
        # Protocole de communication séquentiel
        self.command_sequence = [
            ('S', 100),    # Commande de start, attente 100ms
            ('A9', 50),    # Lecture accéléromètre, attente 50ms
            ('G9', 50),    # Lecture gyroscope, attente 50ms
            ('M9', 50),    # Lecture magnétomètre, attente 50ms
            ('L9', 50),    # Lecture LIDAR, attente 50ms
            ('F20', 50)    # Commande finale, attente 50ms
        ]
        
    def connect(self):
        """Établit la connexion série"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=2  # Timeout plus long pour les réponses
            )
            print(f"✓ Connexion établie sur {self.port} à {self.baudrate} bauds")
            print(f"✓ Port ouvert: {self.ser.is_open}")
            
            # Vider les buffers
            self.ser.flushInput()
            self.ser.flushOutput()
            time.sleep(0.5)  # Attendre la stabilisation
            
            return True
            
        except serial.SerialException as e:
            print(f"❌ Erreur de connexion série: {e}")
            return False
    
    def disconnect(self):
        """Ferme la connexion série"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"✓ Port {self.port} fermé")
    
    def send_command(self, command):
        """Envoie une commande au capteur (basé sur l'exemple fonctionnel)"""
        try:
            # Ajouter terminaison '*' si nécessaire
            if not command.endswith('*'):
                command += '*'
            
            # Envoi de la commande comme dans l'exemple fonctionnel
            self.ser.write(command.encode())
            print(f"📤 Commande envoyée: '{command}'")
            return True
            
        except Exception as e:
            print(f"❌ Erreur envoi commande '{command}': {e}")
            return False
    
    def read_single_response(self):
        """Lit une seule réponse du capteur (comme dans LabVIEW)"""
        try:
            response = self.ser.readline().decode().strip()
            if response:
                print(f"📥 Réponse: '{response}'")
                return response
            else:
                print("📥 Aucune réponse")
                return ""
                
        except Exception as e:
            print(f"❌ Erreur lecture: {e}")
            return ""
    
    def execute_full_sequence(self):
        """Exécute la séquence complète de commandes"""
        print(f"\n=== EXÉCUTION SÉQUENCE COMPLÈTE ===")
        
        sequence_data = {
            'timestamp': datetime.now().isoformat(),
            'responses': {}
        }
        
        for i, (command, wait_ms) in enumerate(self.command_sequence):
            print(f"\n--- Étape {i+1}/{len(self.command_sequence)}: {command}* ---")
            
            # Envoyer la commande
            if self.send_command(command):
                # Attendre le délai spécifié
                time.sleep(wait_ms / 1000.0)  # Conversion ms -> s
                
                # Lire une seule réponse (comme dans LabVIEW)
                response = self.read_single_response()
                sequence_data['responses'][command] = [response] if response else []
                
                if response:
                    print(f"✓ Réponse reçue")
                    
                    # Analyser la réponse
                    if response:
                        values = response.split()  # Les valeurs semblent séparées par des espaces
                        print(f"  → {len(values)} valeurs détectées: {values}")
                else:
                    print(f"⚠️ Aucune réponse reçue")
            else:
                print(f"❌ Échec envoi commande {command}")
                break
        
        return sequence_data
    
    def test_individual_commands(self):
        """Test des commandes individuelles"""
        print(f"\n=== TEST COMMANDES INDIVIDUELLES ===")
        
        for command, wait_ms in self.command_sequence:
            print(f"\n--- Test de {command}* ---")
            
            # Vider le buffer
            self.ser.flushInput()
            
            # Tester la commande
            if self.send_command(command):
                time.sleep(wait_ms / 1000.0)
                response = self.read_single_response()  # Une seule lecture
                
                if response:
                    print(f"✓ Réponse reçue")
                    
                    # Analyser la réponse
                    values = response.split()
                    print(f"  → {len(values)} valeurs: {values}")
                    
                    # Essayer d'identifier le type de données selon la longueur
                    if len(values) == 3:
                        print(f"  → Probable: Accéléromètre [X, Y, Z]")
                    elif len(values) == 6:
                        print(f"  → Probable: Accéléromètre + Gyroscope [Ax, Ay, Az, Gx, Gy, Gz]")
                    elif len(values) == 9:
                        print(f"  → Probable: Magnétomètre + Accéléromètre + Gyroscope [Mx, My, Mz, Ax, Ay, Az, Gx, Gy, Gz]")
                    elif len(values) == 10:
                        print(f"  → Probable: Tous capteurs + LIDAR [Mx, My, Mz, Ax, Ay, Az, Gx, Gy, Gz, L]")
                else:
                    print(f"❌ Aucune réponse")
            
            # Pause entre les tests
            time.sleep(0.5)
    
    def test_simple_command(self, command="S"):
        """Test d'une commande simple avec une seule lecture"""
        print(f"\n=== TEST SIMPLE COMMANDE {command}* ===")
        
        try:
            # Vider le buffer
            self.ser.flushInput()
            
            # Envoi de la commande
            full_command = command + "*"
            self.ser.write(full_command.encode())
            print(f"📤 Commande envoyée: {full_command}")
            
            # Attendre un peu
            time.sleep(0.1)
            
            # Une seule lecture (comme dans LabVIEW)
            response = self.read_single_response()
            
            return [response] if response else []
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return []
    
    def continuous_sequential_reading(self, save_to_file=True):
        """Lecture continue utilisant le protocole séquentiel"""
        print(f"\n=== LECTURE CONTINUE SÉQUENTIELLE ===")
        print("Appuyez sur Ctrl+C pour arrêter")
        
        if save_to_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"LSM9D_sequential_data_{timestamp}.csv"
            csv_file = open(filename, 'w', newline='')
            csv_writer = csv.writer(csv_file)
            
            # En-tête CSV détaillé
            header = ['cycle', 'timestamp', 'command', 'response_number', 'response_raw']
            csv_writer.writerow(header)
            print(f"✓ Sauvegarde dans: {filename}")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                print(f"\n🔄 Cycle #{cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                sequence_data = self.execute_full_sequence()
                
                # Sauvegarder les données
                if save_to_file:
                    for command, responses in sequence_data['responses'].items():
                        for i, response in enumerate(responses):
                            row = [cycle_count, sequence_data['timestamp'], command, i+1, response]
                            csv_writer.writerow(row)
                    csv_file.flush()
                
                # Pause entre les cycles
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n\n✓ Lecture arrêtée - {cycle_count} cycles complétés")
            
        finally:
            if save_to_file:
                csv_file.close()
                print(f"✓ Fichier sauvegardé: {filename}")
    
    def analyze_raw_data(self, duration=10):
        """Analyse les données brutes pour comprendre le format"""
        print(f"\n=== ANALYSE DES DONNÉES BRUTES ({duration}s) ===")
        
        start_time = time.time()
        raw_data_samples = []
        
        while time.time() - start_time < duration:
            try:
                if self.ser.in_waiting > 0:
                    # Essayer différentes méthodes de lecture
                    
                    # Méthode 1: Lecture par ligne
                    try:
                        line = self.ser.readline().decode('utf-8').strip()
                        if line:
                            raw_data_samples.append(('line', line))
                            print(f"Ligne: '{line}'")
                    except:
                        pass
                        
                    # Méthode 2: Lecture de bytes bruts
                    if self.ser.in_waiting > 0:
                        raw_bytes = self.ser.read(min(50, self.ser.in_waiting))
                        if raw_bytes:
                            hex_str = ' '.join([f'{b:02X}' for b in raw_bytes])
                            ascii_str = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in raw_bytes])
                            raw_data_samples.append(('bytes', hex_str, ascii_str))
                            print(f"Bytes: {hex_str}")
                            print(f"ASCII: '{ascii_str}'")
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                break
        
        print(f"\n📊 Échantillons collectés: {len(raw_data_samples)}")
        return raw_data_samples
    
    def try_csv_format_reading(self, duration=10):
        """Essaie de lire les données en format CSV"""
        print(f"\n=== LECTURE FORMAT CSV ({duration}s) ===")
        
        start_time = time.time()
        csv_lines = []
        
        while time.time() - start_time < duration:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').strip()
                    
                    if line and ',' in line:  # Probable ligne CSV
                        values = line.split(',')
                        csv_lines.append(values)
                        print(f"CSV ({len(values)} colonnes): {values}")
                        
                        # Si on a assez de colonnes pour nos capteurs
                        if len(values) >= 14:
                            parsed_data = self.parse_sensor_data(values)
                            if parsed_data:
                                print(f"  → Données capteurs: {parsed_data}")
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                break
                
        print(f"\n📊 Lignes CSV trouvées: {len(csv_lines)}")
        return csv_lines
    
    def try_binary_format_reading(self, duration=10):
        """Essaie de lire les données en format binaire"""
        print(f"\n=== LECTURE FORMAT BINAIRE ({duration}s) ===")
        
        start_time = time.time()
        binary_packets = []
        
        while time.time() - start_time < duration:
            try:
                if self.ser.in_waiting >= 4:  # Au moins 4 bytes pour un float
                    # Essayer de lire comme des floats
                    data = self.ser.read(4)
                    if len(data) == 4:
                        try:
                            # Essayer little-endian et big-endian
                            float_le = struct.unpack('<f', data)[0]
                            float_be = struct.unpack('>f', data)[0]
                            
                            binary_packets.append((data, float_le, float_be))
                            
                            hex_str = ' '.join([f'{b:02X}' for b in data])
                            print(f"Binaire: {hex_str} → LE: {float_le:.3f}, BE: {float_be:.3f}")
                            
                        except:
                            pass
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                break
                
        print(f"\n📊 Paquets binaires trouvés: {len(binary_packets)}")
        return binary_packets
    
    def parse_sensor_data(self, values):
        """Parse les données selon la configuration du capteur"""
        try:
            if len(values) < 14:
                return None
                
            # Conversion en float des valeurs
            float_values = []
            for val in values:
                try:
                    float_values.append(float(val.strip()))
                except:
                    return None
            
            # Extraction des données capteurs (indices 1-based dans config, 0-based en Python)
            data = {
                'magnetometer': {
                    'x': float_values[abs(self.data_config['M'][0])-1] * (-1 if self.data_config['M'][0] < 0 else 1),
                    'y': float_values[abs(self.data_config['M'][1])-1] * (-1 if self.data_config['M'][1] < 0 else 1),
                    'z': float_values[abs(self.data_config['M'][2])-1] * (-1 if self.data_config['M'][2] < 0 else 1)
                },
                'accelerometer': {
                    'x': float_values[abs(self.data_config['A'][0])-1] * (-1 if self.data_config['A'][0] < 0 else 1),
                    'y': float_values[abs(self.data_config['A'][1])-1] * (-1 if self.data_config['A'][1] < 0 else 1),
                    'z': float_values[abs(self.data_config['A'][2])-1] * (-1 if self.data_config['A'][2] < 0 else 1)
                },
                'gyroscope': {
                    'x': float_values[abs(self.data_config['G'][0])-1] * (-1 if self.data_config['G'][0] < 0 else 1),
                    'y': float_values[abs(self.data_config['G'][1])-1] * (-1 if self.data_config['G'][1] < 0 else 1),
                    'z': float_values[abs(self.data_config['G'][2])-1] * (-1 if self.data_config['G'][2] < 0 else 1)
                },
                'lidar': float_values[self.data_config['L']-1],
                'time': float_values[self.data_config['t']-1],
                'scan_state': float_values[self.data_config['s']-1]
            }
            
            return data
            
        except Exception as e:
            print(f"Erreur parsing: {e}")
            return None
    
    def interactive_command_mode(self):
        """Mode interactif pour envoyer des commandes manuellement"""
        print(f"\n=== MODE COMMANDE INTERACTIVE ===")
        print("Tapez vos commandes (sans le '*' final, il sera ajouté automatiquement)")
        print("Commandes utiles : S, A9, G9, M9, L9, F20, etc.")
        print("Tapez 'quit' ou 'exit' pour quitter ce mode")
        print("Tapez 'help' pour voir des exemples de commandes")
        print("Tapez 'reconnect' ou 'r' pour reconnecter (reset état)")
        print("Tapez 'stop' pour tenter d'arrêter le streaming")
        print("="*60)
        
        while True:
            try:
                # Demander la commande à l'utilisateur
                user_input = input("\n📝 Commande > ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("🚪 Sortie du mode interactif")
                    break
                    
                elif user_input.lower() in ['reconnect', 'r']:
                    self.reconnect()
                    continue
                    
                elif user_input.lower() == 'stop':
                    self.stop_streaming()
                    continue
                    
                elif user_input.lower() == 'help':
                    self.show_command_help()
                    continue
                    
                elif not user_input:
                    print("⚠️ Veuillez entrer une commande")
                    continue
                
                # Vider le buffer avant d'envoyer
                self.ser.flushInput()
                
                # Envoyer la commande
                print(f"\n🔄 Envoi de '{user_input}*'...")
                
                if self.send_command(user_input):
                    # Petite attente
                    time.sleep(0.1)
                    
                    # Lire la réponse
                    response = self.read_single_response()
                    
                    if response:
                        # Analyser la réponse
                        values = response.split()
                        print(f"📊 Analyse: {len(values)} valeurs détectées")
                        
                        # Afficher les valeurs de façon organisée
                        self.display_parsed_values(values, user_input)
                    else:
                        print("❌ Aucune réponse reçue")
                else:
                    print("❌ Erreur lors de l'envoi")
                    
            except KeyboardInterrupt:
                print("\n🚪 Interruption - Sortie du mode interactif")
                break
            except Exception as e:
                print(f"❌ Erreur: {e}")
    
    def show_command_help(self):
        """Affiche l'aide des commandes avec la logique modulaire"""
        print(f"\n📚 AIDE DES COMMANDES (LOGIQUE MODULAIRE):")
        print("\n🔧 COMMANDES D'ACTIVATION:")
        print("  S     - Initialisation/Start")
        print("  A9    - Activation Accéléromètre")
        print("  G9    - Activation Gyroscope") 
        print("  M9    - Activation Magnétomètre")
        print("  L9    - Activation LIDAR")
        
        print("\n📊 COMMANDES DE LECTURE FINALE:")
        print("  F15   - Lecture MAG (Magnétomètre complet)")
        print("  F20   - Lecture MAGL (Tous capteurs + LIDAR)")
        print("  F25   - Lecture capteur individuel")
        
        print("\n🎯 SÉQUENCES RECOMMANDÉES:")
        print("  A+G:     S* → A9* → G9* → F25*")
        print("  M seul:  S* → M9* → F25*")
        print("  MAG:     S* → A9* → G9* → M9* → F15*") 
        print("  MAGL:    S* → A9* → G9* → M9* → L9* → F20*")
        
        print("\n⚠️ COMPORTEMENT IMPORTANT:")
        print("  • Le capteur garde un ÉTAT PERSISTANT après initialisation")
        print("  • Une fois un mode activé, il continue à streamer ces données")
        print("  • Pour changer de mode: RECONNEXION nécessaire (débranchement USB)")
        print("  • Commandes de reset: 'reconnect' ou 'r' dans le mode interactif")
        
        print("\n🔄 GESTION D'ÉTAT:")
        print("  reconnect - Reconnexion complète (reset état)")
        print("  stop      - Tentative d'arrêt du streaming")
        print("  r         - Raccourci pour reconnect")
        
        print("\n🔍 EXEMPLES DE TEST:")
        print("  > S")
        print("  > A9")
        print("  > F25")
        print("  > reconnect")
        print("  > help")
        print("  > quit")
    
    def display_parsed_values(self, values, command):
        """Affiche les valeurs de façon organisée selon le nombre de valeurs"""
        if not values:
            return
            
        print(f"📋 Valeurs brutes: {values}")
        
        try:
            # Convertir en nombres pour affichage
            num_values = [float(v) for v in values]
            
            if len(values) == 2:
                print(f"   Val1: {num_values[0]:.0f}")
                print(f"   Val2: {num_values[1]:.0f}")
                
            elif len(values) == 3:
                print(f"   X: {num_values[0]:.0f}")
                print(f"   Y: {num_values[1]:.0f}")
                print(f"   Z: {num_values[2]:.0f}")
                
            elif len(values) == 6:
                print(f"   📐 Accéléromètre - X: {num_values[0]:.0f}, Y: {num_values[1]:.0f}, Z: {num_values[2]:.0f}")
                print(f"   🌀 Gyroscope     - X: {num_values[3]:.0f}, Y: {num_values[4]:.0f}, Z: {num_values[5]:.0f}")
                
            elif len(values) == 9:
                print(f"   🧲 Magnétomètre  - X: {num_values[0]:.0f}, Y: {num_values[1]:.0f}, Z: {num_values[2]:.0f}")
                print(f"   📐 Accéléromètre - X: {num_values[3]:.0f}, Y: {num_values[4]:.0f}, Z: {num_values[5]:.0f}")
                print(f"   🌀 Gyroscope     - X: {num_values[6]:.0f}, Y: {num_values[7]:.0f}, Z: {num_values[8]:.0f}")
                
            elif len(values) == 10:
                print(f"   🧲 Magnétomètre  - X: {num_values[0]:.0f}, Y: {num_values[1]:.0f}, Z: {num_values[2]:.0f}")
                print(f"   📐 Accéléromètre - X: {num_values[3]:.0f}, Y: {num_values[4]:.0f}, Z: {num_values[5]:.0f}")
                print(f"   🌀 Gyroscope     - X: {num_values[6]:.0f}, Y: {num_values[7]:.0f}, Z: {num_values[8]:.0f}")
                print(f"   📏 LIDAR         - Distance: {num_values[9]:.0f}")
                
            else:
                print(f"   📊 {len(values)} valeurs: {[f'{v:.0f}' for v in num_values]}")
                
        except ValueError:
            print(f"   ⚠️ Certaines valeurs ne sont pas numériques")

    def passive_reading_mode(self, duration=30):
        """Mode de lecture passive - lit les données sans envoyer de commandes"""
        print(f"\n=== MODE LECTURE PASSIVE ({duration}s) ===")
        print("Lecture des données sans envoyer de commandes...")
        print("Appuyez sur Ctrl+C pour arrêter plus tôt")
        print("="*60)
        
        start_time = time.time()
        response_count = 0
        
        try:
            while time.time() - start_time < duration:
                if self.ser.in_waiting > 0:
                    response = self.read_single_response()
                    if response:
                        response_count += 1
                        values = response.split()
                        print(f"📊 #{response_count} - {len(values)} valeurs")
                        self.display_parsed_values(values, "passive")
                        print("-" * 40)
                
                time.sleep(0.1)  # Petite pause pour éviter de surcharger
                
        except KeyboardInterrupt:
            print(f"\n🚪 Lecture interrompue")
            
        print(f"\n✓ Lecture terminée - {response_count} réponses reçues en {time.time() - start_time:.1f}s")

    def execute_custom_sequence(self, sensors, final_command):
        """Exécute une séquence personnalisée selon la logique modulaire"""
        print(f"\n=== SÉQUENCE PERSONNALISÉE ===")
        print(f"Capteurs demandés: {sensors}")
        print(f"Commande finale: {final_command}")
        
        # Mapping des capteurs vers leurs commandes
        sensor_commands = {
            'A': ('A9', 50),  # Accéléromètre
            'G': ('G9', 50),  # Gyroscope  
            'M': ('M9', 50),  # Magnétomètre
            'L': ('L9', 50)   # LIDAR
        }
        
        sequence_data = {
            'timestamp': datetime.now().isoformat(),
            'responses': {}
        }
        
        # 1. Initialisation
        print(f"\n--- Initialisation : S* ---")
        if self.send_command('S'):
            time.sleep(0.1)
            response = self.read_single_response()
            sequence_data['responses']['S'] = [response] if response else []
        
        # 2. Activation des capteurs demandés
        for sensor in sensors:
            if sensor in sensor_commands:
                command, wait_ms = sensor_commands[sensor]
                print(f"\n--- Activation {sensor} : {command}* ---")
                
                if self.send_command(command):
                    time.sleep(wait_ms / 1000.0)
                    response = self.read_single_response()
                    sequence_data['responses'][command] = [response] if response else []
                    
                    if response:
                        values = response.split()
                        print(f"  → {len(values)} valeurs reçues")
        
        # 3. Commande finale pour récupérer les données
        print(f"\n--- Lecture finale : {final_command}* ---")
        if self.send_command(final_command):
            time.sleep(0.1)
            response = self.read_single_response()
            sequence_data['responses'][final_command] = [response] if response else []
            
            if response:
                values = response.split()
                print(f"✓ Données finales: {len(values)} valeurs")
                self.display_parsed_values(values, final_command)
            else:
                print("❌ Aucune donnée finale reçue")
        
        return sequence_data

    def quick_sequence_menu(self):
        """Menu pour les séquences rapides selon la logique modulaire"""
        print(f"\n=== SÉQUENCES RAPIDES ===")
        print("1. A + G (Accéléromètre + Gyroscope) → F25*")
        print("2. M seul (Magnétomètre) → F25*") 
        print("3. MAG (Magnétomètre + Accéléromètre + Gyroscope) → F15*")
        print("4. MAGL (Tous capteurs + LIDAR) → F20*")
        print("5. Séquence personnalisée")
        print("6. Retour au menu principal")
        
        choice = input("Votre choix (1-6): ").strip()
        
        if choice == '1':
            self.execute_custom_sequence(['A', 'G'], 'F25')
        elif choice == '2':
            self.execute_custom_sequence(['M'], 'F25')
        elif choice == '3':
            self.execute_custom_sequence(['A', 'G', 'M'], 'F15')
        elif choice == '4':
            self.execute_custom_sequence(['A', 'G', 'M', 'L'], 'F20')
        elif choice == '5':
            self.custom_sequence_builder()
        elif choice == '6':
            return
        else:
            print("❌ Choix invalide")

    def custom_sequence_builder(self):
        """Constructeur de séquence personnalisée"""
        print(f"\n=== CONSTRUCTEUR DE SÉQUENCE ===")
        
        # Sélection des capteurs
        print("Sélectionnez les capteurs (tapez les lettres sans espaces, ex: AGM):")
        print("  A - Accéléromètre")
        print("  G - Gyroscope") 
        print("  M - Magnétomètre")
        print("  L - LIDAR")
        
        sensors_input = input("Capteurs > ").strip().upper()
        sensors = list(sensors_input)
        
        # Validation
        valid_sensors = ['A', 'G', 'M', 'L']
        sensors = [s for s in sensors if s in valid_sensors]
        
        if not sensors:
            print("❌ Aucun capteur valide sélectionné")
            return
            
        print(f"✓ Capteurs sélectionnés: {sensors}")
        
        # Sélection de la commande finale
        print("\nCommande finale:")
        print("  F15 - Pour MAG (Magnétomètre complet)")
        print("  F20 - Pour MAGL (Tous capteurs)")
        print("  F25 - Pour capteur individuel")
        print("  Autre - Commande personnalisée")
        
        final_cmd = input("Commande finale > ").strip().upper()
        if not final_cmd.startswith('F'):
            final_cmd = 'F' + final_cmd if final_cmd.isdigit() else final_cmd
            
        print(f"✓ Commande finale: {final_cmd}")
        
        # Exécution
        self.execute_custom_sequence(sensors, final_cmd)

    def reconnect(self):
        """Reconnexion complète pour reset l'état du capteur"""
        print(f"\n🔄 RECONNEXION POUR RESET...")
        
        # Fermer la connexion actuelle
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("✓ Port fermé")
            
        # Attendre un peu pour la déconnexion
        time.sleep(1)
        
        # Reconnecter
        if self.connect():
            print("✓ Reconnexion réussie - État du capteur reseté")
            return True
        else:
            print("❌ Échec de la reconnexion")
            return False
    
    def stop_streaming(self):
        """Tentative d'arrêt du streaming (peut ne pas fonctionner selon l'état)"""
        print(f"\n⏹️ TENTATIVE D'ARRÊT DU STREAMING...")
        
        stop_commands = ['STOP*', 'ST*', 'S0*', '0*', 'RESET*']
        
        for cmd in stop_commands:
            print(f"Essai: {cmd}")
            if self.send_command(cmd.replace('*', '')):
                time.sleep(0.1)
                response = self.read_single_response()
                if response:
                    print(f"Réponse: {response}")
                    
        print("⚠️ Si le streaming continue, utilisez la reconnexion (option R)")

def main():
    print("=== LECTEUR DE DONNÉES LSM9D (PROTOCOLE MODULAIRE) ===")
    
    # Créer l'instance du lecteur
    reader = LSM9D_DataReader()
    
    # Se connecter
    if not reader.connect():
        return
    
    try:
        while True:
            print("\n" + "="*60)
            print("MENU:")
            print("1. Test simple d'une commande (S*)")
            print("2. Test des commandes individuelles")
            print("3. Séquences rapides (A+G, MAG, MAGL...)")
            print("4. Mode commande interactive")
            print("5. Mode lecture passive (sans envoyer)")
            print("6. Lecture continue séquentielle")
            print("7. Analyser les données brutes (mode debug)")
            print("R. Reconnexion (reset état du capteur)")
            print("8. Quitter")
            print("="*60)
            print("⚠️ IMPORTANT: Le capteur garde un état persistant!")
            print("   Utilisez 'R' pour changer de mode de capteur")
            print("="*60)
            
            choice = input("Votre choix (1-8, R): ").strip().upper()
            
            if choice == '1':
                reader.test_simple_command("S")
            elif choice == '2':
                reader.test_individual_commands()
            elif choice == '3':
                reader.quick_sequence_menu()
            elif choice == '4':
                reader.interactive_command_mode()
            elif choice == '5':
                duration = input("Durée de lecture en secondes (30 par défaut): ").strip()
                duration = int(duration) if duration.isdigit() else 30
                reader.passive_reading_mode(duration)
            elif choice == '6':
                reader.continuous_sequential_reading(True)
            elif choice == '7':
                reader.analyze_raw_data(10)
            elif choice == 'R':
                reader.reconnect()
            elif choice == '8':
                break
            else:
                print("❌ Choix invalide")
                
    except KeyboardInterrupt:
        print("\n\n--- Arrêt demandé ---")
        
    finally:
        reader.disconnect()

if __name__ == "__main__":
    main() 