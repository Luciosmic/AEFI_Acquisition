# lidar_stream_error — Intention

## Rationale

« Le panneau diffuse déjà le flux » et « la carte ne répond pas » appellent deux
gestes différents de l'opérateur (arrêter le panneau / vérifier la carte). Sans
erreurs déclarées par le port, le service devrait reconnaître des exceptions série.

## Responsibility

- `LidarStreamBusyError` : le flux a déjà un propriétaire (panneau du capteur).
- `LidarUnavailableError` : ouverture ou lecture du flux impossible.

## Design

- Exceptions nommées levées par l'adaptateur et par le Fake, traduites par le
  service en erreurs de cas d'usage. `LidarStreamBusyError` hérite de
  `LidarUnavailableError` : un appelant qui ne distingue pas reste correct.
