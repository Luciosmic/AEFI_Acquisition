# exclusive_control — Intention

## Rationale

Plusieurs use cases pilotent les mêmes ressources du banc : l'excitation, le
flux d'acquisition continue, les réglages avancés (n_avg du MCU, OSR de
l'ADC). Sans propriétaire unique, une action manuelle ou un autre use case
change la ressource au milieu d'une mesure — et la mesure continue, sans
erreur, sur des données fausses (constaté le 2026-10-02 : flux arrêté depuis
Continuous Reading au milieu d'une caractérisation du débit). La règle
« un seul pilote à la fois » existait pour l'excitation ; recopiée pour
chaque ressource, elle divergerait.

## Responsibility

- `take(controller)` : devenir l'unique pilote ; refusé (`OperationResult.fail`,
  message lisible) si un autre pilote la tient ; reprendre sa propre ressource
  ne fait rien.
- `release(controller)` : rendre la ressource ; ignoré si `controller` n'est
  pas le pilote ; idempotent.
- `refusal(caller, command)` : le message de refus si `caller` (None = action
  manuelle) n'est pas le pilote, sinon None — à appeler en tête de chaque
  commande qui modifie la ressource.
- Prévenir l'appelant de chaque changement de pilote (`on_changed`), pour
  qu'il publie l'événement de sa ressource.
- `take_all([(take, release), ...])` : prendre plusieurs ressources, tout ou
  rien — au premier refus, rendre ce qui a été pris. Rend les libérations à
  appeler (ordre inverse). Un use case qui pilote excitation + flux +
  réglages ne peut pas rester à moitié propriétaire.

## Design

- Vérification à l'exécution (équivalent de `RefCell::try_borrow_mut` en
  Rust) ; la lecture de la ressource reste libre.
- Verrou `threading.Lock` : les use cases prennent la ressource depuis leur
  tâche de fond. `on_changed` est appelé hors du verrou.
- Pas d'événement ici : chaque ressource garde son propre événement
  (`ExcitationControlChanged`, `AefiAcquisitionControlChanged`,
  `HardwareConfigurationControlChanged`) — un nom par concept.
- La libération est explicite : les use cases la placent dans un `finally`.
