import matplotlib.pyplot as plt
import numpy as np
import pyvisa
import time

def list_available_devices():
    """Liste tous les périphériques VISA disponibles avec plus de détails."""
    rm = pyvisa.ResourceManager()
    devices = rm.list_resources()
    
    print("\nRecherche des périphériques VISA...")
    print("-----------------------------------")
    
    if not devices:
        print("Aucun périphérique VISA trouvé.")
        print("\nVérifiez que :")
        print("1. L'oscilloscope est bien connecté via USB")
        print("2. Les pilotes VISA sont installés")
        print("3. L'oscilloscope est allumé")
        return []
    
    # Filtrer et afficher les périphériques USB
    usb_devices = [d for d in devices if "USB" in d]
    if usb_devices:
        print("\nPériphériques USB trouvés :")
        for i, device in enumerate(usb_devices, 1):
            try:
                with rm.open_resource(device) as inst:
                    idn = inst.query("*IDN?")
                    print(f"{i}. {device}")
                    print(f"   Identifiant : {idn}")
            except:
                print(f"{i}. {device}")
                print("   Impossible de lire les informations du périphérique")
    else:
        print("\nAucun périphérique USB trouvé.")
        print("Périphériques série trouvés :")
        for i, device in enumerate(devices, 1):
            print(f"{i}. {device}")
    
    return devices

def select_device():
    """Permet à l'utilisateur de sélectionner un périphérique parmi ceux disponibles."""
    devices = list_available_devices()
    
    if not devices:
        raise Exception("Aucun périphérique VISA trouvé. Vérifiez les connexions.")
    
    while True:
        try:
            choice = int(input("\nSélectionnez le numéro de l'oscilloscope (1-{}): ".format(len(devices))))
            if 1 <= choice <= len(devices):
                return devices[choice - 1]
            else:
                print("Choix invalide. Veuillez réessayer.")
        except ValueError:
            print("Veuillez entrer un nombre valide.")

def connect_to_oscilloscope():
    """Établit la connexion avec l'oscilloscope DSO-X 2014A."""
    print("\nInitialisation de la connexion...")
    
    device_address = select_device()
    print(f"\nTentative de connexion à : {device_address}")
    
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            print(f"Tentative de connexion {attempt + 1}/{max_attempts}...")
            rm = pyvisa.ResourceManager()
            scope = rm.open_resource(device_address)
            scope.timeout = 10000
            
            model = scope.query("*IDN?")
            print(f"Modèle détecté : {model}")
            
            if "DSO-X 2014A" not in model:
                print(f"Attention : Le modèle détecté ({model}) n'est pas un DSO-X 2014A.")
                if input("Voulez-vous continuer quand même ? (o/n): ").lower() != 'o':
                    scope.close()
                    raise Exception("Connexion annulée par l'utilisateur.")
            
            return scope
            
        except Exception as e:
            print(f"Erreur lors de la tentative {attempt + 1}: {str(e)}")
            if attempt < max_attempts - 1:
                print("Nouvelle tentative dans 2 secondes...")
                time.sleep(2)
            else:
                raise Exception(f"Impossible de se connecter après {max_attempts} tentatives.")

def configure_channel(scope, channel=1, vdiv=50.0, offset=0.0, coupling="DC"):
    """Configure un canal de l'oscilloscope."""
    print(f"\nConfiguration du canal {channel}...")
    
    # Configurer le voltage/div
    scope.write(f":CHANnel{channel}:SCALe {vdiv}")
    print(f"Voltage/div : {vdiv}V")
    
    # Configurer l'offset
    scope.write(f":CHANnel{channel}:OFFSet {offset}")
    print(f"Offset : {offset}V")
    
    # Configurer le couplage
    scope.write(f":CHANnel{channel}:COUPling {coupling}")
    print(f"Couplage : {coupling}")

