# driver_lsm9ds1_stream — Intention

## Rationale

La carte garde son flux actif port fermé : un driver qui n'envoie pas `S*` à
la connexion ni à l'arrêt laisse la carte émettre dans le vide, et le
processus suivant reçoit un flux qu'il n'a pas demandé. Isoler `pyserial`, la
séquence de démarrage et la lecture bloquante dans un seul module rend cette
règle de sécurité vérifiable sans matériel.

## Responsibility

- `connect()` : ouvre, envoie `S*` (un flux peut survivre à la fermeture
  précédente), vide le tampon. Aucune attente de reset (aucun reset observé à
  l'ouverture).
- `start_stream(sensors, rate_hz=None)` : `S*`, vidage, puis
  `A9*`/`G9*`/`M9*`/`L9*` espacées de 100 ms (séquence du VI LabVIEW).
  `rate_hz` (25, 50, 100) envoie `F<n>*` seulement s'il est demandé ; sinon la
  cadence persistante de la carte est conservée. **Bloque ~0,5 s** (quatre
  commandes espacées) : à appeler depuis un thread de travail, jamais depuis le
  thread Qt.
- `read_sample(timeout_s)` : lecture bloquante, horodatage à la réception,
  lignes hors régime (transitoire de 3 à 9 lignes au démarrage séquencé,
  lignes tronquées) comptées dans `dropped_lines` et ignorées.
- `stop_stream()` / `disconnect()` : toujours `S*` puis vidage ; `disconnect`
  est idempotent. 1 à 3 lignes tardives peuvent encore arriver après `S*` : le
  vidage les écarte.

## Design

- Port série et débit sont **requis** : ils viennent de la configuration
  (`config_templates/lsm9ds1_config.json`), pas de constantes du driver.
- `serial_factory`, `sleep` et `clock` injectables : tests sans matériel ni
  attente.
- La carte garde F après `S*` (1 cas observé) : la cadence obtenue peut venir
  d'une session précédente ; l'appelant la mesure.
- Pas de thread ni de callback : l'appelant boucle sur `read_sample`.
- Jamais de LF ni CRLF envoyé (« poison LF » : invalide la trame suivante).
