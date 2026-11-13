# column_settled — Intention

## Rationale

Après chaque déplacement, la mesure attend que la colonne soit au repos, ou à défaut le délai fixe.
Sans ce fait publié, on ne peut pas savoir, point par point, si la mesure est partie au repos, au délai fixe, ou au délai maximal avec une colonne qui vibrait encore.

## Responsibility

- Dire, pour chaque attente, le point mesuré ensuite (`point_index`), comment l'attente s'est terminée (`method`), quand le mouvement s'est arrêté, combien de temps elle a duré, et la vibration jugée contre son seuil.

## Design

- `@dataclass(frozen=True)`, publié par la boucle de scan sur le topic `columnsettled`.
- Les valeurs de `method` sont des constantes de ce module, reprises par l'application et l'export.
- Au scan au vol, l'attente se fait au début de chaque ligne : `point_index` est celui du premier point de la ligne.
