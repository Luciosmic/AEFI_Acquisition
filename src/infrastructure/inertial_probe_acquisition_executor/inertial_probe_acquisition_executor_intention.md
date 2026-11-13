---
type: adaptateur::solidai-hexagonal
tldr: "Adaptateur `inertial_probe_acquisition_executor` : Implémenter `IInertialProbeAcquisitionExecutor`."
code: ["[[src/infrastructure/inertial_probe_acquisition_executor/inertial_probe_acquisition_executor.py]]"]
cause_de_changement: outil
implements: ["[[src/application/inertial_probe/inertial_probe_service/ports/i_inertial_probe_acquisition_executor_intention]]"]
---
# inertial_probe_acquisition_executor — Intention

## Rationale

`start_stream` bloque ~0,5 s sur la vraie carte et `read_sample` bloque
jusqu'à la prochaine ligne : dans le thread de l'interface, le panneau se
figerait. Et si la carte se tait ou la liaison tombe, rien d'autre ne
préviendrait l'opérateur que la dernière valeur affichée est périmée. Même
rôle que `ElectricFieldProbeAcquisitionExecutor` pour la sonde de champ.

## Responsibility

- Implémenter `IInertialProbeAcquisitionExecutor`.
- Faire tourner dans un thread daemon : `stream_port.start_stream(canaux)`
  (bloquant), puis la boucle `read_sample` bloquante, en publiant
  `InertialProbeSampleAcquired` pour chaque échantillon.
- Toujours terminer par `stream_port.stop_stream()` (`finally`) : la carte
  garde son flux actif tant qu'on ne le lui arrête pas.
- Tolérer jusqu'à `MAX_CONSECUTIVE_READ_ERRORS` (2) erreurs de lecture
  consécutives (exception du port) et `MAX_SILENCE_S` (3 s) sans échantillon
  avant de publier `InertialProbeStreamFailed`. Un arrêt demandé par
  l'opérateur ne publie pas d'échec.

## Design

- Thread + `threading.Event` pour l'arrêt, `join(timeout=2.0)` — même
  squelette que les autres exécuteurs.
- `READ_TIMEOUT_S` (0,25 s) : borne le temps entre deux tests du drapeau
  d'arrêt, donc la latence de `stop()`.
- Pas de `time.sleep` dans la boucle : c'est la lecture bloquante qui cadence
  (fake en mode temps réel, vraie carte à 25 Hz).
- Le lidar traverse l'exécuteur comme canal du même flux (dette `ponytail:`
  du port).
