import os
import time
import pandas as pd
import sys
from datetime import datetime

# Ajout des chemins pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '../../..')  # Remonte de 3 niveaux
agilent_path = os.path.join(project_root, 'Agilent_DSOX2014')
instruments_path = os.path.join(project_root, 'getE3D/instruments')

# Vérification et ajout des chemins
paths_to_add = []
for path in [agilent_path, instruments_path]:
    if os.path.exists(path):
        paths_to_add.append(path)
        print(f"✓ Chemin ajouté : {path}")
    else:
        print(f"✗ Chemin introuvable : {path}")

sys.path.extend(paths_to_add)

# Import avec gestion d'erreur
try:
    from EFImagingBench_Oscilloscope_DSOX2014 import OscilloscopeDSOX2014AController
    print("✓ Module oscilloscope importé avec succès")
except ImportError as e:
    print(f"✗ Erreur d'import oscilloscope : {e}")
    print("Vérifiez que le fichier EFImagingBench_Oscilloscope_DSOX2014.py existe dans Agilent_DSOX2014/")
    sys.exit(1)

try:
    from AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator
    print("✓ Module DDS importé avec succès")
except ImportError as e:
    print(f"✗ Erreur d'import DDS : {e}")
    print("Vérifiez que le fichier AD9106_ADS131A04_SerialCommunicationModule.py existe dans getE3D/instruments/")
    sys.exit(1)

# Paramètres
CH1 = 3  # DDS1 amplifié
CH2 = 4  # DDS2 amplifié
DDS_PORT = "COM10"  # Port automatique

# Initialisation des instruments
scope = None
dds = None

def initialize_instruments():
    """Initialise les instruments avec gestion d'erreur"""
    global scope, dds
    
    try:
        scope = OscilloscopeDSOX2014AController()
        print("✓ Oscilloscope initialisé")
    except Exception as e:
        print(f"✗ Erreur d'initialisation oscilloscope : {e}")
        return False
    
    try:
        dds = SerialCommunicator()
        print("✓ DDS initialisé")
    except Exception as e:
        print(f"✗ Erreur d'initialisation DDS : {e}")
        return False
    
    return True

