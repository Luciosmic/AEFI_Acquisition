# line_grid_point — Intention

## Rationale

Le fly-scan est exploratoire : ses points de grille sont projetés par `FlyScanLineProjector` depuis un balayage continu, sans N échantillons contrôlés. Si chaque point était un agrégat, on payerait une transaction et un invariant « N échantillons » qui n'ont pas de sens ici, ce qui force ~81 transactions par ligne pour rien. Un value object suffit : la ligne est l'unité atomique.

## Responsibility

- Un point de grille d'une ligne : rang dans la ligne (`index_in_line >= 0`), position, mesure projetée.

## Design

- `@dataclass(frozen=True)`, défini par sa valeur, sans identité.
- Distinct de `AefiPoint` (agrégat du step-scan, N échantillons moyennés).
