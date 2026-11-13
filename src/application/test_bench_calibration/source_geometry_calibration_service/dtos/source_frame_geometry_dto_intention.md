# source_frame_geometry_dto — Intention

## Rationale

Le panneau de calibration doit dessiner la géométrie reconstruite sans
importer le domain (standard presenter / mémoire « No domain import in UI »).
Sans ce DTO, soit le VO `SourceFrameGeometry` traverse la frontière
application → interface, soit le presenter recalcule les écarts (logique
métier dans l'UI).

## Responsibility

- Transporter vers l'interface les positions S1..S4 dans le repère source, les
  rayons, le carré ajusté, les écarts au carré (par sphère + RMS) et les
  résidus par distance.

## Design

- `@dataclass(frozen=True)`, uniquement des floats/tuples.
- Mêmes noms et mêmes ordres que `SourceFrameGeometry` (un seul langage) ; les
  propriétés dérivées du VO (`square_residuals_m`, `square_rms_residual_m`)
  sont matérialisées en champs.
