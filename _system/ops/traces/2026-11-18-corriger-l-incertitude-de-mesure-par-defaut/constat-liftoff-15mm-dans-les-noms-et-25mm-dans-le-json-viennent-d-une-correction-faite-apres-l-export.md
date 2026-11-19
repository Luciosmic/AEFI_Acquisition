---
doc_type: constat
statut: to_validate
---

# Le scan du 2026-11-16 : `liftoff-15mm` dans les noms, 25 mm dans le JSON

Enquête en lecture seule, rien n'a été corrigé. Réponse de l'opérateur (2026-11-19) : le lift-off réel était de **25 mm** ; 15 mm a été saisi par erreur dans l'interface au lancement du scan. Le `25.0` du JSON est donc la bonne valeur, les noms de fichiers en `15mm` sont faux.

## Verdict

Le logiciel ne peut pas produire cet écart. Il a écrit `15` partout ; le `25` vient d'une correction faite après l'export, à la main.

## Ce que le logiciel fait

- Le nom (`acquisition_name`) et la valeur de `feature_of_interest` viennent du même champ `lift_off_mm` de la même config d'export (`self._config`), lue dans le même gestionnaire `_handle_scan_started` (`scan_export_service.py:287` et `:297`, qui appelle `_start_parameters` puis `:617`).
- La config est figée par `configure_export` avant le départ du scan. Les deux ne peuvent donc pas diverger dans une même exécution.
- Le radical du nom n'est jamais mis à jour après le départ : le nom d'une acquisition ne bouge plus.

## Ce que les fichiers montrent

| Indice | Lecture |
|---|---|
| `data.files[*].name` du JSON : tous en `liftoff-15mm`, le `.h5` compris | le logiciel a écrit 15 partout |
| `source_csv` dans le `.h5` : chemin du laboratoire `...\WATER\2026-11-16_175822_..._liftoff-15mm\...` | le dossier d'origine s'appelait bien `liftoff-15mm` |
| `aefi.csv` et `column-stabilization.csv` : empreintes identiques à celles du JSON | ces fichiers n'ont pas été touchés |
| `.h5` : empreinte différente de celle du JSON, nom et dossier en `25mm`, écrit le 2026-11-18 à 18:12-18:13 | le `.h5` a été réécrit (post-traitement) puis renommé |
| JSON : `feature_of_interest...value = 25.0`, modifié le 2026-11-18 à 20:12, après le renommage du `.h5` | la valeur 25 a été saisie après coup |

Ce qui reste une déduction : l'édition à la main du JSON et du nom. Aucun journal du logiciel ne la porte.

## Proposition (sans code)

1. Valeur juste : 25 mm (dite par l'opérateur le 2026-11-19).
2. La correction se range dans un repo de données avec une note qui garde les deux valeurs, 15 (saisie à l'export) et la valeur corrigée, et la raison. Le dossier `0_inbox/data-a-interpreter/` n'est pas modifié.
3. Pour éviter que cela revienne, la carte des contextes pose la règle : la source de vérité est `feature_of_interest` du JSON ; renommer un dossier ou un fichier casse sa correspondance avec `data.files[*].name`, donc toute correction passe par un fichier qui le dit.
4. Pas de changement du logiciel : il est cohérent. Un champ « corriger le lift-off après coup » serait une nouvelle fonction, à décider à part.
