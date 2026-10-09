---
in_graph: false
vault_ref: "0_inbox/EVENT - 2026-10-08_modelisation-ddd-agregats-scan-aefi.md"
generated: 2026-10-08
---

# le scan est un artefact de tracage gdc qui denote le processus physique et non l occurrent lui meme

> Note de décision architecturale hors graphe. Référence côté vault : [EVENT — modélisation DDD agrégats scan AEFI](../../../../KV_THESE/0_inbox/EVENT - 2026-10-08_modelisation-ddd-agregats-scan-aefi.md)

## Clarification du modèle DDD — session 2026-10-08

### Les trois agrégats du domaine d'acquisition

**`Scan`** — agrégat fin (tracking artifact)
- Invariant : PENDING → COMPLETE n'est franchissable que si tous les points attendus sont présents
- Contient une liste d'`AcquisitionPointId` — références par identité, jamais par containment
- PENDING = état de construction valide (Evans : états intermédiaires légitimes sur un agrégat)
- Repository : `IScanRepository`

**`AcquisitionPoint`** — agrégat fort (step-scan)
- Invariant : exactement N samples valides, atomiquement
- Un point incomplet n'existe pas dans le domaine
- Repository : `IAcquisitionPointRepository`

**`ScanLine`** — agrégat fort (fly-scan)
- Invariant : une ligne est complète ou n'existe pas
- Équivalent sémantique à AcquisitionPoint pour l'acquisition continue 1D
- Repository : `IScanLineRepository`

### Règle UoW : un agrégat par transaction

```python
# 1. Acquisition d'un point → UoW AcquisitionPoint
with uow:
    point = uow.acquisition_points.get(point_id)
    point.record_samples(samples)   # publie PointAcquired
    uow.commit()

# 2. Handler PointAcquired → UoW Scan (transaction séparée)
with uow:
    scan = uow.scans.get(scan_id)
    scan.mark_point_acquired(point_id)
    uow.commit()                    # publie ScanCompleted si dernier point
```

Modifier `Scan` et `AcquisitionPoint` dans la même UoW = signal que les frontières sont mal tracées.

### Pont ontologique BFO/IAO

Le `Scan` n'est pas le processus physique d'acquisition — il est l'**artefact d'information qui le dénote** (Generically Dependent Continuant, IAO).

| BFO | AEFI physique | DDD |
|---|---|---|
| Independent continuant | Électrode, banc, sphères | Aggregate Root |
| Process (occurrent) | Le scan physique qui se déroule | Séquence de Domain Events |
| Process boundary | Début/fin du scan | `ScanStarted`, `ScanCompleted` (immuables) |
| Scalar measurement datum | Sample ADC | Value Object `Sample` |
| GDC / tracking artifact | L'enregistrement du scan | Agrégat `Scan` (fin) |
| GDC / information artifact | CSV résultats, DTO ScanResult | DTO, Value Object |

PENDING = "l'artefact ne dénote pas encore un processus complété"
COMPLETE = "l'artefact dénote un processus complété, tous ses points présents"

Les Domain Events sont immuables parce qu'ils sont des **process boundaries** (BFO) — frontières instantanées d'un occurrent localisé dans le temps.
