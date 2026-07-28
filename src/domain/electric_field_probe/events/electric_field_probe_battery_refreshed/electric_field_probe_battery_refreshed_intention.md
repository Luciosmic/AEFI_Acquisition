# electric_field_probe_battery_refreshed — Intention

## Rationale

Le niveau de batterie n'est lu qu'une fois, à la connexion (pas de polling —
la lecture partage la même liaison série que l'acquisition et pourrait la
perturber). Un rafraîchissement manuel (bouton UI) est donc une action
distincte de la connexion elle-même, et ne doit pas être confondue avec
`ElectricFieldProbeConnectionChanged` (qui signale un changement d'état de
connexion, pas une mise à jour de valeur).

## Responsibility

- Signaler qu'une lecture batterie à la demande a réussi et que l'identité
  `probe` (avec `battery_voltage_v`/`battery_percentage`/
  `battery_remaining_hours` à jour) doit être re-affichée.
- N'est publié que si la sonde est connectée et qu'aucune acquisition n'est
  en cours — cette règle est appliquée par `ElectricFieldProbeService.refresh_battery()`,
  pas par cet événement.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- `probe: ElectricFieldProbe` — toujours présent (l'événement n'est publié
  qu'en cas de succès).
- Topic de publication : `"electricfieldprobebatteryrefreshed"`.
