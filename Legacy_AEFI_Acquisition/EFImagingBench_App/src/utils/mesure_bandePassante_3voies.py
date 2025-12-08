#!/usr/bin/env python3
"""
Script de balayage automatique en fréquence pour la calibration DDS
Mesure uniquement le channel 1 avec un gain DDS fixé à 5000
Utilise une sonde avec un ratio de 10:1
"""

import os
import sys
import time
import json
import numpy as np
import pandas as pd
import argparse
from datetime import datetime

# Ajout des chemins pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '../../../')  # Remonte au répertoire racine (3 niveaux)
agilent_path = os.path.join(project_root, 'Agilent_DSOX2014')
instruments_path = os.path.join(project_root, 'getE3D/instruments')
# Chemin alternatif pour le module SerialCommunicator dans EFImagingBench_App
ef_controller_path = os.path.join(project_root, 'EFImagingBench_App/src/core/AD9106_ADS131A04_ElectricField_3D/controller')

# Vérification et ajout des chemins
paths_to_add = []
for path in [agilent_path, instruments_path, ef_controller_path]:
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
    
    # Essai d'import du SerialCommunicator avec gestion des différentes sources possibles
    try:
        # Essai d'abord depuis getE3D/instruments
        from AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator
        print("[mesure_BandePassante] ✓ SerialCommunicator importé depuis getE3D/instruments")
    except ImportError:
        try:
            # Si échec, essai depuis le module EFImagingBench_App
            import sys
            sys.path.insert(0, ef_controller_path)  # Priorité à ce chemin
            from AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator
            print("[mesure_BandePassante] ✓ SerialCommunicator importé depuis EFImagingBench_App")
        except ImportError as e:
            print(f"[mesure_BandePassante] ✗ Impossible d'importer SerialCommunicator : {e}")
            sys.exit(1)
    
    print("[mesure_BandePassante] ✓ Tous les modules importés avec succès")
except ImportError as e:
    print(f"[mesure_BandePassante] ✗ Erreur d'import : {e}")
    sys.exit(1)

# Paramètres par défaut
DEFAULT_FREQ_MIN = 100  # Hz
DEFAULT_FREQ_MAX = 1000000  # Hz
DEFAULT_N_POINTS = 10
points_per_decade = True

DEFAULT_DDS_PORT = "COM10"
CHANNELS = [1, 2, 3]  # Canaux à mesurer
DDS_GAIN = 5500  # Gain DDS fixé à 5000
SONDE_RATIO = 10  # Ratio de la sonde 10:1
AVG_COUNT = 16 # Moyennage sur 16 échantillons

# Paramètres du capteur
Rg = 5.6  # Résistance de gain en kOhm
Gain_Ampli_Instru_Capteur = 9.83  # Gain de l'amplificateur d'instrumentation du capteur

# Configurations disponibles
available_configs = ['X', 'Y']
config = 'X'  # Configuration par défaut

# Configuration des phases selon le mode
if config == 'Y':
    PHASE_DDS1 = 0      # Phase du DDS1 (0-65535)
    PHASE_DDS2 = 0      # Phase du DDS2 (0-65535)
elif config == 'X':
    PHASE_DDS1 = 0      # Phase du DDS1 (0-65535)
    PHASE_DDS2 = 32768  # Phase du DDS2 (0-65535) - 180 degrés

# DDS1_MODE = "AC"  # Mode du DDS1 (AC ou DC)
# DDS2_MODE = "AC"  # Mode du DDS2 (AC ou DC)



