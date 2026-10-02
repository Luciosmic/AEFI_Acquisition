"""
Caracterisation du bruit ADC pur (ADS131A04), en fonction de l'OSR : circuit ouvert vs court-circuit.

Pourquoi : lever la dette D5 ("origine de la composante non blanche (captation secteur, boucle de
masse, alimentation de l'electronique de conditionnement...) : rien dans ces donnees ne la
renseigne", voir 0_inbox/data-a-interpreter/2026-10-02_debit-et-bruit-acquisition-aefi-vs-n-avg-mcu/
.../le-bruit-de-l-acquisition-aefi-...md) en mesurant le bruit de l'ADC seul -- sans aucune
electronique de conditionnement ni capteur en amont -- pour comparaison avec le bruit observe sur la
chaine complete et avec le bruit annonce par la datasheet.

Montage (deja fait par l'operateur, ce script ne le modifie pas) :
- Canal 5 (Z in-phase)   : entree en circuit ouvert (rien de connecte)
- Canal 6 (Z quadrature) : entree court-circuitee (pattes differentielles reliees)
- Canaux 1-4 (X in-phase/quadrature, Y in-phase/quadrature) : branches sur le capteur reel -- gardes
  cette fois (premiere version du script les acquerait mais les jetait) pour situer le bruit de la
  chaine complete, a OSR variable, entre les deux cas extremes ci-dessus

Scope : script de caracterisation ponctuelle, PAS du code de production, PAS une nouvelle couche DDD.
Modele sur acquisition_hardware_test.py (meme dossier) : instancie MCU_SerialCommunicator et
ADS131A04Adapter directement, sans passer par l'application. N'a aucune fonction nommee test_*, donc
pytest (qui collecte les items par prefixe de fonction, pas seulement par nom de fichier) ne ramasse
rien depuis ce fichier malgre son suffixe _test.py -- meme convention que le fichier modele.

Reglage reel de l'OSR materiel : passe par IAdcOversamplingPort / AdapterAdcOversamplingAds131a04
(ADS131Controller.set_oversampling_ratio), comme AdcOutputRateCharacterizationService. acquire_sample()
de ADS131A04Adapter n'est pas modifie et reste appele tel quel ; son ADCHardwareConfig (gain, Vref,
OSR "de label") ne sert qu'a convertir les codes bruts en volts et n'ecrit rien dans le materiel.
"""
import csv
import json
import os
import shutil
import statistics
import sys
import time
from datetime import datetime, timezone

import numpy as np
import serial.tools.list_ports

# Assuming this file is in src/infrastructure/hardware/micro_controller/ads131a04/_tests/
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../..'))

from infrastructure.hardware.micro_controller.MCU_serial_communicator import MCU_SerialCommunicator
from infrastructure.hardware.micro_controller.ads131a04.adapter_i_acquistion_port_ads131a04 import ADS131A04Adapter
from infrastructure.hardware.micro_controller.ads131a04.ads131_controller import ADS131Controller
from infrastructure.hardware.micro_controller.ads131a04.adapter_adc_oversampling_ads131a04 import (
    AdapterAdcOversamplingAds131a04,
)

SELECTED_PORT = "COM10"
BAUDRATE = 1500000
N_SAMPLES_PER_OSR = 200
REFERENCE_VOLTAGE = 2.442  # V, reference interne -- valeur active dans ads131a04_last_config.json
SETTLE_DELAY_S = 0.05  # meme valeur par defaut que AdcOutputRateCharacterizationService
# L'ADS131Controller n'a pas de lecture de registre (memory_state est une ombre logicielle qui
# demarre a 32 par defaut, cf. adapter_adc_oversampling_ads131a04.py). L'OSR reellement actif avant
# ce script est celui laisse par la derniere session de l'application : 4096 (ads131a04_last_config.json).
OSR_TO_RESTORE = 4096

EXPORT_ROOT = r"C:\Users\manip\Desktop\AEFI_Acquisition_Exports\HARDWARE-CHARACTERIZATION\ADC"
VAULT_ROOT = r"C:\Users\manip\Dropbox\Luis\1 PROJETS\1 - THESE\0_inbox\data-a-interpreter"

CHANNEL_LABELS = (
    # (attribut AefiVoltageMeasurement, cle csv/npz, description)
    ("voltage_x_in_phase", "x_in_phase_capteur_reel", "Canal 1 (X in-phase, capteur reel)"),
    ("voltage_x_quadrature", "x_quadrature_capteur_reel", "Canal 2 (X quadrature, capteur reel)"),
    ("voltage_y_in_phase", "y_in_phase_capteur_reel", "Canal 3 (Y in-phase, capteur reel)"),
    ("voltage_y_quadrature", "y_quadrature_capteur_reel", "Canal 4 (Y quadrature, capteur reel)"),
    ("voltage_z_in_phase", "z_in_phase_circuit_ouvert", "Canal 5 (Z in-phase, circuit ouvert)"),
    ("voltage_z_quadrature", "z_quadrature_court_circuit", "Canal 6 (Z quadrature, court-circuit)"),
)


def build_adc_config(osr: int) -> dict:
    """Config logicielle pour acquire_sample() : gain=1 tous canaux, Vref=2.442V, OSR de label.
    N'ecrit rien dans le materiel (voir load_config dans ADS131A04Adapter)."""
    return {
        "channels": {str(ch): {"gain": 1} for ch in range(1, 7)},
        "oversampling_ratio": osr,
        "reference_voltage": REFERENCE_VOLTAGE,
    }


