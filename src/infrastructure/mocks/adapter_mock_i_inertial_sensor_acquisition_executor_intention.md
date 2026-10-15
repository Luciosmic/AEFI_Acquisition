# adapter_mock_i_inertial_sensor_acquisition_executor — Intention

## Rationale

Tester `InertialSensorService` avec le vrai exécuteur introduit un thread et
des attentes ; un test applicatif qui vérifie « le service délègue le démarrage
avec les bons canaux » n'a pas besoin de cette mécanique.

## Responsibility

- Implémenter `IInertialSensorAcquisitionExecutor` sans thread : enregistre
  les configurations démarrées et les appels à `stop()`, expose un drapeau
  `is_running()`.

## Design

- Pas de publication d'événements ni de lecture du port : le comportement
  réel du worker est couvert par les tests de l'exécuteur d'`infrastructure/execution`.
