# Registre des travaux

Ce qui se fait en parallèle sur ce vault, et ce qui attend.
Le serveur du registre est le seul écrivain : ne l'édite pas à la main une fois qu'il l'a repris.

## En cours

- **2026-11-27 18:20 — Accélérer la boucle d'acquisition logicielle.** Repos : aefi-acquisition. Trace : `AEFI_Acquisition_dev\_system\ops\traces\2026-11-27-accelerer-la-boucle-d-acquisition/`. Session : `ba41e867-56a6-41db-bf6f-2257fc382482`.
  État : Mesuré au banc : application à n_avg=1, 7,13 -> 5,01 ms par point (adaptateur seul 4,89). Vue de lecture continue : redessin limité à 25/s (minuteur). Reste : protocole série (2 lignes par point).
  Éviter : `src/interface/widgets/panels/aefi_continuous_reading_panel.py`, `src/infrastructure/hardware/micro_controller/mcu_serial_communicator.py`.

- **2026-11-27 19:12 — Signe quadrature et unité de conversion.** Repos : aefi-acquisition. Trace : `AEFI_Acquisition_dev\_system\ops\traces\signe-de-la-quadrature-et-unite-de-conversion/`. Session : `e782ef82-a9e2-43a8-8b9b-7e6db3577e17`.
  État : Tranches 1 et 1 bis faites (unité de conversion, signe déclaré, panneaux « Configuration du banc » et « Calibration » séparés). Attente : essai de l'humain dans l'application, puis tranche 2 (appliquer le signe à la lecture de l'ADC).

- **2026-11-27 19:53 — Publier les drivers avec adaptateurs.** Repos : aefi-acquisition. Plan : `AEFI_Acquisition_dev\_system\ops\traces\2026-11-27-publier-les-drivers-avec-leurs-adaptateurs\plan - publier les drivers avec leurs adaptateurs.md`. Session : `a7fa5e17-d792-4063-824c-dc3e04fc4861`.
  État : Arcus : fusionné dans develop, validé au banc. LIDAR ESP32 : paquet v0.1.0 poussé, banc II migré, AEFI sur feature/drivers-publies (poussée), essai au banc à faire. En cours : LSM9DS1, puis DSO-X 2014A, Narda. AD9106/ADS131A04/MCU reportés.
  Éviter : `src/infrastructure/hardware/esp32_serial_lidar/`, `src/infrastructure/hardware/lsm9ds1/`, `src/infrastructure/hardware/oscilloscope_dsox2014/`, `src/infrastructure/hardware/narda_ep600/`, `pyproject.toml`, `uv.lock`.

## En attente
