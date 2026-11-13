---
type: value-object::solidai-ddd
tldr: "Porter le résultat d'un ajustement des angles de montage : les angles (`SensorRotationAngles`) et les indicateurs de qualité — désalignement résiduel des réponses X et Y…"
code: ["[[src/domain/test_bench_calibration/value_objects/sensor_mounting_fit/sensor_mounting_fit.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/test_bench_calibration/calibration_intention]]"
---
# sensor_mounting_fit — Intention

## Rationale

Sans ce VO, le solveur ne rendrait que des angles : l'opérateur recevrait un
P sans pouvoir juger s'il est fiable. Un P ajusté sur du bruit (excitation
trop faible, capteur débranché) ressemble à n'importe quel autre triplet
d'angles — rien ne le distingue, et il serait enregistré comme une vraie
calibration.

## Responsibility

- Porter le résultat d'un ajustement des angles de montage : les angles
  (`SensorRotationAngles`) et les indicateurs de qualité —
  désalignement résiduel des réponses X et Y (°) et angle entre les deux
  réponses (°, idéalement 90).

## Design

- `@dataclass(frozen=True)`, aucune logique : testé via
  `sensor_mounting_solver_test.py`.
