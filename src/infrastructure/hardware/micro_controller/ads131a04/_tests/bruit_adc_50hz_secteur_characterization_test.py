"""
Recherche d'une composante a 50 Hz (secteur) dans le bruit ADC pur (ADS131A04), canaux non pilotes.

Pourquoi : lever une partie de la dette D5 ("origine de la composante non blanche -- captation
secteur, boucle de masse, alimentation de l'electronique de conditionnement... -- rien dans ces
donnees ne la renseigne") en cherchant si le bruit du canal 5 (circuit ouvert) et du canal 6
(court-circuite) contient une raie a 50 Hz. Une raie nette orienterait vers une origine amont
(captation ambiante du secteur) plutot qu'un bruit intrinseque a l'ADC ; son absence ne l'exclut
pas mais ne la corrobore pas non plus.

Montage (deja fait par l'operateur, ce script ne le modifie pas) :
- Canal 5 (Z in-phase)   : entree en circuit ouvert (rien de connecte)
- Canal 6 (Z quadrature) : entree court-circuitee (pattes differentielles reliees)
- Canaux 1-4 (X in-phase/quadrature, Y in-phase/quadrature) : capteur reel branche (acquis pour
  ne pas casser le flux 6 canaux de l'event, mais pas analyses ici -- hors scope de cette recherche)

Contrainte de debit (deja etablie, pas une nouvelle reconnaissance) : acquire_sample() appele en
boucle directe plafonne a quelques Hz -- inutilisable pour une FFT a 50 Hz. Ce script utilise donc
l'acquisition CONTINUE (meme mecanisme que la caracterisation du debit MCU du 2026-10-02, qui a
mesure ~109 echantillons/s a OSR 4096, n_avg=1, latence USB 1 ms) : AdapterAefiAcquisitionAds131a04
publie un event domain AefiVoltageSampleAcquired par echantillon sur IDomainEventBus (topic
"aefivoltagesampleacquired"), chaque event portant sample.timestamp (horodatage reel).

Deviation deliberee par rapport a MCUCompositionRoot : ce script instancie directement
MCU_SerialCommunicator / ADS131A04Adapter / ADS131Controller / AdapterAdcOversamplingAds131a04 /
AdapterAefiAcquisitionAds131a04, plutot que de passer par MCUCompositionRoot.lifecycle.initialize_all().
Raison : initialize_all() reapplique et PERSISTE la config DDS (excitation) et re-ecrit
mcu_last_config.json a chaque connexion -- effets de bord inutiles et hors scope pour une mesure de
bruit ADC pur. n_avg=1 est injecte directement via n_avg_reader=lambda: 1 (meme technique que
continuous_acquisition_sequence_test.py et bruit_court_circuit_vs_osr_characterization_test.py, meme
dossier) pour ne jamais lire/ecrire mcu_last_config.json (qui vaut actuellement n_avg=127 pour un
usage sans rapport). L'OSR materiel (4096) et le gain/Vref logiciels (1 / 2.442 V) sont fixes
explicitement par ce script plutot que supposes herites de ads131a04_last_config.json, meme s'ils y
sont deja identiques au moment ou ce script est ecrit -- pour que la mesure reste correcte si cette
config change entre-temps.

Scope : script de caracterisation ponctuelle, PAS du code de production, PAS une nouvelle couche DDD.
Modele sur bruit_court_circuit_vs_osr_characterization_test.py et continuous_acquisition_sequence_test.py
(meme dossier). N'a aucune fonction nommee test_*, donc pytest (qui collecte par prefixe de fonction,
pas seulement par nom de fichier) ne ramasse rien depuis ce fichier malgre son suffixe _test.py --
meme convention que les deux fichiers modeles.

Limite physique assumee : a Fs mesure ~109 Hz, la frequence de Nyquist (~54.5 Hz) est tres proche de
50 Hz. SEULE la fondamentale a 50 Hz est dans la bande observable -- les harmoniques (100, 150 Hz)
sont hors de portee et NE PEUVENT PAS servir a corroborer une hypothese secteur. Si l'echantillonnage
reel s'avere irregulier (ecart-type des intervalles / moyenne au-dela de quelques %), la FFT (qui
suppose un echantillonnage uniforme) perd en validite -- ce script le mesure et le rapporte, sans le
passer sous silence.
"""
import os
import sys
import time
import json
from datetime import datetime, timezone

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import serial.tools.list_ports

