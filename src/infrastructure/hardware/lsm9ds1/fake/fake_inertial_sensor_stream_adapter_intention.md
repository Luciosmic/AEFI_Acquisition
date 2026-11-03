# fake_inertial_sensor_stream_adapter — Intention

## Rationale

Sans double, tester le service, l'exécuteur et le panneau exigerait une carte
branchée sur un port COM, et le mode « tout mocké » de `main_mock.py` n'aurait
aucun capteur inertiel à afficher.

## Responsibility

- Implémenter `IInertialSensorStreamPort` en mémoire, déterministe : mêmes
  valeurs pour un même index d'échantillon (gravité 1 g sur Z).
- Cadence nominale de 25 Hz, plafonnée à 25 Hz dès que le lidar est actif
  (`LIDAR_CAP_HZ`, mesuré sur la vraie carte : le flux plafonne à 25 Hz avec le
  lidar, journal du 2026-10-12).
- `realtime=True` : une ligne toutes les `1/cadence` s (appli en mode mock) ;
  `realtime=False` : pas d'attente, horodatages synthétiques `k / cadence`
  (tests rapides).
- Modes de défaillance de la vraie carte, pour tester l'exécuteur :
  `simulate_connection_failure` (connect lève `TimeoutError`),
  `fail_after_samples` (la lecture lève `OSError`, comme une erreur
  `pyserial`), `stall_after_samples` (la lecture renvoie `None`, le flux s'est
  tu).

## Design

- Qualité de service : la cadence simulée est un attribut porteur de
  régulation (le plafond 25 Hz avec lidar) ; les `~0,5 s` de blocage de
  `start_stream` sur la vraie carte ne sont pas simulés (vitesse de la suite
  de tests), ce que l'appelant ne doit pas supposer.
- Le lidar est simulé comme canal du même flux (dette `ponytail:` du port).
