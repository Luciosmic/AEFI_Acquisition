# aefi_line_abandoned — Intention

## Rationale

Une `AefiLine` est atomique : complète ou inexistante. Quand une ligne en cours de balayage est interrompue (pause), ses données partielles sont jetées et la ligne sera refaite. Sans fait publié, l'abandon est invisible : l'opérateur voit la progression reculer sans explication et le journal du scan ne dit pas pourquoi une ligne est acquise deux fois.

## Responsibility

- Fait passé : la tentative d'acquisition d'une ligne a été abandonnée ; porte le scan, le rang de la ligne, la raison (p.ex. `"paused"`) et le nombre de points de grille jetés.
- Ce n'est PAS un fait de l'agrégat `AefiLine` (elle n'a jamais été créée) : aucun compteur ni écriture d'export de mesure ne dépend de lui.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`. Topic : `"aefilineabandoned"`.
- Publié par le service applicatif sur le bus, sans unité de travail.
