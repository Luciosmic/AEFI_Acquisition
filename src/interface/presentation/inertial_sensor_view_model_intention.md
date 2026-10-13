# inertial_sensor_view_model — Intention

## Rationale

Si le panneau lisait directement l'événement domain, il importerait des types
de `domain/` et connaîtrait les noms de champs, les unités et les formats ; un
changement de payload casserait le widget. Le view model gelé est la
frontière : des valeurs déjà formatées, des libellés explicites, et les
avertissements « non vérifié » portés avec la donnée plutôt que codés dans le
widget.

## Responsibility

- `CHANNELS` : descripteurs statiques des quatre canaux affichés, avec
  libellé explicite (« Accélération (g) », « Vitesse angulaire (°/s) »,
  « Champ magnétique (µT) », « Distance lidar (mm) »), étiquettes d'axes,
  indicateur et raison « valeur non vérifiée », note de dette.
- `InertialSensorReadingViewModel` : une lecture prête à afficher (une ligne
  de texte par canal, cadence mesurée, nombre d'échantillons).
- `build_reading_view_model(...)` : construit la lecture depuis des
  primitives (aucun type domain importé).

## Design

- Frozen dataclasses de chaînes et de tuples : rien à calculer côté widget.
- Valeurs non vérifiées signalées : gyroscope (plage 490 °/s reprise d'un VI),
  magnétomètre (diviseur 2^15 ou 2^16 non tranché), lidar (mm non vérifié).
- **Dette non silencieuse** : le lidar est un canal provisoire du même flux,
  son libellé le dit (« canal provisoire : concept distinct à venir »).
- Aucune calibration au repos : valeurs brutes converties uniquement.
