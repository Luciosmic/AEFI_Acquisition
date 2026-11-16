---
type: atome::solidai-atome
tldr: "Retrancher à tout le champ le signal mesuré au point de référence, pour ne garder que la perturbation."
code: ["[[external_modules/aefi_post_processor_module/domain/processing/amplitude_subtractor/amplitude_subtractor.py]]"]
cause_de_changement: regle-metier
---
# amplitude_subtractor — Intention

## Rationale

Le champ primaire de la source domine la mesure. Sans le soustraire, la perturbation due à l'objet reste noyée dans un fond plusieurs fois plus grand, et deux scans ne se comparent pas.

## Responsibility

- Lire le vecteur au point de référence (indice hors grille refusé).
- Le soustraire à chaque pixel ; une référence NaN compte pour zéro.
- Rendre le champ soustrait et le vecteur retranché.

## Design

- Classe `PrimaryFieldAmplitudeSubtractor` ; `border_width` est conservé pour la compatibilité, sans effet.
- Un échec connu dans `_tests/amplitude_subtraction_test.py` (`test_offset_removal`), traité par la tranche 5 du plan.