# Assuming this file is in src/infrastructure/hardware/micro_controller/ads131a04/_tests/
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../..'))

from infrastructure.hardware.micro_controller.MCU_serial_communicator import MCU_SerialCommunicator
from infrastructure.hardware.micro_controller.ads131a04.adapter_i_acquistion_port_ads131a04 import ADS131A04Adapter
from infrastructure.hardware.micro_controller.ads131a04.ads131_controller import ADS131Controller
from infrastructure.hardware.micro_controller.ads131a04.adapter_adc_oversampling_ads131a04 import (
    AdapterAdcOversamplingAds131a04,
)
from infrastructure.hardware.micro_controller.ads131a04.adapter_aefi_acquisition_ads131a04 import (
    AdapterAefiAcquisitionAds131a04,
)
from application.services.aefi_acquisition_service.ports.i_aefi_acquisition_executor import AefiAcquisitionConfig
from infrastructure.events.in_memory_event_bus import InMemoryEventBus

SELECTED_PORT = "COM10"
BAUDRATE = 1500000
OSR = 4096
REFERENCE_VOLTAGE = 2.442  # V, reference interne -- meme valeur que les caracterisations precedentes
GAIN = 1
N_AVG = 1  # moyennage logiciel MCU, fixe via n_avg_reader (jamais via mcu_last_config.json)
SETTLE_DELAY_S = 0.05  # meme valeur par defaut que les scripts precedents

TARGET_N_SAMPLES = 2000  # ~18 s a 109 Hz -- ajuste a la fin si le Fs reel differe
MAX_WAIT_S = 90.0  # garde-fou : arret meme si TARGET_N_SAMPLES n'est pas atteint

MAINS_FREQUENCY_HZ = 50.0
NEIGHBOR_BAND_HALF_WIDTH_HZ = 5.0  # bande [45,55] Hz pour le "bruit de fond local"
EXCLUDE_HALF_WIDTH_HZ = 1.5  # bins exclus autour de 50 Hz pour ne pas polluer le fond avec la raie elle-meme

EXPORT_ROOT = r"C:\Users\manip\Desktop\AEFI_Acquisition_Exports\HARDWARE-CHARACTERIZATION\ADC"
# Pas de copie dans le vault Dropbox : decision manuelle de l'operateur (cf. retour du 2026-10-05),
# jamais un comportement par defaut d'un script. Ecriture directe dans EXPORT_ROOT uniquement.

CHANNELS_OF_INTEREST = (
    # (attribut AefiVoltageMeasurement, cle npz/figure, description)
    ("voltage_z_in_phase", "z_in_phase_circuit_ouvert", "Canal 5 (Z in-phase, circuit ouvert)"),
    ("voltage_z_quadrature", "z_quadrature_court_circuit", "Canal 6 (Z quadrature, court-circuit)"),
)
# Canaux 1-4 (capteur reel) acquis dans le meme event mais non analyses ici -- hors scope.
ALL_CHANNEL_ATTRS = (
    "voltage_x_in_phase", "voltage_x_quadrature",
    "voltage_y_in_phase", "voltage_y_quadrature",
    "voltage_z_in_phase", "voltage_z_quadrature",
)


