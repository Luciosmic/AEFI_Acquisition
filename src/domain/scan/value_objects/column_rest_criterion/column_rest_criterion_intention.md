---
type: value-object::solidai-ddd
tldr: "Dire quand la colonne est revenue au repos : la vibration sur la dernière fenêtre (window_s) ne dépasse pas factor fois le niveau de repos."
code: ["[[src/domain/scan/value_objects/column_rest_criterion/column_rest_criterion.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/scan/scan_intention]]"
---
# column_rest_criterion — Intention

## Rationale

Après un déplacement, la colonne vibre : une mesure lancée trop tôt lit un capteur qui bouge encore.
Un délai fixe est soit trop court (le Banc-test-II a montré qu'1 s ne suffisait pas), soit trop long pour tous les points calmes.
Sans critère nommé, le seuil, la fenêtre et le délai maximal finiraient en constantes éparses dans la boucle de scan.

## Responsibility

- Dire quand la colonne est revenue au repos : la vibration sur la dernière fenêtre (`window_s`) ne dépasse pas `factor` fois le niveau de repos.
- Mesurer la vibration d'une série d'accélérations : RMS de |a − ā|, en g, indépendant de l'orientation de la carte (retire la pesanteur et le décalage statique).
- Porter la durée de mesure du niveau de repos (`rest_measurement_s`) et le délai au-delà duquel la mesure part quand même (`timeout_s`).

## Design

- `@dataclass(frozen=True)` : immuable, défini par sa valeur.
- Valeurs par défaut reprises des campagnes du Banc-test-II (`campagnes/campaign.py`, constantes `SETTLE_*`) : repos mesuré 10 s, fenêtre 1 s, facteur 1,5, délai maximal 30 s.
- Aucune lecture de capteur ni horloge : l'application fournit les accélérations et décide quoi faire d'une absence de données.
