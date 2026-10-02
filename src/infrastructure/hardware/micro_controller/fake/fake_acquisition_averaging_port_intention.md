# fake_acquisition_averaging_port — Intention

## Rationale

Le vrai adaptateur écrit `n_avg` dans `.aefi_acquisition/configs/mcu_last_config.json`.
Un test applicatif qui l'utiliserait modifierait la configuration runtime du
banc. Sans ce fake, la caractérisation du débit ne serait testable qu'en
touchant le disque de la manip.

## Responsibility

- `n_avg` en mémoire (`get`/`set`), bornes 1-127, OSR fixe.
- Mêmes modes d'échec que le réel : hors bornes, configuration non
  inscriptible (`fail_on_set=True`).
- `history` : tous les `n_avg` appliqués, dans l'ordre (vérification d'état,
  pas d'interaction).

## Design

- Brancher `get_n_avg` comme `n_avg_reader` de `ADS131A04Adapter` : le
  `FakeMCUSerialCommunicator` reçoit alors `m<n>` avec le `n` appliqué ici et
  simule `T(n)` et le bruit en `1/√n`.
- Pas d'attribut de qualité de service à simuler : `set_n_avg` n'est pas
  une opération régulatrice (le délai vit dans le communicateur).
