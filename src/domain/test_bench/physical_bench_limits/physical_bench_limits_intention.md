# physical_bench_limits — Intention

## Rationale

Sans ce module, chaque type de scan (grille `ScanZone`, ligne `LineScanConfig`) recopie ses propres bornes physiques du banc, ce qui signifie qu'un changement de mécanique (nouvelle course d'axe) doit être répercuté à plusieurs endroits sans que rien ne le garantisse, ce qui force tôt ou tard une désynchronisation silencieuse : un type de scan accepte une position que le banc ne peut pas atteindre.

## Responsibility

- Porter les courses maximales des axes X et Y du banc, en mm, origine à 0 (bornes de validation des scans).
- Porter la course de chaque axe en incréments du contrôleur, de la butée de homing (incrément 0) à la butée + (X 58 233, Y 56 346, relevées sur le banc le 2026-11-12, « environ »). C'est un fait des rails : la course en mm de l'axe = ce compte × µm par incrément, et le milieu du banc = la moitié de ce compte. Corriger le facteur ne déplace donc pas le milieu physique.

## Design

- Les bornes en mm (1200) sont une valeur nominale de validation de scan, pas la course réelle : à 20,62 µm/incrément la course Y est ≈ 1162 mm. Les réconcilier avec la course en incréments est à faire avant de s'y fier près des bords.
- Constantes de module, pas de classe : aucune logique, plusieurs lecteurs.
- Pas de borne Z : son seul lecteur était le scan Z, supprimé le 2026-10-15 (placeholder `PHYSICAL_Z_MAX_MM = 300.0` jamais confirmé sur le hardware). La recréer avec la course réelle quand le scan Z sera développé.
- Cible future : injection depuis une entité banc (`bench_config.json`) quand elle existera.
