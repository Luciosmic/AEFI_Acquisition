# aefi_line — Intention

## Rationale

Aujourd'hui le fly-scan est un `StepScan` transitoire qui garde ses points et s'auto-complète : sans agrégat de ligne, aucun invariant ne dit qu'une ligne est entière, ce qui signifie qu'une ligne trouée (points non projetés) ressemble à une ligne complète, ce qui force à auditer chaque carte. Le fly-scan est exploratoire (pas de mesure précise) : la bonne granularité transactionnelle est la ligne (~81 transactions), pas le point de grille ni le scan entier.

## Responsibility

- Aggregate root d'une ligne de fly-scan : identité `AefiLineId`, référence au scan par `scan_id` (identité seule), `line_index`, nombre de points de grille attendus.
- `record_points(points)` : exige EXACTEMENT les indices `{0..n-1}`, sans doublon ni trou ; sinon `AefiLineIncompleteError` et aucun état modifié. Seconde tentative : `AefiLineAlreadyAcquiredError`. `expected_points >= 1`.
- Sur succès : empile `AefiLineAcquired` (points triés par rang).
- Expose `domain_events` (retourne puis vide, requis par `IUnitOfWork.register`).
- Distinction de vocabulaire : l'`AefiLine` est l'unité du **fly-scan** (balayage continu, points projetés). Le **line-scan** est un step-scan le long d'une droite, fondé sur des `AefiPoint`.

## Design

- Dataclass ; les points de grille sont des value objects `LineGridPoint` (projetés par `FlyScanLineProjector`), pas des agrégats, pas d'invariant « N échantillons ».
- Domaine pur : aucun import infrastructure/application, aucun logger.