def main():
    print("=== Script de mesure phase/amplitude ===")
    
    # Initialisation des instruments
    if not initialize_instruments():
        print("❌ Impossible d'initialiser les instruments. Arrêt.")
        return
    
    try:
        freq = float(input("Fréquence à tester (Hz) : "))
        print(f"Connexion DDS sur {DDS_PORT}...")
        
        # Connexion DDS
        ok, msg = dds.connect(DDS_PORT)
        if not ok:
            print(f"[ERREUR] {msg}")
            return
        print("✓ DDS connecté")
        
        print("Configuration DDS...")
        ok, msg = dds.set_dds_frequency(freq)
        if not ok:
            print(f"[ERREUR] {msg}")
            return
        print(f"✓ Fréquence DDS configurée : {freq} Hz")
        
        # Configuration du gain DDS à 1000 pour les deux canaux
        print("Configuration du gain DDS...")
        ok, msg = dds.set_dds_gain(1, 515)  # DDS1
        if not ok:
            print(f"[ERREUR] Configuration gain DDS1 : {msg}")
            return
        ok, msg = dds.set_dds_gain(2, 515)  # DDS2
        if not ok:
            print(f"[ERREUR] Configuration gain DDS2 : {msg}")
            return
        print("✓ Gain DDS configuré à 1000 pour les deux canaux")
        
        time.sleep(0.5)
        print("Configuration oscilloscope...")
        scope.configure_channel(channel=CH1, vdiv=1.0, offset=0.0, coupling="DC")
        scope.configure_channel(channel=CH2, vdiv=1.0, offset=0.0, coupling="DC")
        scope.configure_acquisition(average_count=64)
        scope.configure_trigger(source=f"CHAN{CH1}", level=0.0, slope="POS")
        print("✓ Oscilloscope configuré")

        # Optimisation de la fenêtre temporelle pour voir 2 périodes
        period = 1.0 / freq  # Période en secondes
        target_timebase = period / 2  # Pour voir ~2 périodes (optimal pour mesure de déphasage)
        print(f"Optimisation de la base de temps...")
        print(f"  Période : {period*1000:.2f} ms")
        print(f"  Base de temps cible : {target_timebase*1000:.2f} ms/div (2 périodes visibles)")
        
        # Configuration de la base de temps
        scope.scope.write(f":TIMebase:SCALe {target_timebase}")
        time.sleep(0.2)
        
        # Optimisation de la fenêtre verticale pour chaque canal
        print("Optimisation de la fenêtre verticale (vdiv) pour CH{0}...".format(CH1))
        success1, vdiv1_opt, vpp1, essais1 = scope.optimize_vdiv(channel=CH1, coupling="DC")
        if success1 and vdiv1_opt is not None:
            print(f"  → vdiv optimal CH{CH1} : {vdiv1_opt} V/div (Vpp mesuré : {vpp1})")
            scope.configure_channel(channel=CH1, vdiv=vdiv1_opt, offset=0.0, coupling="DC")
        else:
            print(f"  ⚠️ Optimisation vdiv CH{CH1} échouée. On garde la config initiale.")

        print("Optimisation de la fenêtre verticale (vdiv) pour CH{0}...".format(CH2))
        success2, vdiv2_opt, vpp2, essais2 = scope.optimize_vdiv(channel=CH2, coupling="DC")
        if success2 and vdiv2_opt is not None:
            print(f"  → vdiv optimal CH{CH2} : {vdiv2_opt} V/div (Vpp mesuré : {vpp2})")
            scope.configure_channel(channel=CH2, vdiv=vdiv2_opt, offset=0.0, coupling="DC")
        else:
            print(f"  ⚠️ Optimisation vdiv CH{CH2} échouée. On garde la config initiale.")

        time.sleep(0.5)
        print("Mesure du déphasage...")
        try:
            phase = scope.measure_phase(CH1, CH2)
            print(f"✓ Déphasage mesuré : {phase:.2f}°")
        except Exception as e:
            print(f"✗ Erreur mesure phase : {e}")
            phase = None
        
        print("Lecture des amplitudes...")
        amp1 = scope.get_measurements(CH1).get('VPP', None)
        amp2 = scope.get_measurements(CH2).get('VPP', None)
        print(f"✓ Amplitude CH{CH1} : {amp1} V | CH{CH2} : {amp2} V")
        
        # Calcul du rapport de multiplication (fonction de transfert)
        # CH2/CH1 = VPP_CH4/VPP_CH3 pour obtenir la fonction de transfert
        transfer_function = None
        if amp1 is not None and amp2 is not None and amp1 > 0:
            transfer_function = amp2 / amp1
            print(f"✓ Fonction de transfert (CH{CH2}/CH{CH1}) : {transfer_function:.4f}")
        else:
            print(f"⚠️ Impossible de calculer la fonction de transfert (amp1={amp1}, amp2={amp2})")
        
        # Sauvegarde
        result = {
            'frequence_Hz': freq,
            'phase_deg': phase,
            f'VPP_CH{CH1}': amp1,
            f'VPP_CH{CH2}': amp2,
            'transfer_function': transfer_function,  # Rapport CH4/CH3
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Générer le nom du fichier CSV avec timestamp et paramètres
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f"mesure_{timestamp}_freq{freq:.0f}Hz.csv"
        csv_path = os.path.join(os.path.dirname(__file__), '../mesures', csv_filename)
        
        # Créer le répertoire de mesures s'il n'existe pas
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)
        else:
            df = pd.DataFrame([result])
        
        df.to_csv(csv_path, index=False)
        print(f"✓ Résultat sauvegardé dans {csv_filename}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Mesure interrompue par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")
    finally:
        # Nettoyage
        if dds:
            try:
                dds.disconnect()
                print("✓ DDS déconnecté")
            except:
                pass
        if scope:
            try:
                scope.close()
                print("✓ Oscilloscope fermé")
            except:
                pass

if __name__ == "__main__":
    main() 