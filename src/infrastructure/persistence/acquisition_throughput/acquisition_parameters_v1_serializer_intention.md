# acquisition_parameters_v1_serializer — Intention

## Rationale

Le 2026-10-02, deux balayages de débit MCU exportés n'ont pas pu être remis
dans leur contexte : latence USB du COM10 (16 ms ou 1 ms — T₀ passe de
23,6 ms à 7,6 ms), flux démarré à la main ou par le balayage, état des voies
de référence DDS3/DDS4, position du banc, version du logiciel. L'opérateur a
dû tout reconstituer depuis le journal d'événements.

Le document doit suivre le schéma partagé `acquisition-parameters.json` 1.0
(contrat : `scan_export_service/acquisition_parameters/acquisition_parameters_intention.md`),
pas un second format. Sa mise en page, ses codes d'unités et ses
descriptions de colonnes changent quand le **format de fichier** change —
pas quand le use case change. Placée dans le service, cette correspondance
forcerait à modifier l'application à chaque version du schéma ; dispersée
dans les adaptateurs de lecture, elle serait introuvable le jour où un
constructeur partagé (scan, série temporelle, débit) la remplacera. D'où un
module unique, à côté de l'écrivain du fichier, remplaçable d'un bloc.

## Responsibility

- `serialize_acquisition_parameters_v1(parameters, generated_at)` : le
  document 1.0 d'un balayage, prêt pour JSON — provenance PROV (activité,
  logiciel, opérateur), objet mesuré (absent, déclaré), procédure,
  composants (catalogue + réglages appliqués), chaîne de mesure, fichiers
  produits et colonnes, liste unique d'avertissements.
- Traduire les unités du catalogue en codes UCUM ; toute unité inconnue est
  écrite en annotation **et** signalée.
- Déclarer chaque inconnu dans `warnings` (`path` + `message`) : jamais une
  omission silencieuse.
- `COLUMNS` : sens, repère et unité de chaque colonne de `summary.csv` et
  `samples.csv` (le test de l'export vérifie qu'aucune colonne écrite n'est
  sans description).

## Design

- Depuis le 2026-10-02, les sections communes à toute acquisition
  (provenance, composants, montage du capteur, détection synchrone, liaison
  série, positions, fichiers) viennent de
  `infrastructure/persistence/acquisition_parameters/acquisition_parameters_v1.py`,
  partagé avec l'export des scans et séries temporelles. Ce module n'ajoute
  que ce que le balayage a fait : procédure, `n_avg` balayé, excitation
  coupée, origine du flux, colonnes de `summary.csv` / `samples.csv`.
- Fonction pure, sans I/O : entrée = `AcquisitionParametersDTO` (sans
  format), sortie = `dict`. L'écriture et l'empreinte des fichiers sont
  faites par `CsvAcquisitionThroughputExportPort`.
- Unicité : chaque fait à une place. L'état de l'excitation et de la
  détection synchrone (`lock_in_enabled`, `phase_offset`) se déduit des
  réglages de l'AD9106 → `derived_from`. `n_avg` du microcontrôleur renvoie
  à la grille de la procédure. Les résultats (T₀, ODR, `n_avg` recommandé)
  restent dans `summary.csv`, pas ici.
- Ce qui n'est pas du format vient des DTO : la définition de la condition
  d'excitation (« coupée ») est fournie par le service qui l'applique.
- Grandeurs `{value, unit}` (UCUM) ; codes registres `{code, unit}` (+
  `value` physique pour la phase, conversion du domaine `PhaseAngle`). Les
  gains ADC sont écrits en valeur (1–16), pas en code registre : l'encodage
  registre ne vit qu'à l'ACL (adaptateur ADS131A04).
- Dates ISO 8601 avec décalage (heure locale).
- `UCUM_UNITS` : la liste fermée des unités écrites ; le test garde-fou
  refuse toute autre unité et toute grandeur numérique sans unité.

### Extensions au schéma 1.0 (à proposer au propriétaire du schéma)

- `provenance.activity.kind` : `mcu_throughput_characterization`.
- `provenance.activity.exclusive_control` : propriétaire et contrôles tenus
  (excitation, flux d'acquisition, configuration avancée `mcu` / `ads131a04`).
- `provenance.software.version`, `provenance.software.hardware_backends`
  (réel / simulé par sous-système ; simulé → avertissement).
- `feature_of_interest.present: false` : absence déclarée, pas omise.
- `procedure.mcu_throughput_characterization` : `n_avg_grid` (quantité à
  valeur liste), `samples_per_point`, `settle_delay`, `point_timeout`,
  `excitation`.
- Caractérisation en courbe (débit vs `n_avg`) : `{abscissa, ordinate}`,
  chacun `{value: [...], unit}`.
- `components.adc.settings.channels.N.digital_gain` (au lieu de `gain`),
  `components.signal_generation_chip.settings.channels.N.constant`,
  `link_dds3_dds4_gain`, `state_read`.
- `components.microcontroller.settings` : `n_avg` balayé (`derived_from`),
  `n_avg_before_activity`, `n_avg_restored_after_activity`, `host_link`
  (`serial_port`, `baud_rate`, `usb_latency_timer` + source).
- `measurement_chain.excitation.state` : `applied`, `definition`,
  `operator_setting` (mode, niveaux), `operator_setting_restored_after_activity`.
- `measurement_chain.digitization.stream` : `origin`
  (`started_by_activity` | `already_running`), `stopped_after_activity`.
- `measurement_chain.positioning.state` : position début / fin,
  `motors_held_by_activity`.
- `measurement_chain.sensor.deployment.rotation_applied.applies_to_data`.
- `data.files[]` : `byte_size`, `sha256`, `was_generated_by` ; le document
  lui-même listé sans empreinte.
- `data.columns.timestamp` : `format` au lieu de `unit` (une date n'a pas
  d'unité UCUM).
