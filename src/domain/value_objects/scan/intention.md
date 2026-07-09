# Valeurs Objets — Scan

## Rationale
Ce dossier regroupe les valeurs objets domaine liés au scan spatial 2D. Ces types immuables portent les données de configuration, de progression et de trajectoire du scan sans aucune logique d'infrastructure.

## Responsibility
- `ScanZone` : définir les bornes rectangulaires 2D (x_min/max, y_min/max en mm) avec validation contre les limites physiques du banc (1200 mm × 1200 mm).
- `StepScanConfig` : encapsuler la configuration complète d'un scan pas-à-pas (zone, nombre de points X/Y, pattern, délai de stabilisation, nombre de moyennages, incertitude maximale requise). Fournit `total_points()` et `estimated_duration_seconds()`.
- `ScanProgress` : snapshot immuable de la progression en cours (point courant, ligne courante, temps écoulé, temps restant estimé). Fournit `percentage()` et `is_complete()`.
- `ScanTrajectory` : séquence ordonnée et immuable de `Position2D` générée par `ScanTrajectoryFactory`. Itérable et indexable.

## Design
- Tous les types sont des dataclasses `frozen=True` : immuables, égalité par valeur.
- La validation des invariants se fait dans `__post_init__` pour garantir qu'aucun objet invalide n'existe.
- `ScanZone` hardcode temporairement les limites physiques (MVP) ; un TODO documente l'injection future depuis `TestBench`.
