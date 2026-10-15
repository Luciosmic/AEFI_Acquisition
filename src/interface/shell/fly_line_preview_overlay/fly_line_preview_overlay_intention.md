# fly_line_preview_overlay — intention

## Rationale

Sans ce module, les points provisoires d'une ligne de fly-scan (aperçu `scan_line_preview`) restent dessinés sur la carte quand la ligne n'est jamais confirmée — ligne abandonnée sur pause, scan annulé ou en échec. L'opérateur voit alors comme acquis des points qui n'existent ni dans le domaine ni dans l'export, ce qui contredit l'atomicité d'`AefiLine` (ligne complète ou inexistante) et l'amène à mal juger ce qui reste à refaire.

## Responsibility

Retenir, pour la carte AEFI, les positions dessinées depuis un aperçu non encore confirmé par un point définitif (`scan_progress`), et les effacer (valeurs NaN) quand la ligne n'est pas confirmée : `scan_line_abandoned`, `scan_cancelled`, `scan_failed`. Oublier une position dès que son point définitif arrive ; tout oublier au démarrage d'un scan.

## Design

- Pure plomberie d'interface : signaux du `ScanPresenter` → méthodes des panneaux (`update_data_point_from_position`). Aucun import de `domain/`.
- Effacer = réécrire la cellule à NaN par l'API existante du panneau, pas de nouvelle primitive de widget.
- La correspondance aperçu/définitif se fait par position exacte : les deux viennent du même point de grille côté service (ponytail, voir le code).
