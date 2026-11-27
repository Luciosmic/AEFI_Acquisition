# Registre des travaux

Ce qui se fait en parallèle sur ce vault, et ce qui attend.
Le serveur du registre est le seul écrivain : ne l'édite pas à la main une fois qu'il l'a repris.

## En cours

- **2026-11-27 18:20 — Accélérer la boucle d'acquisition logicielle.** Repos : aefi-acquisition. Trace : `AEFI_Acquisition_dev\_system\ops\traces\2026-11-27-accelerer-la-boucle-d-acquisition/`. Session : `ba41e867-56a6-41db-bf6f-2257fc382482`.
  État : Mesuré au banc : application à n_avg=1, 7,13 -> 5,01 ms par point (adaptateur seul 4,89). Vue de lecture continue : redessin limité à 25/s (minuteur). Reste : protocole série (2 lignes par point).
  Éviter : `src/interface/widgets/panels/aefi_continuous_reading_panel.py`, `src/infrastructure/hardware/micro_controller/mcu_serial_communicator.py`.

- **2026-11-27 19:12 — Signe quadrature et unité de conversion.** Repos : aefi-acquisition. Trace : `AEFI_Acquisition_dev\_system\ops\traces\signe-de-la-quadrature-et-unite-de-conversion/`. Session : `e782ef82-a9e2-43a8-8b9b-7e6db3577e17`.
  État : Tranche 1 codée et testée (regroupement « Unité de conversion » dans Calibration > Électronique, signe de la quadrature déclaré sur la carte de conditionnement, unité « 1 » à l'export). Reste : essai par l'humain, puis tranche 2 (appliquer le signe à la lecture de l'ADC).
  Éviter : `src/domain/test_bench_configuration/value_objects/hardware_component_kind/`, `src/interface/widgets/panels/calibration_panel.py`.

## En attente
