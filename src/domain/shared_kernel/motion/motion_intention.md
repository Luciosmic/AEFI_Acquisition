# motion — Intention

## Rationale

Sans ce regroupement, les faits du mouvement des moteurs (déplacement terminé,
échoué, arrêté, position mise à jour, arrêt d'urgence, conversion mm/incréments
disponible ou manquante) vivent à plat dans `shared_kernel/events/`, à côté des
types vraiment transverses (`DomainEvent`, `IDomainEventBus`). Le shared kernel
global mélange alors un sujet métier précis et les primitives communes à tous
les contextes : on ne voit plus ce qui est partagé par nécessité et ce qui
attend simplement son propre contexte.

## Responsibility

- Porter les événements domain du mouvement des moteurs du banc (`events/`).

## Design

- **Sous-dossier transitoire**, sur le modèle de `shared_kernel/excitation/` :
  aucun agrégat ni invariant motion n'existe encore, donc pas de contexte à
  part entière.
- À reconsidérer quand la conversion mm/incréments deviendra un modèle : ce
  sera le premier invariant motion, et le dossier pourra alors devenir un
  contexte cohésif avec son agrégat.
- Les topics du bus restent le nom de classe des événements : le déplacement
  ne change aucun abonnement.
