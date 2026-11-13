# fake_adc_oversampling_port — Intention

## Rationale

Le vrai adaptateur écrit le registre de l'ADS131A04 par le port série du MCU.
Sans ce fake, le balayage de l'OSR ne se testerait qu'avec le banc branché.

## Responsibility

- Registre OSR en mémoire (`get` / `set`), liste des OSR acceptés (datasheet,
  tableau 30), identifiant de configuration `ads131a04`.
- Mêmes modes d'échec que le réel : OSR refusé par la puce, écriture refusée
  par le MCU (`fail_on_set=True`).
- `history` : les OSR écrits, dans l'ordre (vérification d'état).

## Design

- `get_oversampling_ratio` sert de source d'OSR au `FakeDrdyCapturePort` :
  les fronts simulés suivent l'OSR écrit ici.
- Testé via les tests du service.
