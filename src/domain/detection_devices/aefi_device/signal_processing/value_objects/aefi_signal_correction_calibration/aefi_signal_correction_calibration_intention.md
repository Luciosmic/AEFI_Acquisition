# aefi_signal_correction_calibration — Intention

## Rationale

Aujourd'hui l'état de calibration (offsets de bruit, angles de phase, offsets de champ primaire) vit dans `ProcessingState`, une dataclass mutable interne à `interface/presenters/signal_processor.py`. Elle n'est pas partageable entre deux consommateurs (le plot temporel et la future FFT) sans dupliquer la logique, et rien n'empêche une mutation partielle incohérente (ex. activer une correction sans jamais renseigner ses offsets). Pour que l'agrégat `AefiCorrectedSample` puisse valider un invariant sur un instantané de calibration, cet instantané doit être une valeur immuable passée explicitement, pas un état interne muté au fil des appels.

## Responsibility

- Porter l'état de calibration des trois étapes de correction (bruit, phase, champ primaire) : offset par axe (`x`/`y`/`z`), activation par étape.
- Servir d'entrée à `AefiSignalCorrectionService` et d'invariant vérifié par `AefiCorrectedSample.correct`.
- Remplacer `ProcessingState` (`interface/presenters/signal_processor.py`), qui disparaît à la fin de la migration.

## Design

- `@dataclass(frozen=True)` : immuable — toute mise à jour produit une nouvelle instance (`dataclasses.replace`), jamais une mutation en place.
- Clés d'axe `"x"`, `"y"`, `"z"` (vocabulaire domaine, aligné sur les champs `voltage_{axis}_in_phase/quadrature` de `AefiVoltageMeasurement`) — la traduction depuis les clés UI (`"Ux"`, `"Uy"`, `"Uz"`) reste un détail de la couche interface, hors de ce module.
- Valeurs par défaut : dictionnaires vides et corrections désactivées, équivalent à l'état initial de `ProcessingState()`.
