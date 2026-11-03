# physical_bench_limits — Intention

## Rationale

Sans ce module, chaque type de scan (grille `ScanZone`, ligne `LineScanConfig`, axe Z `ZAxisScanConfig`) recopie ses propres bornes physiques du banc, ce qui signifie qu'un changement de mécanique (nouvelle course d'axe) doit être répercuté à trois endroits sans que rien ne le garantisse, ce qui force tôt ou tard une désynchronisation silencieuse : un type de scan accepte une position que le banc ne peut pas atteindre.

## Responsibility

- Porter les courses maximales des axes X, Y, Z du banc, en mm, origine à 0.

## Design

- Constantes de module, pas de classe : aucune logique, trois lecteurs.
- `PHYSICAL_Z_MAX_MM = 300.0` est un placeholder non confirmé sur le hardware (TODO).
- Cible future : injection depuis une entité banc (`bench_config.json`) quand elle existera.
