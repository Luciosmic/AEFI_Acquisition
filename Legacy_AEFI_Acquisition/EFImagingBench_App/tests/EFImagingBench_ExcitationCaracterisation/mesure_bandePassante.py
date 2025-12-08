#!/usr/bin/env python3
"""
Script de balayage automatique en fréquence pour la calibration DDS
Mesure uniquement le channel 1 avec un gain DDS fixé à 5000
Utilise une sonde avec un ratio de 10:1
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
project_root = os.path.join(current_dir, '../../../../')  # Remonte au répertoire racine
agilent_path = os.path.join(project_root, 'Agilent_DSOX2014')
instruments_path = os.path.join(project_root, 'getE3D/instruments')

# Vérification et ajout des chemins
paths_to_add = []
for path in [agilent_path, instruments_path]:
    if os.path.exists(path):
        paths_to_add.append(path)
        print(f"[mesure_BandePassante] ✓ Chemin ajouté : {path}")
    else:
        print(f"[mesure_BandePassante] ✗ Chemin introuvable : {path}")

sys.path.extend(paths_to_add)

# Import avec gestion d'erreur
try:
    # Import direct après avoir ajouté les chemins au sys.path
    from EFImagingBench_Oscilloscope_DSOX2014 import OscilloscopeDSOX2014AController
    from AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator
    print("[mesure_BandePassante] ✓ Modules importés avec succès")
except ImportError as e:
    print(f"[mesure_BandePassante] ✗ Erreur d'import : {e}")
    sys.exit(1)

# Paramètres par défaut
DEFAULT_FREQ_MIN = 10  # Hz
DEFAULT_FREQ_MAX = 1e5  # Hz
DEFAULT_N_POINTS = 2
DEFAULT_DDS_PORT = "COM10"
CH1 = 1  # Canal à mesurer
DDS_GAIN = 5000  # Gain DDS fixé à 5000
SONDE_RATIO = 10  # Ratio de la sonde 10:1
AVG_COUNT = 16 # Moyennage sur 16 échantillons

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
    """Effectue une mesure pour une fréquence donnée sur le channel 1"""
    try:
        # Configuration DDS et attente
        print(f"[mesure_BandePassante]   Configuration DDS à {freq:.1f} Hz...")
        ok, msg = dds.set_dds_frequency(freq)
        if not ok:
            return None, f"Erreur configuration DDS : {msg}"
        
        print(f"[mesure_BandePassante]   Configuration du gain DDS à {DDS_GAIN}...")
        ok, msg = dds.set_dds_gain(1, DDS_GAIN)
        if not ok:
            return None, f"Erreur configuration gain DDS1 : {msg}"
        print(f"[mesure_BandePassante]   ✓ Gain DDS configuré à {DDS_GAIN}")
        
        # Attendre que le signal se stabilise
        time.sleep(1.0)
        
        # D'abord l'autoscale pour trouver le signal
        print(f"[mesure_BandePassante]   Exécution de l'autoscale...")
        scope.scope.write(":AUToscale")
        time.sleep(3.0)  # Attendre que l'autoscale soit terminé
        
        # Ensuite optimiser la base de temps pour voir 2 périodes
        period = 1.0 / freq  # Période en secondes
        target_timebase = period / 2  # Pour voir ~2 périodes
        print(f"[mesure_BandePassante]   Optimisation base de temps : {target_timebase*1000:.2f} ms/div (2 périodes)")
        timebase_ok = scope.configure_timebase(tscale=target_timebase, position=0.0)
        
        # Attendre que les changements soient appliqués
        time.sleep(0.5)
        
        # Mesure de l'amplitude après optimisation
        measures = scope.get_measurements(CH1)
        amp1 = measures.get('VPP', None)
        
        if amp1 is None:
            print(f"[mesure_BandePassante]   ⚠️ Impossible de lire l'amplitude")
            return None, "Lecture d'amplitude échouée"
        else:
            print(f"[mesure_BandePassante]   Amplitude mesurée : {amp1} V")
        
        # Validation des mesures pour détecter les valeurs aberrantes
        is_valid = True
        error_msg = ""
        
        # Vérification de l'amplitude (doit être raisonnable)
        # Les seuils sont multipliés par 10 car la sonde atténue d'un facteur 10
        if amp1 is not None and (amp1 < 0.1 or amp1 > 1000):
            is_valid = False
            error_msg += f"Amplitude CH{CH1} aberrante: {amp1} V "
        
        if not is_valid:
            return None, f"Mesure rejetée - valeurs aberrantes détectées: {error_msg}"
        
        # Résultat
        result = {
            'frequence_Hz': freq,
            f'VPP_CH{CH1}': amp1,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return result, None
        
    except Exception as e:
        return None, f"Erreur inattendue : {e}"

def balayage_frequence(freq_list, dds_port=DEFAULT_DDS_PORT, resume_from=None):
    """Effectue le balayage complet en fréquence"""
    print("[mesure_BandePassante] === Balayage automatique en fréquence ===")
    print(f"[mesure_BandePassante] Nombre de fréquences à tester : {len(freq_list)}")
    print(f"[mesure_BandePassante] Plage : {freq_list[0]:.1f} Hz à {freq_list[-1]:.1f} Hz")
    print(f"[mesure_BandePassante] Sonde utilisée : ratio {SONDE_RATIO}:1")
    
    # Génération du nom de fichier avec date, heure et paramètres
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    freq_min = freq_list[0]
    freq_max = freq_list[-1]
    n_points = len(freq_list)
    
    # Création du dossier data s'il n'existe pas
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Nom de fichier descriptif
    csv_filename = f"{timestamp}_bandePassante_freq{freq_min:.0f}-{freq_max:.0f}Hz_{n_points}pts.csv"
    csv_path = os.path.join(data_dir, csv_filename)
    
    print(f"[mesure_BandePassante] Fichier de résultats : {csv_filename}")
    
    # Initialisation des instruments
    scope = None
    dds = None
    
    try:
        # Initialiser l'oscilloscope
        scope = OscilloscopeDSOX2014AController()
        # Augmenter le timeout si nécessaire
        scope.scope.timeout = 5000  # 5 secondes
        print("[mesure_BandePassante] ✓ Oscilloscope initialisé")
        
        dds = SerialCommunicator()
        print("[mesure_BandePassante] ✓ DDS initialisé")
        
        # Connexion DDS
        print(f"[mesure_BandePassante] Connexion DDS sur {dds_port}...")
        ok, msg = dds.connect(dds_port)
        if not ok:
            print(f"[mesure_BandePassante] ✗ Erreur connexion DDS : {msg}")
            return False
        
        print("[mesure_BandePassante] ✓ DDS connecté")
        
        # Configuration oscilloscope initiale
        print("[mesure_BandePassante] Configuration oscilloscope...")
        scope.configure_channel(channel=CH1, vdiv=1.0, offset=0.0, coupling="DC", sonde_ratio=SONDE_RATIO)
        scope.configure_acquisition(average_count=AVG_COUNT)
        scope.configure_trigger(source=f"CHAN{CH1}", level=0.0, slope="POS")
        print("[mesure_BandePassante] ✓ Oscilloscope configuré")
        
        # Charger les résultats existants si reprise
        existing_results = []
        if resume_from and os.path.exists(resume_from):
            try:
                df_existing = pd.read_csv(resume_from)
                existing_results = df_existing['frequence_Hz'].tolist()
                print(f"[mesure_BandePassante] ✓ Reprise depuis : {resume_from}")
                print(f"[mesure_BandePassante]   {len(existing_results)} mesures existantes")
            except Exception as e:
                print(f"[mesure_BandePassante] ⚠️ Impossible de lire les résultats existants : {e}")
        elif os.path.exists(csv_path):
            try:
                df_existing = pd.read_csv(csv_path)
                existing_results = df_existing['frequence_Hz'].tolist()
                print(f"[mesure_BandePassante] ✓ Reprise détectée : {len(existing_results)} mesures existantes dans {csv_filename}")
            except Exception as e:
                print(f"[mesure_BandePassante] ⚠️ Impossible de lire les résultats existants : {e}")
        else:
            print("[mesure_BandePassante] ✓ Nouveau balayage")
        
        # Balayage
        results = []
        for i, freq in enumerate(freq_list):
            print(f"\n[mesure_BandePassante] --- Mesure {i+1}/{len(freq_list)} : {freq:.1f} Hz ---")
            
            # Vérifier si déjà mesuré
            if freq in existing_results:
                print(f"[mesure_BandePassante]   ⏭️ Fréquence déjà mesurée, passage à la suivante")
                continue
            
            # Mesure
            result, error = measure_single_frequency(freq, scope, dds, dds_port)
            
            if result is not None:
                results.append(result)
                print(f"[mesure_BandePassante]   ✓ Mesure réussie : amplitude={result[f'VPP_CH{CH1}']:.4f} V")
                
                # Sauvegarde incrémentale
                df_new = pd.DataFrame([result])
                if os.path.exists(csv_path):
                    df_existing = pd.read_csv(csv_path)
                    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                else:
                    df_combined = df_new
                df_combined.to_csv(csv_path, index=False)
                print(f"[mesure_BandePassante]   ✓ Sauvegardé dans {csv_path}")
            else:
                print(f"[mesure_BandePassante]   ✗ Échec : {error}")
                # Continuer avec la fréquence suivante
        
        print(f"\n[mesure_BandePassante] === Balayage terminé ===")
        print(f"[mesure_BandePassante] Mesures réussies : {len(results)}/{len(freq_list)}")
        print(f"[mesure_BandePassante] Résultats sauvegardés dans : {csv_path}")
        
        return True
        
    except KeyboardInterrupt:
        print("\n[mesure_BandePassante] ⚠️ Balayage interrompu par l'utilisateur")
        return False
    except Exception as e:
        print(f"[mesure_BandePassante] ❌ Erreur inattendue : {e}")
        return False
    finally:
        # Nettoyage
        if dds:
            try:
                dds.disconnect()
                print("[mesure_BandePassante] ✓ DDS déconnecté")
            except:
                pass
        if scope:
            try:
                scope.close()
                print("[mesure_BandePassante] ✓ Oscilloscope fermé")
            except:
                pass

def main():
    parser = argparse.ArgumentParser(description='Balayage automatique en fréquence pour calibration DDS (Channel 1 uniquement)')
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
    
    print(f"[mesure_BandePassante] Liste des fréquences générée :")
    print(f"[mesure_BandePassante]   {len(freq_list)} points de {freq_list[0]:.1f} Hz à {freq_list[-1]:.1f} Hz")
    print(f"[mesure_BandePassante]   Échelle : {'linéaire' if args.linear else 'logarithmique'}")
    
    # Confirmation utilisateur
    response = input("\n[mesure_BandePassante] Démarrer le balayage ? (o/N) : ")
    if response.lower() not in ['o', 'oui', 'y', 'yes']:
        print("[mesure_BandePassante] Balayage annulé")
        return
    
    # Lancement du balayage
    success = balayage_frequence(freq_list, args.dds_port, args.resume)
    
    if success:
        print("\n[mesure_BandePassante] ✅ Balayage terminé avec succès !")
    else:
        print("\n[mesure_BandePassante] ❌ Balayage terminé avec des erreurs")

if __name__ == "__main__":
    main() 