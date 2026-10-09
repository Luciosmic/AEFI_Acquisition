# spectral_analysis_service — Intention

## Rationale

L'objectif est d'observer le contenu basse fréquence (dérive, bruit, 50 Hz secteur) du signal AEFI corrigé déjà affiché dans le plot temporel, sans dupliquer le pipeline de correction : la FFT doit s'abonner au même signal corrigé que le plot (`AefiCorrectedFieldSampleAcquired`), pas au signal brut. Comme `AefiSignalProcessingService`, ce service applicatif ne porte aucune logique mathématique propre — le calcul (resampling + FFT) est délégué au domain service pur `SpectralAnalysisCalculator` ; ce service se limite à maintenir la fenêtre glissante et à republier le résultat.

## Responsibility

- S'abonner à `aeficorrectedfieldsampleacquired` et accumuler les échantillons dans un buffer borné par DURÉE (pas par nombre d'échantillons) : les plus anciens sont retirés dès que la fenêtre dépasse `window_duration_s`.
- Réinitialiser le buffer dès qu'un `acquisition_id` différent du courant est reçu — un spectre ne doit jamais mélanger deux acquisitions.
- Une fois la fenêtre pleine, appeler `SpectralAnalysisCalculator.compute(...)` et publier `SpectralAnalysisResultUpdated`. Recalcul à chaque nouvel échantillon, sans throttling (coût `rfft` négligeable à la cadence de l'acquisition continue AEFI, ~100-200 Hz).
- Exposer `set_window_duration(dto)` (vide le buffer — pas de fenêtre partielle mélangeant deux durées) et `get_window_duration()`.

## Design

- `window_duration_s` est un paramètre constructeur sans valeur par défaut imposée ici (décision utilisateur, le câblage dans `main.py`/l'UI fixe la valeur initiale — hors scope de cette tâche, qui ne couvre pas le câblage).
- **Détection de fenêtre pleine — écart volontaire par rapport au pseudo-code initial du plan** : rederiver "la fenêtre est pleine" depuis le span du buffer APRÈS troncature (`buffer[-1].t - buffer[0].t < window_duration_s: return`) latche en silence après la première troncature — un échantillonnage discret n'atterrit (quasi) jamais exactement sur la borne de la fenêtre, donc le span post-troncature est presque toujours strictement inférieur à `window_duration_s`, et `compute` ne serait plus jamais appelé après la première troncature. Vérifié empiriquement par le test de bout en bout (`aefi_signal_correction_to_spectral_analysis_integration_test.py`), qui échouait avec ce pseudo-code littéral. Remplacé par un verrou one-way `_window_filled`, dérivé de l'écart entre le tout premier timestamp vu pour l'acquisition courante et le timestamp courant (jamais tronqué) — une fois vrai, reste vrai jusqu'au reset (changement d'`acquisition_id` ou `set_window_duration`).
- Logger nommé `logging.getLogger(__name__)`.
- Pas de `ports/` : seul `IDomainEventBus` est injecté, aucune I/O propre à ce service.
