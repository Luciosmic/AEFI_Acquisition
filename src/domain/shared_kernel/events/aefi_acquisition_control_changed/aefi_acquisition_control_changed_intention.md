# aefi_acquisition_control_changed — Intention

## Rationale

Le scan, la calibration automatique et la caractérisation du débit lisent le
flux d'acquisition continue ; le panneau Continuous Reading peut le
démarrer et l'arrêter. Le 2026-10-02, un Stop manuel au milieu d'une
caractérisation l'a bloquée 58 s sans explication. Le verrou empêche le
Stop ; cet événement rend visible qui tient le flux, sinon le bouton
désactivé est un état caché.

## Responsibility

- Signaler que le pilote du flux a changé : pris (`controller` = nom
  lisible) ou libéré (`None`).

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`, même forme que
  `ExcitationControlChanged`.
- Publié par `AefiAcquisitionService.take_control()` / `release_control()`,
  uniquement sur changement effectif. Topic : `"aefiacquisitioncontrolchanged"`.
- Testé via `aefi_acquisition_service` (pas de logique propre).
