# electric_field_probe_connection_changed — Intention

## Rationale

La sonde Narda EP-601 est auto-off et se déconnecte/time-out fréquemment. La
connexion est déclenchée à la demande depuis l'UI, jamais au démarrage de
l'application. Un seul événement couvre les trois issues possibles (connecté,
déconnecté, échec de connexion) pour que le presenter n'ait qu'un seul
abonnement à piloter le voyant "sonde".

## Responsibility

- Signaler un changement d'état de connexion de la sonde : `connected=True`
  avec l'identité (`probe`), ou `connected=False` avec un message d'erreur
  optionnel (time-out, port absent, déconnexion demandée).

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- `probe: Optional[ElectricFieldProbe]` — présent seulement si `connected=True`.
- `error: Optional[str]` — présent seulement en cas d'échec.
- Topic de publication : `"electricfieldprobeconnectionchanged"`.
