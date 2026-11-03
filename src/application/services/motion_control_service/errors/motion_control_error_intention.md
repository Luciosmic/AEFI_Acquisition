# motion_control_error — Intention

## Rationale

Sans union d'erreurs nommée, `MotionControlService` renvoie des chaînes : l'interface ne peut pas distinguer « le banc n'est pas calibré, saisissez le pas par tour » de « le contrôleur ne répond pas ». Le premier doit mener l'opérateur au panneau Calibration, le second au banc.

## Responsibility

- `MotionConversionUnavailable` : commande refusée côté service parce que la conversion mm/impulsion manque (moteur, grandeur manquante, où la saisir).
- `MotionCommandFailed` : le port ou le contrôleur a levé pendant l'exécution.
- `message` : texte opérateur, pour que le presenter ne dépende pas des variantes.

## Design

- Union scellée : classe de base + dataclasses figées, sur le modèle de `ScanExecutionError`.
- Traduction des erreurs port/infrastructure (`MotionConversionUnavailableError`, exceptions) faite dans `MotionControlService`, seul site de traduction.
