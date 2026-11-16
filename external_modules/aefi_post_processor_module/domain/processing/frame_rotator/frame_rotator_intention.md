---
type: atome::solidai-atome
tldr: "Passer le champ du repère du capteur à celui des sources par la rotation de montage P = Rx·Ry·Rz."
code: ["[[external_modules/aefi_post_processor_module/domain/processing/frame_rotator/frame_rotator.py]]"]
cause_de_changement: regle-metier
---
# frame_rotator — Intention

## Rationale

Le capteur est monté tourné par rapport aux sources. Sans cette rotation, les composantes x, y, z de la carte ne correspondent pas aux axes du problème direct, et la comparaison avec la simulation est faussée par une erreur de repère.

## Responsibility

- Construire la rotation de montage à partir des trois angles en degrés (extrinsèque, Z puis Y puis X, scipy `XYZ`).
- L'appliquer à chaque vecteur du champ, parties en phase et en quadrature séparément, en laissant les NaN.
- Rendre le champ tourné et les angles et le quaternion utilisés.

## Design

- Classe `SensorToEFSourcesFrameRotator`, par quaternion pour la stabilité numérique.
- La convention des angles est celle de l'acquisition (`rotation_convention`) ; la tranche 2 du plan la reprend de l'amont.
