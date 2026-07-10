# adapter_electric_field_probe_port — Intention

## Rationale

Seul point du code spécifique à la marque Narda dans la chaîne
`electric_field_probe` : enveloppe `driver_narda_ep601.NardaEP601` (protocole
série existant) derrière `IElectricFieldProbePort`, pour que l'application et
le domaine restent agnostiques au fabricant.

## Responsibility

- `connect()` : ouvre le port série puis interroge `get_serial_number()` pour
  construire l'identité `ElectricFieldProbe`. Toute exception (time-out,
  port absent) remonte telle quelle — c'est `ElectricFieldProbeService` qui
  l'absorbe et la transforme en événement.
- `acquire_sample()` : lit `get_field_components()` (X, Y, Z en V/m) et
  délègue à `probe.record_measurement()` pour produire un `FieldMeasurement`.
- `is_connected()`/`is_ready()` reflètent l'état réel de la connexion.

## Design

- Sonde tri-axiale fixe (`axis_labels=("X", "Y", "Z")`) — c'est un fait du
  modèle EP-601, pas une configuration.
- Pas de retry/reconnexion automatique ici : la sonde est auto-off et
  time-out par nature, la reconnexion est une action utilisateur explicite
  (bouton "Connect" du panel), pas une responsabilité de l'adaptateur.
