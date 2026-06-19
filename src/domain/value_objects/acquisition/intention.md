# Valeurs Objets — Acquisition

## Rationale
Ce dossier contient les valeurs objets domaine représentant les données brutes issues du capteur électromagnétique. Ils constituent le langage ubiquitaire du domaine pour les données de mesure, indépendant du hardware ADC sous-jacent.

## Responsibility
- `VoltageMeasurement` : représenter une mesure de tension complète du capteur à 3 axes (X, Y, Z) en composantes en phase et en quadrature (6 flottants au total), avec un timestamp et une estimation optionnelle d'incertitude. Fournit optionnellement les écarts-types pour les mesures moyennées.
- `AcquisitionSample` : alias de `VoltageMeasurement` pour homogénéité du langage ubiquitaire dans les contextes d'acquisition continue.

## Design
- `VoltageMeasurement` est une dataclass `frozen=True` : immuable, égalité par valeur, sérialisable.
- Les noms des champs utilisent le vocabulaire domaine (`voltage_x_in_phase`) plutôt que les noms hardware (`adc1_ch1`) ; le mapping est fait dans la couche infrastructure.
- La validation dans `__post_init__` garantit que toutes les composantes de tension sont des flottants finis (rejet de `nan`/`inf`).
