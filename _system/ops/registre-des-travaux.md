# Registre des travaux

Ce qui se fait en parallèle sur ce vault, et ce qui attend.
Le serveur du registre est le seul écrivain : ne l'édite pas à la main une fois qu'il l'a repris.

## En cours

- **2026-11-27 18:20 — Accélérer la boucle d'acquisition logicielle.** Repos : aefi-acquisition. Trace : `AEFI_Acquisition_dev\_system\ops\traces\2026-11-27-accelerer-la-boucle-d-acquisition/`. Session : `ba41e867-56a6-41db-bf6f-2257fc382482`.
  État : Tranche 1 commitée : journal d'audit par fil écrivain, n_avg en mémoire. Simulation : 1,9 -> 0,17 ms par point. Reste ~2 ms à mesurer au banc (lecture série, abonnés du scan). Attente : mesure de débit au banc.
  Éviter : `src/infrastructure/hardware/micro_controller/mcu_serial_communicator.py`, `src/infrastructure/hardware/ads131a04/adapter_aefi_acquisition_ads131a04/`.

## En attente
