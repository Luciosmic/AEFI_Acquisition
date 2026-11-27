# Registre des travaux

Ce qui se fait en parallèle sur ce vault, et ce qui attend.
Le serveur du registre est le seul écrivain : ne l'édite pas à la main une fois qu'il l'a repris.

## En cours

- **2026-11-27 18:20 — Accélérer la boucle d'acquisition logicielle.** Repos : aefi-acquisition. Trace : `AEFI_Acquisition_dev\_system\ops\traces\2026-11-27-accelerer-la-boucle-d-acquisition/`. Session : `ba41e867-56a6-41db-bf6f-2257fc382482`.
  État : Première tranche : journal d'audit écrit par un fil dédié (fichier tenu ouvert), n_avg relu seulement si mcu_last_config.json change. Mesuré en simulation : 1,9 ms par point sur ~4 ms d'écart.
  Éviter : `src/infrastructure/events/event_audit_log.py`, `src/infrastructure/hardware/ads131a04/adapter_i_acquistion_port_ads131a04/`.

## En attente
