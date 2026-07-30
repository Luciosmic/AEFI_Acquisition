# electric_field_probe_frequency_correction_changed — Intention

## Rationale

La sonde Narda EP-601 applique une correction de calibration factory dépendante
de la fréquence d'excitation courante (`set_frequency_correction`, commande
série `#00k`). Ce recalage doit être visible en UI (voyant), y compris dans
les cas où il n'a PAS pu être appliqué (fréquence <10kHz, hors
`RF_SENSING_RANGE_HZ`, ou panne matérielle) — nommé "Changed" et non
"Applied" car il couvre ces trois issues.

## Responsibility

- Signaler le résultat d'une tentative de correction fréquence, quelle que
  soit l'issue : appliquée, hors-plage sonde, ou erreur matérielle.
- `applied_hz` est `None` sauf en cas de succès — jamais un facteur de gain
  inventé, seulement le point de calibration en Hz confirmé par la sonde
  (le protocole ne renvoie aucun gain numérique).

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- `requested_hz: float` — fréquence demandée (miroir de l'excitation courante).
- `applied_hz: Optional[float]` — fréquence effectivement confirmée par la
  sonde, `None` si hors-plage ou erreur.
- `in_range: bool` — `False` si `requested_hz` est sous
  `RF_SENSING_RANGE_HZ[0]` (10kHz) : limite physique permanente de la sonde,
  pas une panne.
- `error: Optional[str] = None` — message si une exception driver a été
  capturée (jamais propagée à l'appelant).
- Topic de publication : `"electricfieldprobefrequencycorrectionchanged"`.
