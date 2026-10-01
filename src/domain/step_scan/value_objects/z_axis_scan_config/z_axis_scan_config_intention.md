# z_axis_scan_config — Intention

## Rationale

Sans ce module, un profil vertical du champ (décroissance avec la hauteur au-dessus des sphères) n'a aucune représentation domain : les hauteurs visitées vivent dans un tableur ou dans la tête de l'opérateur, ce qui signifie que la mesure ne peut pas être rattachée à une consigne validée ni rejouée, ce qui force à reconstruire a posteriori où chaque point a été pris.

## Responsibility

- Décrire un scan en Z à position XY fixe : `xy_position`, `z_min_mm`, `z_max_mm`, `n_points`.
- Valider : `xy_position` dans les limites X/Y, `0 <= z_min < z_max <= PHYSICAL_Z_MAX_MM`, `n_points >= 1`.

## Design

- `@dataclass(frozen=True)`, validation dans `__post_init__`.
- **Ne code pas** si le déplacement Z est manuel (opérateur) ou motorisé : c'est une préoccupation d'exécution (application/infra), pas une donnée domain.
- `PHYSICAL_Z_MAX_MM` est un placeholder non confirmé hardware (voir `physical_bench_limits`).