def build_adc_config() -> dict:
    """Config logicielle pour acquire_sample() : gain=1 tous canaux, Vref=2.442V, OSR=4096.
    N'ecrit rien dans le materiel (voir load_config dans ADS131A04Adapter) ; seul set_oversampling_ratio
    ci-dessous ecrit reellement le registre OSR."""
    return {
        "channels": {str(ch): {"gain": GAIN} for ch in range(1, 7)},
        "oversampling_ratio": OSR,
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

    # n_avg_reader fixe a 1 : pas de moyennage logiciel MCU, jamais via mcu_last_config.json
    # (qui vaut actuellement n_avg=127 pour un usage sans rapport avec cette mesure).
    acquisition_port = ADS131A04Adapter(communicator, n_avg_reader=lambda: N_AVG)
    controller = ADS131Controller(communicator)
    oversampling_port = AdapterAdcOversamplingAds131a04(controller)
    event_bus = InMemoryEventBus()
    executor = AdapterAefiAcquisitionAds131a04(event_bus)

    collected_events = []

    def on_sample(event):
        collected_events.append(event)

    event_bus.subscribe("aefivoltagesampleacquired", on_sample)

    start_utc = datetime.now(timezone.utc)
    osr_write_ok = False
    try:
        print(f"\nEcriture OSR={OSR}...")
        written = oversampling_port.set_oversampling_ratio(OSR)
        if written.is_failure:
            print(f"  OSR {OSR} non ecrit : {written.error} -- la mesure continue avec l'OSR deja actif")
        else:
            osr_write_ok = True
            print(f"  OSR {OSR} ecrit.")
        time.sleep(SETTLE_DELAY_S)

        acquisition_port.load_config(build_adc_config())

        print(f"\nDemarrage acquisition continue (cible {TARGET_N_SAMPLES} echantillons, "
              f"garde-fou {MAX_WAIT_S} s)...")
        config = AefiAcquisitionConfig(max_duration_s=MAX_WAIT_S)
        wait_start = time.time()
        executor.start(config, acquisition_port)

        last_report = 0
        while len(collected_events) < TARGET_N_SAMPLES and (time.time() - wait_start) < MAX_WAIT_S:
            time.sleep(0.5)
            if len(collected_events) - last_report >= 200:
                print(f"  ... {len(collected_events)} echantillons recus")
                last_report = len(collected_events)

        print(f"Arret demande apres {len(collected_events)} echantillons "
              f"({time.time() - wait_start:.1f} s ecoulees).")
    finally:
        executor.stop()
        print("Deconnexion...")
        communicator.disconnect()

    end_utc = datetime.now(timezone.utc)

    n = len(collected_events)
    if n < 10:
        print(f"\nTrop peu d'echantillons ({n}) pour une analyse -- abandon.")
        return

    # --- Horodatage reel : Fs effectif + regularite ---
    timestamps = [e.sample.timestamp for e in collected_events]
    t0 = timestamps[0]
    t_seconds = np.array([(t - t0).total_seconds() for t in timestamps], dtype=float)
    intervals = np.diff(t_seconds)
    mean_interval_s = float(np.mean(intervals))
    std_interval_s = float(np.std(intervals))
    irregularity_ratio = std_interval_s / mean_interval_s if mean_interval_s > 0 else float("nan")
    fs_effective_hz = 1.0 / mean_interval_s if mean_interval_s > 0 else float("nan")
    nyquist_hz = fs_effective_hz / 2.0
    total_duration_s = float(t_seconds[-1] - t_seconds[0])

    print("\n--- Horodatage reel ---")
    print(f"n = {n} echantillons sur {total_duration_s:.2f} s")
    print(f"Fs effectif (moyen) = {fs_effective_hz:.3f} Hz  (intervalle moyen {mean_interval_s * 1e3:.2f} ms)")
    print(f"Ecart-type des intervalles = {std_interval_s * 1e3:.3f} ms")
    print(f"Irregularite (sigma/moyenne) = {irregularity_ratio * 100:.2f} %")
    irregularity_warning = irregularity_ratio > 0.05
    if irregularity_warning:
        print("ATTENTION : irregularite > 5 % -- l'hypothese d'echantillonnage uniforme sous-jacente a "
              "la FFT est affaiblie. Les resultats frequentiels ci-dessous doivent etre lus avec cette "
              "reserve.")
    else:
        print("Irregularite <= 5 % -- hypothese d'echantillonnage uniforme raisonnable pour cette FFT.")

    print(f"Nyquist (Fs/2) = {nyquist_hz:.3f} Hz")
    if nyquist_hz < MAINS_FREQUENCY_HZ:
        print(f"ATTENTION : Nyquist ({nyquist_hz:.2f} Hz) < 50 Hz -- la fondamentale secteur est elle-meme "
              "hors de portee de ce Fs. Aucune conclusion sur le secteur n'est possible depuis ces donnees.")
    elif nyquist_hz < MAINS_FREQUENCY_HZ + 10:
        print(f"Nyquist ({nyquist_hz:.2f} Hz) proche de 50 Hz : seule la fondamentale a 50 Hz est dans la "
              "bande observable. Les harmoniques (100 Hz, 150 Hz) sont hors de portee et NE PEUVENT PAS "
              "servir a corroborer une hypothese secteur -- seule la fondamentale est testee ici.")

    # --- FFT canaux 5 et 6 ---
    results = {}
    for attr, key, description in CHANNELS_OF_INTEREST:
        values = np.array([getattr(e.sample, attr) for e in collected_events], dtype=float)
        values_detrended = values - np.mean(values)
        spectrum = np.fft.rfft(values_detrended)
        freqs = np.fft.rfftfreq(n, d=mean_interval_s)
        magnitude = np.abs(spectrum)

        if freqs[-1] < MAINS_FREQUENCY_HZ:
            print(f"\n{description} : bande observable ([0, {freqs[-1]:.2f}] Hz) n'atteint pas 50 Hz -- "
                  "test 50 Hz impossible pour ce canal avec ce Fs.")
            results[key] = {"test_50hz_possible": False}
            continue

        idx_50 = int(np.argmin(np.abs(freqs - MAINS_FREQUENCY_HZ)))
        freq_50_actual = float(freqs[idx_50])
        level_50 = float(magnitude[idx_50])

        neighbor_mask = (
            (freqs >= MAINS_FREQUENCY_HZ - NEIGHBOR_BAND_HALF_WIDTH_HZ)
            & (freqs <= MAINS_FREQUENCY_HZ + NEIGHBOR_BAND_HALF_WIDTH_HZ)
            & (np.abs(freqs - MAINS_FREQUENCY_HZ) > EXCLUDE_HALF_WIDTH_HZ)
        )
        if not np.any(neighbor_mask):
            # Bande trop etroite compte tenu de la resolution frequentielle (Fs/n) -- repli sur tous les
            # bins sauf celui a 50 Hz et son voisin immediat.
            neighbor_mask = np.ones_like(freqs, dtype=bool)
            neighbor_mask[max(0, idx_50 - 1):idx_50 + 2] = False
        local_floor = float(np.mean(magnitude[neighbor_mask])) if np.any(neighbor_mask) else float("nan")

        ratio = level_50 / local_floor if local_floor > 0 else float("nan")
        ratio_db = 20 * np.log10(ratio) if ratio > 0 else float("nan")

        print(f"\n{description} :")
        print(f"  Bin le plus proche de 50 Hz : {freq_50_actual:.3f} Hz (resolution {freqs[1] - freqs[0]:.3f} Hz)")
        print(f"  Niveau au bin 50 Hz = {level_50:.3e} V")
        print(f"  Bruit de fond local (bande +/-{NEIGHBOR_BAND_HALF_WIDTH_HZ} Hz, hors +/-{EXCLUDE_HALF_WIDTH_HZ} Hz "
              f"autour de 50 Hz) = {local_floor:.3e} V")
        print(f"  Facteur niveau_50Hz / fond_local = {ratio:.2f}x ({ratio_db:+.1f} dB)")

        results[key] = {
            "test_50hz_possible": True,
            "freq_50hz_bin_hz": freq_50_actual,
            "level_50hz_v": level_50,
            "local_floor_v": local_floor,
            "ratio": ratio,
            "ratio_db": ratio_db,
            "freqs": freqs,
            "magnitude": magnitude,
        }

    # --- Sauvegarde ---
    timestamp_label = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    folder_name = f"{timestamp_label}_bruit-adc-ads131a04-50hz-secteur-ouvert-vs-court-circuit"
    file_prefix = f"{timestamp_label}_bruit-adc-50hz"
    destination_dir = os.path.join(EXPORT_ROOT, folder_name)
    os.makedirs(destination_dir, exist_ok=True)

    # npz : toutes les valeurs brutes + timestamps reels (secondes depuis le premier echantillon) +
    # les 6 canaux (pas seulement 5/6) pour que la donnee brute reste exploitable au-dela de ce script.
    npz_payload = {"t_seconds": t_seconds}
    for attr in ALL_CHANNEL_ATTRS:
        npz_payload[attr] = np.array([getattr(e.sample, attr) for e in collected_events], dtype=float)
    npz_path = os.path.join(destination_dir, f"{file_prefix}_echantillons-bruts.npz")
    np.savez(npz_path, **npz_payload)

    conditions_path = os.path.join(destination_dir, f"{file_prefix}_conditions.json")
    with open(conditions_path, "w", encoding="utf-8") as f:
        json.dump({
            "debut_utc": start_utc.isoformat(),
            "fin_utc": end_utc.isoformat(),
            "port_serie": SELECTED_PORT,
            "baudrate": BAUDRATE,
            "n_echantillons_cible": TARGET_N_SAMPLES,
            "n_echantillons_obtenus": n,
            "n_avg_logiciel_mcu": N_AVG,
            "oversampling_ratio": OSR,
            "osr_ecrit_avec_succes": osr_write_ok,
            "reference_voltage_V": REFERENCE_VOLTAGE,
            "gain_tous_canaux": GAIN,
            "fs_effectif_hz": fs_effective_hz,
            "intervalle_moyen_s": mean_interval_s,
            "intervalle_sigma_s": std_interval_s,
            "irregularite_ratio": irregularity_ratio,
            "nyquist_hz": nyquist_hz,
            "duree_totale_s": total_duration_s,
            "canal_1_x_in_phase": "capteur reel",
            "canal_2_x_quadrature": "capteur reel",
            "canal_3_y_in_phase": "capteur reel",
            "canal_4_y_quadrature": "capteur reel",
            "canal_5_z_in_phase": "circuit ouvert (rien de connecte)",
            "canal_6_z_quadrature": "court-circuit (pattes differentielles reliees)",
            "script": os.path.relpath(__file__, start=os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..")),
        }, f, indent=2, ensure_ascii=False)

    # Figure : spectres canaux 5 et 6, ligne verticale a 50 Hz.
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    for ax, (attr, key, description) in zip(axes, CHANNELS_OF_INTEREST):
        res = results.get(key, {})
        if not res.get("test_50hz_possible"):
            ax.set_title(f"{description} -- test 50 Hz impossible (bande observable insuffisante)")
            continue
        freqs = res["freqs"]
        magnitude = res["magnitude"]
        ax.semilogy(freqs, magnitude, linewidth=0.8)
        ax.axvline(MAINS_FREQUENCY_HZ, color="red", linestyle="--", linewidth=1,
                   label=f"50 Hz (bin reel {res['freq_50hz_bin_hz']:.2f} Hz)")
        ax.axvline(nyquist_hz, color="gray", linestyle=":", linewidth=1, label=f"Nyquist ({nyquist_hz:.1f} Hz)")
        ax.set_title(f"{description} -- niveau_50Hz/fond_local = {res['ratio']:.2f}x ({res['ratio_db']:+.1f} dB)")
        ax.set_ylabel("Amplitude FFT (V)")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, which="both", alpha=0.3)
    axes[-1].set_xlabel("Frequence (Hz)")
    fig.suptitle(f"Spectre canaux 5/6 -- Fs effectif={fs_effective_hz:.2f} Hz, n={n}, "
                 f"irregularite={irregularity_ratio * 100:.2f} %")
    fig.tight_layout()
    png_path = os.path.join(destination_dir, f"{file_prefix}_spectre-canaux-5-6.png")
    fig.savefig(png_path, dpi=150)
    plt.close(fig)

    print(f"\nFichiers ecrits dans {destination_dir} :")
    print(f"  {os.path.basename(npz_path)}")
    print(f"  {os.path.basename(conditions_path)}")
    print(f"  {os.path.basename(png_path)}")

    print("\n--- Resume ---")
    print(f"Fs effectif = {fs_effective_hz:.3f} Hz, irregularite = {irregularity_ratio * 100:.2f} %, "
          f"Nyquist = {nyquist_hz:.3f} Hz")
    for attr, key, description in CHANNELS_OF_INTEREST:
        res = results.get(key, {})
        if res.get("test_50hz_possible"):
            print(f"{description} : niveau_50Hz/fond_local = {res['ratio']:.2f}x ({res['ratio_db']:+.1f} dB)")
        else:
            print(f"{description} : test 50 Hz impossible (bande observable insuffisante)")


if __name__ == "__main__":
    main()
