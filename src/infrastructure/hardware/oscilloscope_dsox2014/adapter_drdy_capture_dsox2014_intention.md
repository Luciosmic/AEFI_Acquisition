# adapter_drdy_capture_dsox2014 — Intention

## Rationale

L'ODR de l'ADC a été mesurée le 2026-10-02 par un script autonome
(`mesure_periode_drdy_oscilloscope.py`, rangé avec les données dans le vault
de thèse). Sans adaptateur, la mesure reste hors de l'application, exige de
fermer le logiciel, et le savoir-faire SCPI (sauvegarde/restauration de la
configuration, mode RAW, déclenchement) se perd avec le script. Le pilote
existant des ressources de thèse (`driver_oscilloscope_DSOX2014.py`) vit hors
du dépôt et lit en mode NORMal (~1000 points), insuffisant pour dater des
fronts.

## Responsibility

- Implémenter `IDrdyCapturePort` pour l'Agilent DSO-X 2014A en VISA :
  sauvegarder la configuration de l'instrument, capturer en acquisition
  unique la voie demandée sur la fenêtre demandée (déclenchement front
  descendant à mi-tension logique), lire la forme d'onde en points RAW,
  restaurer la configuration, fermer.
- Dater les fronts descendants (`falling_edges` : franchissements du seuil
  mi-hauteur, interpolés linéairement).
- Toute erreur (pyvisa absent, pas d'instrument, délai de déclenchement
  dépassé, erreur SCPI) → `OperationResult.fail` avec la raison.

## Design

- Même méthode SCPI que la mesure de référence du 2026-10-02 (1000,000 µs à
  OSR 4096) : le résultat intégré se compare à elle.
- Adresse VISA optionnelle : à défaut, premier instrument USB/TCPIP dont le
  `*IDN?` contient « DSO-X 2014A ».
- `pyvisa` importé à l'ouverture seulement : l'application démarre sans
  l'oscilloscope ni la bibliothèque VISA. ponytail: `pyvisa` vient de la
  dépendance `pylablib` (non déclaré en propre dans `pyproject.toml`) —
  le déclarer si `pylablib` disparaît.
- Tests : `falling_edges` sur signal synthétique ; la séquence SCPI contre un
  instrument simulé minimal. ponytail: la fidélité au vrai DSO-X n'est
  vérifiée que par la mesure de référence au banc.
