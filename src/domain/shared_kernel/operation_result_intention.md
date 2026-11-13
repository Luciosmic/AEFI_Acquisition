---
type: noyau-partage::solidai-ddd
tldr: "Noyau partagé du domaine : le résultat d'opération, les événements transverses et les valeurs de mesure que plusieurs agrégats et couches utilisent."
code: ["[[src/domain/shared_kernel/operation_result.py]]"]
cause_de_changement: regle-metier
utilise_par: ["[[src/domain/test_bench_calibration/calibration_intention]]", "[[src/application/scan/scan_application_service/scan_application_service_intention]]"]
---
# operation_result — Intention

Cette intention déclare aussi le noyau partagé `domain/shared_kernel/` (Evans, DDD, ch. 14, « Shared Kernel ») : le sous-ensemble du modèle que plusieurs agrégats s'accordent à partager. Ses événements et objets-valeurs lui sont rattachés par `part_of`, et `utilise_par` nomme ceux qui l'importent.

## Rationale

Encapsuler le résultat d'une opération (succès/échec) sans lever d'exception vers la couche appelante. `OperationResult[T, E]` force les appelants (notamment la UI via `MotionControlService`) à traiter les deux cas de manière explicite.

## Responsibility

- Représenter soit un succès avec valeur `T` (`OperationResult.ok(value)`), soit un échec avec erreur `E` (`OperationResult.fail(error)`).
- Exposer `is_success`, `value`, `error` comme accesseurs typés.

## Design

- **Generic `[T, E]`** : réutilisable pour n'importe quel type de retour et d'erreur.
- Placé dans `domain/shared/` : utilitaire domain partagé entre services applicatifs et domain.
- Alternative aux exceptions pour les erreurs "attendues" (échec de mouvement, limite atteinte) vs les exceptions "inattendues" (bug).
