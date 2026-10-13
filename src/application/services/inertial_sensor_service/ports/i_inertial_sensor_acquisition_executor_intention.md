# i_inertial_sensor_acquisition_executor — Intention

## Rationale

`start_stream` bloque ~0,5 s et `read_sample` bloque jusqu'à la prochaine
ligne : si le service les appelait directement depuis le thread de
l'interface, le panneau se figerait à chaque démarrage. La mécanique
d'exécution (thread, boucle, tolérance aux échecs) est de l'infrastructure ;
le service applicatif reste un délégateur mince, testable sans thread réel.

## Responsibility

- Déclarer `start(config, stream_port)` (non bloquant pour l'appelant),
  `stop()` et `is_running()`.

## Design

- **Port outbound** dans `inertial_sensor_service/ports/`.
- Implémenté par `InertialSensorAcquisitionExecutor` dans
  `infrastructure/execution/`.
- La politique de tolérance aux échecs vit dans l'implémentation, pas dans le
  contrat.
- Même forme que `IElectricFieldProbeAcquisitionExecutor`, sans correction de
  fréquence (aucun équivalent pour ce capteur).
