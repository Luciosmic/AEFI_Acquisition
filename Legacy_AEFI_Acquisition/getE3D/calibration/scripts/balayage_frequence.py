#!/usr/bin/env python3
"""
Script de balayage automatique en fréquence pour la calibration DDS
Utilise le script de mesure existant pour effectuer des mesures sur une plage de fréquences
"""

import os
import sys
import time
import numpy as np
import pandas as pd
import argparse
from datetime import datetime

# Ajout des chemins pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '../../..')
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
    from AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator
    print("✓ Modules importés avec succès")
except ImportError as e:
    print(f"✗ Erreur d'import : {e}")
    sys.exit(1)

# Paramètres par défaut
DEFAULT_FREQ_MIN = 1  # Hz
DEFAULT_FREQ_MAX = 1e6  # Hz (500 kHz)
DEFAULT_N_POINTS = 3
DEFAULT_DDS_PORT = "COM10"
CH1 = 1  # DDS1 amplifié
CH2 = 2  # DDS2 amplifié

def create_frequency_list(freq_min, freq_max, n_points, log_scale=True):
    """Crée la liste des fréquences à tester"""
    if log_scale:
        frequencies = np.logspace(np.log10(freq_min), np.log10(freq_max), n_points)
    else:
        frequencies = np.linspace(freq_min, freq_max, n_points)
    
    # Arrondir à des valeurs "propres"
    frequencies = np.round(frequencies, 1)
    return frequencies

