#!/usr/bin/env python3
"""
Script de test minimal pour la nouvelle fonction optimize_vdiv avec autoscale
Test avec un signal à 1kHz et un gain DDS de 5000
"""

import os
import sys
import time

# Ajout des chemins pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '../../../../')  # Remonte au répertoire racine
agilent_path = os.path.join(project_root, 'Agilent_DSOX2014')
instruments_path = os.path.join(project_root, 'getE3D/instruments')

# Vérification et ajout des chemins
paths_to_add = []
for path in [agilent_path, instruments_path]:
    if os.path.exists(path):
        paths_to_add.append(path)
        print(f"[test_minimal] ✓ Chemin ajouté : {path}")
    else:
        print(f"[test_minimal] ✗ Chemin introuvable : {path}")

sys.path.extend(paths_to_add)

# Import avec gestion d'erreur
try:
    # Import direct après avoir ajouté les chemins au sys.path
    from EFImagingBench_Oscilloscope_DSOX2014 import OscilloscopeDSOX2014AController
    from AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator
    print("[test_minimal] ✓ Modules importés avec succès")
except ImportError as e:
    print(f"[test_minimal] ✗ Erreur d'import : {e}")
    sys.exit(1)

# Paramètres de test
TEST_FREQ = 1000  # 1 kHz
DDS_GAIN = 5000   # Gain DDS fixé à 5000
DDS_PORT = "COM10"
CH1 = 1           # Canal à mesurer
SONDE_RATIO = 10  # Ratio de la sonde 10:1

def main():
    """Fonction principale de test"""
    scope = None
    dds = None
    
    try:
        # Initialiser l'oscilloscope
        print("[test_minimal] Initialisation de l'oscilloscope...")
        scope = OscilloscopeDSOX2014AController()
        scope.scope.timeout = 5000  # 5 secondes
        print("[test_minimal] ✓ Oscilloscope initialisé")
        
        # Initialiser le DDS
        print("[test_minimal] Initialisation du DDS...")
        dds = SerialCommunicator()
        print("[test_minimal] ✓ DDS initialisé")
        
        # Connexion DDS
        print(f"[test_minimal] Connexion DDS sur {DDS_PORT}...")
        ok, msg = dds.connect(DDS_PORT)
        if not ok:
            print(f"[test_minimal] ✗ Erreur connexion DDS : {msg}")
            return
        print("[test_minimal] ✓ DDS connecté")
        
        # Configuration oscilloscope initiale
        print("[test_minimal] Configuration oscilloscope...")
        scope.configure_channel(channel=CH1, vdiv=1.0, offset=0.0, coupling="DC", sonde_ratio=SONDE_RATIO)
        scope.configure_acquisition(average_count=16)
        scope.configure_trigger(source=f"CHAN{CH1}", level=0.0, slope="POS")
        print("[test_minimal] ✓ Oscilloscope configuré")
        
        # Configuration DDS à 1kHz
        print(f"[test_minimal] Configuration DDS à {TEST_FREQ} Hz...")
        ok, msg = dds.set_dds_frequency(TEST_FREQ)
        if not ok:
            print(f"[test_minimal] ✗ Erreur configuration DDS : {msg}")
            return
        
        # Configuration du gain DDS à 5000
        print(f"[test_minimal] Configuration du gain DDS à {DDS_GAIN}...")
        ok, msg = dds.set_dds_gain(1, DDS_GAIN)  # DDS1
        if not ok:
            print(f"[test_minimal] ✗ Erreur configuration gain DDS1 : {msg}")
            return
        print(f"[test_minimal] ✓ Gain DDS configuré à {DDS_GAIN}")
        
        # Attendre que le signal se stabilise
        print("[test_minimal] Attente de stabilisation du signal (3s)...")
        time.sleep(3.0)
        
        # Optimisation de la base de temps pour voir 2 périodes
        period = 1.0 / TEST_FREQ  # Période en secondes
        target_timebase = period / 2  # Pour voir ~2 périodes
        print(f"[test_minimal] Configuration base de temps : {target_timebase*1000:.2f} ms/div (2 périodes)")
        timebase_ok = scope.configure_timebase(tscale=target_timebase, position=0.0)
        if not timebase_ok:
            print("[test_minimal] ⚠️ Configuration de la base de temps non optimale")
        
        # Attendre que la base de temps soit appliquée
        time.sleep(1.0)
        
        # Test de la fonction optimize_vdiv avec autoscale
        print("[test_minimal] Test de optimize_vdiv avec autoscale...")
        vdiv_auto = scope.optimize_vdiv(
            channel=CH1, 
            coupling="DC", 
            sonde_ratio=SONDE_RATIO
        )
        print(f"[test_minimal] ✓ Échelle verticale après autoscale : {vdiv_auto} V/div (valeur brute)")
        print(f"[test_minimal] ✓ Échelle effective appliquée : {vdiv_auto * SONDE_RATIO} V/div")
        
        # Mesure de l'amplitude après optimisation
        print("[test_minimal] Mesure de l'amplitude après optimisation...")
        measures = scope.get_measurements(CH1)
        amp = measures.get('VPP', None)
        freq = measures.get('FREQ', None)
        
        if amp is not None:
            print(f"[test_minimal] ✓ Amplitude mesurée : {amp} V")
        else:
            print("[test_minimal] ⚠️ Impossible de lire l'amplitude")
        
        if freq is not None:
            print(f"[test_minimal] ✓ Fréquence mesurée : {freq} Hz (attendu: {TEST_FREQ} Hz)")
        else:
            print("[test_minimal] ⚠️ Impossible de lire la fréquence")
        
        print("[test_minimal] Test terminé avec succès")
        
    except Exception as e:
        print(f"[test_minimal] ❌ Erreur inattendue : {e}")
    finally:
        # Nettoyage
        if dds:
            try:
                dds.disconnect()
                print("[test_minimal] ✓ DDS déconnecté")
            except:
                pass
        if scope:
            try:
                scope.close()
                print("[test_minimal] ✓ Oscilloscope fermé")
            except:
                pass

if __name__ == "__main__":
    main()
