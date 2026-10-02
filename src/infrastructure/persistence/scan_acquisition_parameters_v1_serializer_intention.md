# scan_acquisition_parameters_v1_serializer — Intention

## Rationale

Jusqu'au 2026-10-02, le document de paramètres d'un scan (`0.3-agile`) était
mis en page dans un service applicatif et ne partageait rien avec celui du
balayage de débit, déjà au schéma 1.0 : deux formats pour un même contrat,
des réglages exportés sans unité, la rotation « la plus récente » au lieu de
celle appliquée, et ni la version du code, ni le pas moteur, ni la latence
USB. Un scan exporté ne pouvait pas être rejoué à l'identique.

## Responsibility

- `serialize_scan_acquisition_parameters_v1(parameters, generated_at)` : le
  document 1.0 d'un scan pas-à-pas ou d'une série temporelle, prêt pour JSON.
- N'écrit que ce que l'acquisition a fait : procédure du scan, `n_avg`
  appliqué et liaison série, excitation telle que réglée, sonde auxiliaire
  (absente = notée, pas inconnue), positions du banc (le scan tient les
  moteurs ; une série temporelle signale un banc qui a bougé), colonnes.
- `STEP_SCAN_COLUMNS` / `TIME_SERIES_COLUMNS` : sens, axe, repère et unité de
  chaque colonne écrite (fichier principal et fichier de la sonde).

## Design

- Les sections communes (provenance, composants, montage du capteur,
  détection synchrone, liaison série, fichiers) viennent de
  `acquisition_parameters/acquisition_parameters_v1.py`, partagé avec le
  balayage de débit. Contrat : `application/services/scan_export_service/acquisition_parameters/acquisition_parameters_intention.md`.
- Fonction pure, sans I/O. `CsvScanExportPort` l'appelle au démarrage puis
  après la fermeture de tous les fichiers (qu'il liste et hache).
- Tensions exportées dans le repère du capteur : `applies_to_data: false`.
- `ponytail:` aucune saisie de l'objet mesuré ni de l'opérateur encore —
  toujours signalés en avertissement, jamais omis en silence.