def measure_single_frequency(freq, scope, dds, dds_port):
    """Effectue une mesure pour une fréquence donnée"""
    try:
        print(f"  Configuration DDS à {freq:.1f} Hz...")
        ok, msg = dds.set_dds_frequency(freq)
        if not ok:
            return None, f"Erreur configuration DDS : {msg}"
        
        # Configuration du gain DDS à 1000 pour les deux canaux
        print(f"  Configuration du gain DDS...")
        ok, msg = dds.set_dds_gain(1, 515)  # DDS1
        if not ok:
            return None, f"Erreur configuration gain DDS1 : {msg}"
        ok, msg = dds.set_dds_gain(2, 515)  # DDS2
        if not ok:
            return None, f"Erreur configuration gain DDS2 : {msg}"
        print(f"  ✓ Gain DDS configuré à 1000")
        
        time.sleep(0.5)
        
        # Optimisation de la fenêtre temporelle pour voir 2 périodes
        period = 1.0 / freq  # Période en secondes
        target_timebase = period / 2  # Pour voir ~2 périodes (optimal pour mesure de déphasage)
        print(f"  Optimisation base de temps : {target_timebase*1000:.2f} ms/div (2 périodes)")
        scope.scope.write(f":TIMebase:SCALe {target_timebase}")
        time.sleep(0.2)
        
        # Optimisation de la fenêtre verticale pour chaque canal
        print(f"  Optimisation vdiv CH{CH1}...")
        success1, vdiv1_opt, vpp1, essais1 = scope.optimize_vdiv(channel=CH1, coupling="DC")
        if success1 and vdiv1_opt is not None:
            scope.configure_channel(channel=CH1, vdiv=vdiv1_opt, offset=0.0, coupling="DC")
        
        print(f"  Optimisation vdiv CH{CH2}...")
        success2, vdiv2_opt, vpp2, essais2 = scope.optimize_vdiv(channel=CH2, coupling="DC")
        if success2 and vdiv2_opt is not None:
            scope.configure_channel(channel=CH2, vdiv=vdiv2_opt, offset=0.0, coupling="DC")
        
        time.sleep(0.5)
        
        # Mesures
        print(f"  Mesure du déphasage...")
        try:
            phase = scope.measure_phase(CH1, CH2)
        except Exception as e:
            phase = None
            print(f"    ⚠️ Erreur mesure phase : {e}")
        
        print(f"  Lecture des amplitudes...")
        amp1 = scope.get_measurements(CH1).get('VPP', None)
        amp2 = scope.get_measurements(CH2).get('VPP', None)
        
        # Calcul de la fonction de transfert
        transfer_function = None
        if amp1 is not None and amp2 is not None and amp1 > 0:
            transfer_function = amp2 / amp1
        
        # Validation des mesures pour détecter les valeurs aberrantes
        is_valid = True
        error_msg = ""
        
        # Vérification des amplitudes (doivent être raisonnables)
        if amp1 is not None and (amp1 < 0.1 or amp1 > 100):
            is_valid = False
            error_msg += f"Amplitude CH{CH1} aberrante: {amp1} V "
        
        if amp2 is not None and (amp2 < 0.1 or amp2 > 100):
            is_valid = False
            error_msg += f"Amplitude CH{CH2} aberrante: {amp2} V "
        
        # Vérification de la phase (doit être entre -180° et +180°)
        if phase is not None and (phase < -180 or phase > 180):
            is_valid = False
            error_msg += f"Phase aberrante: {phase}° "
        
        # Vérification de la fonction de transfert (doit être raisonnable)
        if transfer_function is not None and (transfer_function < 0.1 or transfer_function > 10):
            is_valid = False
            error_msg += f"Fonction de transfert aberrante: {transfer_function} "
        
        if not is_valid:
            return None, f"Mesure rejetée - valeurs aberrantes détectées: {error_msg}"
        
        # Résultat
        result = {
            'frequence_Hz': freq,
            'phase_deg': phase,
            f'VPP_CH{CH1}': amp1,
            f'VPP_CH{CH2}': amp2,
            'transfer_function': transfer_function,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return result, None
        
    except Exception as e:
        return None, f"Erreur inattendue : {e}"

def balayage_frequence(freq_list, dds_port=DEFAULT_DDS_PORT, resume_from=None):
    """Effectue le balayage complet en fréquence"""
    print("=== Balayage automatique en fréquence ===")
    print(f"Nombre de fréquences à tester : {len(freq_list)}")
    print(f"Plage : {freq_list[0]:.1f} Hz à {freq_list[-1]:.1f} Hz")
    
    # Génération du nom de fichier avec date, heure et paramètres
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    freq_min = freq_list[0]
    freq_max = freq_list[-1]
    n_points = len(freq_list)
    
    # Nom de fichier descriptif
    csv_filename = f"balayage_{timestamp}_freq{freq_min:.0f}-{freq_max:.0f}Hz_{n_points}pts.csv"
    csv_path = os.path.join(os.path.dirname(__file__), '../mesures', csv_filename)
    
    print(f"Fichier de résultats : {csv_filename}")
    
    # Créer le répertoire de mesures s'il n'existe pas
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
    # Initialisation des instruments
    scope = None
    dds = None
    
    try:
        scope = OscilloscopeDSOX2014AController()
        print("✓ Oscilloscope initialisé")
        
        dds = SerialCommunicator()
        print("✓ DDS initialisé")
        
        # Connexion DDS
        print(f"Connexion DDS sur {dds_port}...")
        ok, msg = dds.connect(dds_port)
        if not ok:
            print(f"✗ Erreur connexion DDS : {msg}")
            return False
        
        print("✓ DDS connecté")
        
        # Configuration oscilloscope
        print("Configuration oscilloscope...")
        scope.configure_channel(channel=CH1, vdiv=1.0, offset=0.0, coupling="DC")
        scope.configure_channel(channel=CH2, vdiv=1.0, offset=0.0, coupling="DC")
        scope.configure_acquisition(average_count=64)
        scope.configure_trigger(source=f"CHAN{CH1}", level=0.0, slope="POS")
        print("✓ Oscilloscope configuré")
        
        # Charger les résultats existants si reprise
        existing_results = []
        if resume_from and os.path.exists(resume_from):
            try:
                df_existing = pd.read_csv(resume_from)
                existing_results = df_existing['frequence_Hz'].tolist()
                print(f"✓ Reprise depuis : {resume_from}")
                print(f"  {len(existing_results)} mesures existantes")
            except Exception as e:
                print(f"⚠️ Impossible de lire les résultats existants : {e}")
        elif os.path.exists(csv_path):
            try:
                df_existing = pd.read_csv(csv_path)
                existing_results = df_existing['frequence_Hz'].tolist()
                print(f"✓ Reprise détectée : {len(existing_results)} mesures existantes dans {csv_filename}")
            except Exception as e:
                print(f"⚠️ Impossible de lire les résultats existants : {e}")
        else:
            print("✓ Nouveau balayage")
        
        # Balayage
        results = []
        for i, freq in enumerate(freq_list):
            print(f"\n--- Mesure {i+1}/{len(freq_list)} : {freq:.1f} Hz ---")
            
            # Vérifier si déjà mesuré
            if freq in existing_results:
                print(f"  ⏭️ Fréquence déjà mesurée, passage à la suivante")
                continue
            
            # Mesure
            result, error = measure_single_frequency(freq, scope, dds, dds_port)
            
            if result is not None:
                results.append(result)
                print(f"  ✓ Mesure réussie : phase={result['phase_deg']:.2f}°, transfert={result['transfer_function']:.4f}")
                
                # Sauvegarde incrémentale
                df_new = pd.DataFrame([result])
                if os.path.exists(csv_path):
                    df_existing = pd.read_csv(csv_path)
                    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                else:
                    df_combined = df_new
                df_combined.to_csv(csv_path, index=False)
                print(f"  ✓ Sauvegardé dans {csv_path}")
            else:
                print(f"  ✗ Échec : {error}")
                # Continuer avec la fréquence suivante
        
        print(f"\n=== Balayage terminé ===")
        print(f"Mesures réussies : {len(results)}/{len(freq_list)}")
        print(f"Résultats sauvegardés dans : {csv_path}")
        
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️ Balayage interrompu par l'utilisateur")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")
        return False
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

def main():
    parser = argparse.ArgumentParser(description='Balayage automatique en fréquence pour calibration DDS')
    parser.add_argument('--freq-min', type=float, default=DEFAULT_FREQ_MIN, 
                       help=f'Fréquence minimale en Hz (défaut: {DEFAULT_FREQ_MIN})')
    parser.add_argument('--freq-max', type=float, default=DEFAULT_FREQ_MAX, 
                       help=f'Fréquence maximale en Hz (défaut: {DEFAULT_FREQ_MAX})')
    parser.add_argument('--n-points', type=int, default=DEFAULT_N_POINTS, 
                       help=f'Nombre de points (défaut: {DEFAULT_N_POINTS})')
    parser.add_argument('--linear', action='store_true', 
                       help='Échelle linéaire au lieu de logarithmique')
    parser.add_argument('--dds-port', type=str, default=DEFAULT_DDS_PORT, 
                       help=f'Port DDS (défaut: {DEFAULT_DDS_PORT})')
    parser.add_argument('--resume', action='store_true', 
                       help='Reprendre un balayage interrompu')
    
    args = parser.parse_args()
    
    # Création de la liste des fréquences
    freq_list = create_frequency_list(args.freq_min, args.freq_max, args.n_points, not args.linear)
    
    print(f"Liste des fréquences générée :")
    print(f"  {len(freq_list)} points de {freq_list[0]:.1f} Hz à {freq_list[-1]:.1f} Hz")
    print(f"  Échelle : {'linéaire' if args.linear else 'logarithmique'}")
    
    # Confirmation utilisateur
    response = input("\nDémarrer le balayage ? (o/N) : ")
    if response.lower() not in ['o', 'oui', 'y', 'yes']:
        print("Balayage annulé")
        return
    
    # Lancement du balayage
    success = balayage_frequence(freq_list, args.dds_port, args.resume)
    
    if success:
        print("\n✅ Balayage terminé avec succès !")
    else:
        print("\n❌ Balayage terminé avec des erreurs")

if __name__ == "__main__":
    main() 