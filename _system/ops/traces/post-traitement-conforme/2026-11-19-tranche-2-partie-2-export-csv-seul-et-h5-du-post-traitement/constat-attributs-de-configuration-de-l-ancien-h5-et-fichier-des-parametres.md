---
doc_type: constat
type: constat::sh-agent-os
genere_par: "[[tache - tranche 2 partie 2 export csv seul et h5 du post traitement]]"
---

# Les attributs de configuration de l'ancien `.h5` sont-ils dans le fichier des paramètres ?

**Verdict : oui pour les scans pas à pas et à la volée, non pour les scans en ligne.** Aucune modification du fichier de paramètres n'est nécessaire pour les deux premiers ; le scan en ligne n'est pas un nouveau manque (voir plus bas). Vérifié le 2026-11-19 sur `summarize_scan_config` (ce que l'ancien port HDF5 écrivait en attributs de racine, avec `scan_id`) et sur le sérialiseur du schéma.

| Attribut de l'ancien `.h5` | Où il est dans le fichier des paramètres |
|---|---|
| `scan_id` | `provenance.activity.id` |
| `pattern`, `scan_axis` | `procedure.<kind>.pattern`, `procedure.<kind>.fast_axis` |
| `fly_scan` | `procedure.fly_scan` ou `procedure.step_scan` (et `provenance.activity.kind`) |
| `x_min`, `x_max`, `y_min`, `y_max` | `procedure.<kind>.zone` |
| `x_nb_points`, `y_nb_points`, `total_points` | `procedure.<kind>.grid` |
| `stabilization_delay_ms` | `procedure.<kind>.stabilization_delay` |
| `averaging_per_position`, `estimated_duration_s` | `procedure.step_scan` seulement : le scan à la volée les déclare « non pertinents » (pas de moyennage, pas d'estimation), l'ancien `.h5` y écrivait les valeurs du gabarit sans sens |

## Le scan en ligne n'est pas couvert, et ne l'était déjà pas

- L'ancien `.h5` d'un scan en ligne portait `scan_kind: line`, `center_x/y`, `length_mm`, `theta_deg`, `start_*`, `end_*`. Le fichier des paramètres n'a aucun champ pour cette géométrie.
- `ScanExportService._scan_procedure` rend `None` pour un scan en ligne, et le sérialiseur appelle alors `_grid(None)` : `AttributeError: 'NoneType' object has no attribute 'x_min_mm'` (reproduit hors export). Le gestionnaire de `ScanStarted` attrape l'erreur : l'export d'un scan en ligne ne s'ouvre pas, avant comme après ce changement. Le post-traitement ne sait pas non plus traiter une ligne (le constructeur de grille attend deux axes).
- Ce n'est pas une régression de la tranche 2. Si l'humain veut exporter les scans en ligne, c'est un besoin à ajouter au contrat client-fournisseur (une procédure `line_scan` dans le schéma, version mineure), et au post-traitement.

## Ce que le `.h5` du post-traitement garde en plus

Les points bruts relus du CSV (`raw_scan`), la source (CSV, SHA-256, activité, empreinte déclarée, égalité des deux) : décrits dans `hdf5_step_writer_intention.md`. Le `.h5` ne recopie aucun attribut de configuration : on les lit dans le fichier des paramètres, à côté.