def main():
    print(f"Ports serie disponibles : {[p.device for p in serial.tools.list_ports.comports()]}")
    print(f"Connexion a {SELECTED_PORT} a {BAUDRATE} bauds...")

    communicator = MCU_SerialCommunicator()
    if not communicator.connect(SELECTED_PORT, baudrate=BAUDRATE):
        print(f"Echec de connexion a {SELECTED_PORT}")
        return
    print(f"Connecte a {SELECTED_PORT}")

    # n_avg_reader fixe a 1 : pas de moyennage logiciel MCU, pour isoler l'effet de l'OSR materiel seul.
    adapter = ADS131A04Adapter(communicator, n_avg_reader=lambda: 1)
    controller = ADS131Controller(communicator)
    oversampling_port = AdapterAdcOversamplingAds131a04(controller)

    osr_values = list(ADS131A04Adapter.AVAILABLE_OSR)
    print(f"Balayage prevu ({len(osr_values)} OSR) : {osr_values}")

    raw_samples = {}  # cle npz -> np.array des echantillons bruts (V)
    summary_rows = []  # une ligne par (osr, canal)
    start_utc = datetime.now(timezone.utc)

    try:
        for osr in osr_values:
            print(f"\n--- OSR {osr} ---")
            written = oversampling_port.set_oversampling_ratio(osr)
            if written.is_failure:
                print(f"  OSR {osr} non ecrit : {written.error} -- pas acquis pour cet OSR")
                continue
            time.sleep(SETTLE_DELAY_S)
            adapter.load_config(build_adc_config(osr))

            channel_values = {key: [] for _, key, _ in CHANNEL_LABELS}
            for i in range(N_SAMPLES_PER_OSR):
                try:
                    measurement = adapter.acquire_sample()
                except Exception as error:
                    print(f"  Echantillon {i} echoue : {error}")
                    continue
                for attr, key, _ in CHANNEL_LABELS:
                    channel_values[key].append(getattr(measurement, attr))

            for attr, key, description in CHANNEL_LABELS:
                values = channel_values[key]
                n = len(values)
                mean_v = statistics.fmean(values) if n else float("nan")
                sigma_v = statistics.stdev(values) if n > 1 else float("nan")
                print(f"  {description}: n={n} moyenne={mean_v * 1e3:.4f} mV sigma={sigma_v * 1e6:.2f} uV")
                summary_rows.append({
                    "oversampling_ratio": osr,
                    "canal": key,
                    "description_canal": description,
                    "n": n,
                    "moyenne_V": mean_v,
                    "sigma_V": sigma_v,
                })
                raw_samples[f"osr_{osr}_{key}"] = np.array(values, dtype=float)
    finally:
        print(f"\nRestauration de l'OSR a {OSR_TO_RESTORE}...")
        restored = oversampling_port.set_oversampling_ratio(OSR_TO_RESTORE)
        print(f"  {'ok' if restored.is_success else 'echec : ' + str(restored.error)}")
        print("Deconnexion...")
        communicator.disconnect()

    end_utc = datetime.now(timezone.utc)
    timestamp_label = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    folder_name = f"{timestamp_label}_bruit-adc-ads131a04-circuit-ouvert-vs-court-circuit-vs-osr"
    file_prefix = f"{timestamp_label}_bruit-adc"

    # --- Ecriture locale (scratchpad) puis copie vers les deux destinations ---
    local_dir = os.path.join(os.path.dirname(__file__), "_bruit_adc_output", folder_name)
    os.makedirs(local_dir, exist_ok=True)

    npz_path = os.path.join(local_dir, f"{file_prefix}_echantillons-bruts.npz")
    np.savez(npz_path, **raw_samples)

    csv_path = os.path.join(local_dir, f"{file_prefix}_resume-par-osr.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "oversampling_ratio", "canal", "description_canal", "n", "moyenne_V", "sigma_V",
        ])
        writer.writeheader()
        writer.writerows(summary_rows)

    conditions_path = os.path.join(local_dir, f"{file_prefix}_conditions.json")
    with open(conditions_path, "w", encoding="utf-8") as f:
        json.dump({
            "debut_utc": start_utc.isoformat(),
            "fin_utc": end_utc.isoformat(),
            "port_serie": SELECTED_PORT,
            "baudrate": BAUDRATE,
            "n_echantillons_par_osr": N_SAMPLES_PER_OSR,
            "n_avg_logiciel_mcu": 1,
            "reference_voltage_V": REFERENCE_VOLTAGE,
            "gain_tous_canaux": 1,
            "osr_balayes": osr_values,
            "osr_restaure": OSR_TO_RESTORE,
            "canal_1_x_in_phase": "capteur reel",
            "canal_2_x_quadrature": "capteur reel",
            "canal_3_y_in_phase": "capteur reel",
            "canal_4_y_quadrature": "capteur reel",
            "canal_5_z_in_phase": "circuit ouvert (rien de connecte)",
            "canal_6_z_quadrature": "court-circuit (pattes differentielles reliees)",
            "script": os.path.relpath(__file__, start=os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..")),
        }, f, indent=2, ensure_ascii=False)

    for destination_root in (EXPORT_ROOT, VAULT_ROOT):
        destination_dir = os.path.join(destination_root, folder_name)
        os.makedirs(destination_dir, exist_ok=True)
        for src_name in (
            f"{file_prefix}_echantillons-bruts.npz",
            f"{file_prefix}_resume-par-osr.csv",
            f"{file_prefix}_conditions.json",
        ):
            shutil.copy2(os.path.join(local_dir, src_name), os.path.join(destination_dir, src_name))
        print(f"Copie ecrite dans {destination_dir}")

    print("\n--- Resume ---")
    for row in summary_rows:
        print(
            f"OSR {row['oversampling_ratio']:>5} | {row['description_canal']:<40} "
            f"| n={row['n']:>3} | sigma={row['sigma_V'] * 1e6:8.2f} uV"
        )


if __name__ == "__main__":
    main()
