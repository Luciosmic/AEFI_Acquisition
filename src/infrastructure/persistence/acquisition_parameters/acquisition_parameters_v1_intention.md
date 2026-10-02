# acquisition_parameters_v1 — Intention

## Rationale

Le document `acquisition-parameters.json` 1.0 est écrit par plusieurs
acquisitions : scan pas-à-pas, série temporelle, balayage de débit MCU. Ses
sections communes — provenance, composants et leurs réglages, montage du
capteur, détection synchrone, liaison série, positions du banc, fichiers
produits — ont la même mise en page et les mêmes unités pour toutes. Écrites
une fois par export, elles divergeraient au premier changement du schéma
(deux unités pour un même réglage, deux noms pour une même clé) : un même
fait, deux formes, et des scripts d'analyse qui doivent connaître les deux.

## Responsibility

- Écrire, à partir des DTO partagés (`application/shared/acquisition_parameters/`),
  les sections communes du schéma 1.0 : `provenance`, `feature_of_interest`,
  `components` (catalogue, réglages ADC et AD9106), `host_link`,
  `deployment` du capteur, état de la détection synchrone, `positioning_state`,
  `data.files` (+ colonnes fournies par l'appelant).
- Tenir la liste unique d'avertissements (`new_warnings`) et la traduction des
  unités du catalogue en UCUM (`ucum`, `UCUM_UNITS`).

## Design

- Fonctions pures, sans I/O ; entrée = DTO sans format, sortie = `dict` prêt
  pour JSON. Contrat : `application/services/scan_export_service/acquisition_parameters/acquisition_parameters_intention.md`.
- Chaque export garde son propre sérialiseur, qui n'ajoute que ce que son
  acquisition a fait (procédure, état de l'excitation, flux, colonnes) — ex.
  `acquisition_throughput/acquisition_parameters_v1_serializer.py`.
- Ce qui varie d'un export à l'autre est passé en paramètre, jamais deviné :
  `state_read` (quand l'état de l'AD9106 a été lu), `applies_to_data` (la
  rotation est-elle appliquée aux valeurs exportées ?), `motors_held`,
  `absent_because`.
- Extrait le 2026-10-02 du sérialiseur du balayage de débit, à sortie
  identique (seuls deux messages d'avertissement disent désormais
  « acquisition » au lieu de « balayage »).