def measure_single_frequency(freq, scope, dds, dds_port):
    """Effectue une mesure pour une fréquence donnée sur les canaux spécifiés"""
    try:
        # Configuration de la fréquence DDS uniquement
        print(f"[mesure_BandePassante]   Configuration DDS à {freq:.1f} Hz...")
        ok, msg = dds.set_dds_frequency(freq)
        if not ok:
            return None, f"Erreur configuration DDS : {msg}"
        
        # Attendre que le signal se stabilise
        time.sleep(5.0)
        
        # D'abord l'autoscale pour trouver le signal
        print(f"[mesure_BandePassante]   Exécution de l'autoscale...")
        scope.scope.write(":AUToscale")
        time.sleep(5.0)  # Attendre que l'autoscale soit terminé
        
        # Ensuite optimiser la base de temps pour voir 2 périodes
        period = 1.0 / freq  # Période en secondes
        target_timebase = period / 2  # Pour voir ~2 périodes
        print(f"[mesure_BandePassante]   Optimisation base de temps : {target_timebase*1000:.2f} ms/div (2 périodes)")
        timebase_ok = scope.configure_timebase(tscale=target_timebase, position=0.0)
        
        # Attendre que les changements soient appliqués
        time.sleep(3)
        
        # Résultat initial avec la fréquence et le timestamp
        result = {
            'frequence_Hz': freq,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Mesure de l'amplitude pour chaque canal
        is_valid = True
        error_msg = ""
        
        for channel in CHANNELS:
            # Mesure de l'amplitude
            measures = scope.get_measurements(channel)
            amplitude = measures.get('VPP', None)
            
            if amplitude is None:
                print(f"[mesure_BandePassante]   ⚠️ Impossible de lire l'amplitude sur le canal {channel}")
                error_msg += f"Lecture d'amplitude échouée sur CH{channel}. "
                is_valid = False
            else:
                print(f"[mesure_BandePassante]   Amplitude mesurée sur CH{channel} : {amplitude} V")
                result[f'VPP_CH{channel}'] = amplitude
                
                # Vérification de l'amplitude (doit être raisonnable)
                # Les seuils sont multipliés par 10 car la sonde atténue d'un facteur 10
                if amplitude < 0.1 or amplitude > 1000:
                    is_valid = False
                    error_msg += f"Amplitude CH{channel} aberrante: {amplitude} V. "
        
        if not is_valid:
            return None, f"Mesure rejetée - valeurs aberrantes détectées: {error_msg}"
        
        return result, None
        
    except Exception as e:
        return None, f"Erreur inattendue : {e}"

def balayage_frequence(freq_list, dds_port=DEFAULT_DDS_PORT, resume_from=None, chosen_config='Y', capteur_rg=5.6, capteur_gain=9.83):
    """Effectue le balayage complet en fréquence"""
    print("[mesure_BandePassante] === Balayage automatique en fréquence ===")
    print(f"[mesure_BandePassante] Nombre de fréquences à tester : {len(freq_list)}")
    print(f"[mesure_BandePassante] Plage : {freq_list[0]:.1f} Hz à {freq_list[-1]:.1f} Hz")
    print(f"[mesure_BandePassante] Canaux mesurés : {', '.join(map(str, CHANNELS))}")
    print(f"[mesure_BandePassante] Configuration : {chosen_config} (PHASE_DDS1={PHASE_DDS1}, PHASE_DDS2={PHASE_DDS2})")
    print(f"[mesure_BandePassante] Sonde utilisée : ratio {SONDE_RATIO}:1")
    print(f"[mesure_BandePassante] Paramètres capteur : Rg={capteur_rg} kOhm, Gain={capteur_gain}")
    
    # Génération du nom de fichier avec date, heure et paramètres
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    freq_min = freq_list[0]
    freq_max = freq_list[-1]
    n_points = len(freq_list)
    
    # Création du dossier data s'il n'existe pas
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Nom de fichier descriptif (sans la configuration dans le nom)
    csv_filename = f"{timestamp}_bandePassante_freq{freq_min:.0f}-{freq_max:.0f}Hz_{n_points}pts.csv"
    csv_path = os.path.join(data_dir, csv_filename)
    
    # Nom du fichier JSON associé
    json_filename = csv_filename.replace('.csv', '.json')
    json_path = os.path.join(data_dir, json_filename)
    
    print(f"[mesure_BandePassante] Fichier de résultats : {csv_filename}")
    print(f"[mesure_BandePassante] Fichier de configuration : {json_filename}")
    
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
        
        # Configuration DDS globale (gain, phase, mode)
        print("[mesure_BandePassante] Configuration globale du DDS...")
        
        # Configuration du gain DDS1
        print(f"[mesure_BandePassante] Configuration du gain DDS1 à {DDS_GAIN}...")
        ok, msg = dds.set_dds_gain(1, DDS_GAIN)
        if not ok:
            print(f"[mesure_BandePassante] ✗ Erreur configuration gain DDS1 : {msg}")
            return False
        print(f"[mesure_BandePassante] ✓ Gain DDS1 configuré à {DDS_GAIN}")
        
        # Configuration de la phase DDS1
        print(f"[mesure_BandePassante] Configuration de la phase DDS1 à {PHASE_DDS1}...")
        ok, msg = dds.set_dds_phase(1, PHASE_DDS1)
        if not ok:
            print(f"[mesure_BandePassante] ✗ Erreur configuration phase DDS1 : {msg}")
            return False
        print(f"[mesure_BandePassante] ✓ Phase DDS1 configurée à {PHASE_DDS1}")
        
        # Configuration de la phase DDS2
        print(f"[mesure_BandePassante] Configuration de la phase DDS2 à {PHASE_DDS2}...")
        ok, msg = dds.set_dds_phase(2, PHASE_DDS2)
        if not ok:
            print(f"[mesure_BandePassante] ✗ Erreur configuration phase DDS2 : {msg}")
            return False
        print(f"[mesure_BandePassante] ✓ Phase DDS2 configurée à {PHASE_DDS2}")
        
        # # Configuration des modes DDS
        # print(f"[mesure_BandePassante] Configuration des modes DDS : DDS1={DDS1_MODE}, DDS2={DDS2_MODE}...")
        # dds1_ac = (DDS1_MODE == "AC")
        # dds2_ac = (DDS2_MODE == "AC")
        # ok, msg = dds.set_dds_modes(dds1_ac, dds2_ac, True, True)  # DDS3 et DDS4 en AC par défaut
        # if not ok:
        #     print(f"[mesure_BandePassante] ✗ Erreur configuration modes DDS : {msg}")
        #     return False
        # print(f"[mesure_BandePassante] ✓ Modes DDS configurés")
        
        # Configuration oscilloscope initiale pour tous les canaux
        print("[mesure_BandePassante] Configuration oscilloscope...")
        for channel in CHANNELS:
            print(f"[mesure_BandePassante] Configuration du canal {channel}...")
            scope.configure_channel(channel=channel, vdiv=1.0, offset=0.0, coupling="DC", sonde_ratio=SONDE_RATIO)
        
        # Configuration de l'acquisition et du trigger (sur le premier canal)
        scope.configure_acquisition(average_count=AVG_COUNT)
        scope.configure_trigger(source=f"CHAN{CHANNELS[0]}", level=0.0, slope="POS")
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
                # Afficher les amplitudes de tous les canaux
                amplitudes_str = ", ".join([f"CH{ch}={result[f'VPP_CH{ch}']:.4f} V" for ch in CHANNELS])
                print(f"[mesure_BandePassante]   ✓ Mesure réussie : {amplitudes_str}")
                
                # Sauvegarde incrémentale
                df_new = pd.DataFrame([result])
                if os.path.exists(csv_path):
                    df_existing = pd.read_csv(csv_path)
                    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                else:
                    df_combined = df_new
                df_combined.to_csv(csv_path, index=False)
                print(f"[mesure_BandePassante]   ✓ Données sauvegardées dans {csv_path}")
                
                # Création et sauvegarde du fichier JSON avec les paramètres
                config_data = {
                    "acquisition_params": {
                        "timestamp": timestamp,
                        "freq_min": freq_min,
                        "freq_max": freq_max,
                        "n_points": n_points,
                        "points_per_decade": points_per_decade
                    },
                    "excitation_params": {
                        "config": chosen_config,
                        "DDS_GAIN": DDS_GAIN,
                        "PHASE_DDS1": PHASE_DDS1,
                        "PHASE_DDS2": PHASE_DDS2
                    },
                    "measurement_params": {
                        "CHANNELS": CHANNELS,
                        "SONDE_RATIO": SONDE_RATIO,
                        "AVG_COUNT": AVG_COUNT
                    },
                    "sensor_params": {
                        "Rg": capteur_rg,
                        "Gain_Ampli_Instru_Capteur": capteur_gain
                    },
                    "data_file": csv_filename
                }
                
                with open(json_path, 'w') as f:
                    json.dump(config_data, f, indent=4)
                print(f"[mesure_BandePassante]   ✓ Configuration sauvegardée dans {json_path}")
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


def create_frequency_list(freq_min, freq_max, n_points, log_scale=True, use_points_per_decade=None):
    """
    Crée la liste des fréquences à tester
    
    Args:
        freq_min: Fréquence minimale en Hz
        freq_max: Fréquence maximale en Hz
        n_points: Nombre de points total ou par décade selon points_per_decade
        log_scale: Si True, échelle logarithmique, sinon linéaire
        use_points_per_decade: Si True, n_points est interprété comme le nombre de points par décade.
                              Si None, utilise la valeur globale de points_per_decade.
    """
    # Utiliser la variable globale si aucune valeur n'est fournie
    if use_points_per_decade is None:
        use_points_per_decade = points_per_decade
    if log_scale:
        if use_points_per_decade:
            # Calculer le nombre de décades
            n_decades = np.log10(freq_max / freq_min)
            # Calculer le nombre total de points
            total_points = int(np.ceil(n_points * n_decades))
            # Générer les fréquences
            frequencies = np.logspace(np.log10(freq_min), np.log10(freq_max), total_points)
            print(f"[mesure_BandePassante] {n_points} points par décade sur {n_decades:.2f} décades = {total_points} points au total")
        else:
            # Comportement original: n_points au total sur toute la plage
            frequencies = np.logspace(np.log10(freq_min), np.log10(freq_max), n_points)
    else:
        # En échelle linéaire, points_per_decade n'a pas de sens
        frequencies = np.linspace(freq_min, freq_max, n_points)
    
    # Arrondir à des valeurs "propres"
    frequencies = np.round(frequencies, 1)
    return frequencies


def main():
    parser = argparse.ArgumentParser(description='Balayage automatique en fréquence pour calibration DDS')
    parser.add_argument('--freq-min', type=float, default=DEFAULT_FREQ_MIN, 
                       help=f'Fréquence minimale en Hz (défaut: {DEFAULT_FREQ_MIN})')
    parser.add_argument('--freq-max', type=float, default=DEFAULT_FREQ_MAX, 
                       help=f'Fréquence maximale en Hz (défaut: {DEFAULT_FREQ_MAX})')
    parser.add_argument('--n-points', type=int, default=DEFAULT_N_POINTS, 
                       help=f'Nombre de points par décade par défaut (défaut: {DEFAULT_N_POINTS})')
    parser.add_argument('--linear', action='store_true', 
                       help='Échelle linéaire au lieu de logarithmique')
    parser.add_argument('--no-points-per-decade', action='store_true', 
                       help='Interpréter n-points comme le nombre total de points et non par décade')
    parser.add_argument('--dds-port', type=str, default=DEFAULT_DDS_PORT, 
                       help=f'Port DDS (défaut: {DEFAULT_DDS_PORT})')
    parser.add_argument('--config', type=str, choices=available_configs, default=config,
                       help=f'Configuration d\'excitation (défaut: {config})')
    parser.add_argument('--rg', type=float, default=Rg,
                       help=f'Résistance de gain en kOhm (défaut: {Rg})')
    parser.add_argument('--gain-capteur', type=float, default=Gain_Ampli_Instru_Capteur,
                       help=f'Gain de l\'amplificateur d\'instrumentation du capteur (défaut: {Gain_Ampli_Instru_Capteur})')
    parser.add_argument('--resume', action='store_true', 
                       help='Reprendre un balayage interrompu')
    
    args = parser.parse_args()
    
    # Utilisation des paramètres du capteur depuis les arguments
    capteur_rg = args.rg
    capteur_gain = args.gain_capteur
    
    # Mise à jour de la configuration et des phases
    chosen_config = args.config
    # Mise à jour des phases selon la configuration
    if chosen_config == 'X':
        PHASE_DDS1 = 0
        PHASE_DDS2 = 0
    elif chosen_config == 'Y':
        PHASE_DDS1 = 0
        PHASE_DDS2 = 32768
    
    # Création de la liste des fréquences
    # Si --no-points-per-decade est spécifié, on désactive le mode points par décade
    use_points_per_decade = not args.no_points_per_decade
    
    freq_list = create_frequency_list(args.freq_min, args.freq_max, args.n_points, 
                                     not args.linear, use_points_per_decade)
    
    print(f"[mesure_BandePassante] Configuration : {chosen_config} (PHASE_DDS1={PHASE_DDS1}, PHASE_DDS2={PHASE_DDS2})")
    print(f"[mesure_BandePassante] Paramètres capteur : Rg={capteur_rg} kOhm, Gain={capteur_gain}")
    print(f"[mesure_BandePassante] Liste des fréquences générée :")
    print(f"[mesure_BandePassante]   {len(freq_list)} points de {freq_list[0]:.1f} Hz à {freq_list[-1]:.1f} Hz")
    print(f"[mesure_BandePassante]   Échelle : {'linéaire' if args.linear else 'logarithmique'}")
    if not args.linear:
        print(f"[mesure_BandePassante]   Mode : {DEFAULT_N_POINTS} points {'par décade' if use_points_per_decade else 'au total'}")
    
    # Confirmation utilisateur
    response = input("\n[mesure_BandePassante] Démarrer le balayage ? (o/N) : ")
    if response.lower() not in ['o', 'oui', 'y', 'yes']:
        print("[mesure_BandePassante] Balayage annulé")
        return
    
    # Lancement du balayage
    success = balayage_frequence(freq_list, args.dds_port, args.resume, chosen_config, capteur_rg, capteur_gain)
    
    if success:
        print("\n[mesure_BandePassante] ✅ Balayage terminé avec succès !")
    else:
        print("\n[mesure_BandePassante] ❌ Balayage terminé avec des erreurs")

if __name__ == "__main__":
    main() 