def configure_measurements(scope, channel=1):
    """Configure les mesures automatiques sur le canal spécifié."""
    print(f"\nConfiguration des mesures sur le canal {channel}...")
    
    # Activer les mesures
    scope.write(":MEASure:STATistics ON")
    
    # Configurer les mesures
    measurements = {
        "FREQ": "Fréquence",
        "VPP": "Tension crête à crête",
        "VMAX": "Tension maximale",
        "VMIN": "Tension minimale",
        "VAMP": "Amplitude",
        "VRMS": "Tension RMS",
        "PERIOD": "Période",
        "RISE": "Temps de montée",
        "FALL": "Temps de descente"
    }
    
    # Activer toutes les mesures
    for measure in measurements.keys():
        scope.write(f":MEASure:{measure} CHANnel{channel}")
        print(f"Mesure {measure} ({measurements[measure]}) activée")
    
    return measurements

def get_measurements(scope, measurements):
    """Récupère les valeurs des mesures configurées."""
    results = {}
    
    print("\nRécupération des mesures...")
    for measure in measurements.keys():
        try:
            value = float(scope.query(f":MEASure:{measure}?"))
            results[measure] = value
            print(f"{measure}: {value}")
        except:
            print(f"Impossible de lire la mesure {measure}")
    
    return results

def get_waveform(scope, channel=1):
    """Récupère la forme d'onde du canal spécifié."""
    print(f"\nConfiguration de l'acquisition sur le canal {channel}...")
    
    scope.write(":RUN")
    scope.write(f":WAVeform:SOURce CHANnel{channel}")
    scope.write(":WAVeform:FORMat BYTE")
    
    print("Récupération des données...")
    scope.write(":WAVeform:DATA?")
    data = scope.read_raw()
    
    data = data[2:-1]
    voltage = np.frombuffer(data, dtype=np.int8)
    
    vscale = float(scope.query(f":CHANnel{channel}:SCALe?"))
    voffset = float(scope.query(f":CHANnel{channel}:OFFSet?"))
    
    voltage = voltage * vscale / 25.0 - voffset
    
    tscale = float(scope.query(":TIMebase:SCALe?"))
    tdelay = float(scope.query(":TIMebase:POSition?"))
    
    time = np.linspace(tdelay - 5*tscale, tdelay + 5*tscale, len(voltage))
    
    return time, voltage

def main():
    try:
        scope = connect_to_oscilloscope()
        print("Connexion établie avec l'oscilloscope")
        
        # Configuration du canal avec 50V/div
        configure_channel(scope, channel=1, vdiv=50.0)
        
        # Configurer les mesures
        measurements = configure_measurements(scope, channel=1)
        
        # Récupérer les mesures
        results = get_measurements(scope, measurements)
        
        # Récupérer la forme d'onde
        time, voltage = get_waveform(scope, channel=1)
        
        # Afficher les données
        plt.figure(figsize=(12, 8))
        
        # Graphique de la forme d'onde
        plt.subplot(2, 1, 1)
        plt.plot(time, voltage)
        plt.title("Forme d'onde - Canal 1")
        plt.xlabel("Temps (s)")
        plt.ylabel("Tension (V)")
        plt.grid(True)
        
        # Tableau des mesures
        plt.subplot(2, 1, 2)
        plt.axis('off')
        table_data = [[measure, f"{value:.3f}"] for measure, value in results.items()]
        table = plt.table(cellText=table_data,
                         colLabels=['Mesure', 'Valeur'],
                         loc='center',
                         cellLoc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 1.5)
        
        plt.tight_layout()
        plt.show()
        
    except Exception as e:
        print(f"\nErreur lors de la communication avec l'oscilloscope: {str(e)}")
        print("\nSuggestions de dépannage :")
        print("1. Vérifiez que l'oscilloscope est allumé")
        print("2. Vérifiez la connexion USB")
        print("3. Assurez-vous que les pilotes VISA sont installés")
        print("4. Essayez de redémarrer l'oscilloscope")
    finally:
        if 'scope' in locals():
            print("\nFermeture de la connexion...")
            scope.close()

if __name__ == "__main__":
    main() 