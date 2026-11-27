# Registre des travaux

Ce qui se fait en parallèle sur ce vault, et ce qui attend.
Le serveur du registre est le seul écrivain : ne l'édite pas à la main une fois qu'il l'a repris.

## En cours

- **2026-11-27 17:45 — Afficher le débit de sortie ADC.** Repos : aefi-acquisition. Trace : `AEFI_Acquisition_dev\_system\ops\traces\2026-11-27-afficher-le-debit-de-sortie-de-l-adc/`. Session : `ba41e867-56a6-41db-bf6f-2257fc382482`.
  État : Panneau de configuration avancée ADS131A04 : ajout du débit de sortie calculé (f_MOD / OSR) et de la fréquence du modulateur, en lecture seule.
  Éviter : `src/interface/widgets/panels/hardware_advanced_config_panel.py`, `src/infrastructure/hardware/ads131a04/ads131a04_advanced_configurator/`.

## En attente
