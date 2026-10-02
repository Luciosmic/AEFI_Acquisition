# Analyse — Configuration de scan centrée (carré/rectangle) : UI vs Domain

**Date:** 2026-07-29
**Origine:** discussion Claude Code sur le worktree `_dev` (branche `develop`), reportée ici car c'est `dev_scan` qui porte le développement scan.
**Objectif:** évaluer où placer la logique de construction d'une zone de scan carrée/rectangulaire définie par un point centre + côté (ou largeur/hauteur) + nombre de points, plutôt que par bornes min/max explicites.

---

## Demande initiale

> Les contrôles du scan puissent se faire aussi autour du centre. Option scan carré (côté + nb points) et scan rectangle (largeur/hauteur + nb points), toujours centré sur le point centre.

---

## État constaté (worktree `_dev`, branche `develop`, avant tout code de cette feature)

- **`ScanZone`** (`src/domain/step_scan/value_objects/scan_zone/scan_zone.py`) — dataclass frozen `x_min/x_max/y_min/y_max`, validée en `__post_init__` contre des constantes physiques hardcodées `PHYSICAL_X_MAX_MM/Y_MAX_MM = 1200.0`. Expose déjà `center()`, `area()`, `contains()`.
- **`StepScanConfig`** compose `ScanZone` + `x_nb_points`/`y_nb_points` + pattern/axis/timing.
- **Flux UI → domain** : `ScanControlPanel._on_start_clicked()` (`src/interface/widgets/panels/scan_control_panel.py:207`) émet un dict brut (`x_min/x_max/x_nb_points/...`) → `ScanApplicationService._to_domain_config()` (`scan_application_service.py:588`) construit `ScanZone(x_min=dto.x_min, ...)`. Aucun calcul géométrique côté UI aujourd'hui — le panel est un formulaire de bornes brutes.
- **Référentiel "centré" existant** (commit `5fe688e`, déjà mergé dans `dev_scan` — vérifié via `git log`) : **purement UI**, dans `MotionPanelCompact` (`_raw_to_display`/`_display_to_raw_x/y`, ligne ~325). Affecte uniquement labels/plage de spinbox du contrôle moteur ponctuel (jog/move-to) ; le service moteur reçoit toujours du raw. **Ne touche pas la config de scan.**
- **Incohérence à noter** : `MotionPanelCompact` calcule son centre depuis `self._max_x/2` où `_max_x` est réglé à **1270** via `set_axis_limits()`, alors que `ScanZone` valide contre **1200**. Deux sources de vérité différentes pour "où est le centre du banc" — à réconcilier avant que scan et déplacement manuel partagent une notion de centre cohérente.

## Lien avec le plan déjà acté dans `goals.md` (feature Scan 1D/Z)

Le plan "Scan 1D (ligne theta) & Scan Z" déjà documenté ici prévoit :
- L'extraction de `PHYSICAL_X_MAX_MM`/`PHYSICAL_Y_MAX_MM`/`PHYSICAL_Z_MAX_MM` vers `src/domain/shared_kernel/physical_bench_limits.py` (pas encore fait à ce jour — vérifié, le fichier n'existe pas encore dans `dev_scan`).
- Un pattern `center: Position2D` déjà choisi pour `LineScanConfig`/`ZAxisScanConfig`.

**La feature "scan carré/rectangle centré" est donc le même besoin (centre + extension) appliqué à `ScanZone`.** Elle devrait consommer la même extraction `physical_bench_limits.py` plutôt que de dupliquer une 3e fois la constante de centre du banc (déjà dupliquée UI/domain aujourd'hui — cf. incohérence 1200/1270 ci-dessus). Il y a donc un ordre logique : faire (ou coordonner avec) l'extraction `physical_bench_limits.py` avant/pendant l'ajout des factory methods carré/rectangle sur `ScanZone`.

## UI vs Domain — pros/cons

**Calcul min/max dans l'UI (côté/largeur/hauteur → bornes) :**
- ❌ Duplique `ScanZone.center()` et les constantes physiques du banc.
- ❌ Contourne l'invariant : le résultat n'est validé qu'après coup par `ScanZone.__post_init__`, donc pas de gain de robustesse.
- ❌ Viole le standard projet "Presenter Responsibility Boundary" (pas de calcul dérivé métier dans l'UI/presenter).
- ❌ Toute autre consommatrice (tests domain, simulation problème direct 4 sphères) devrait réimplémenter le calcul.

**Factory methods sur `ScanZone` (domain)** — ex. `ScanZone.centered_square(side)`, `ScanZone.centered_rect(width, height)`, dérivant `x_min/x_max/y_min/y_max` à partir des mêmes constantes physiques (idéalement `physical_bench_limits.py`) puis retombant sur le `__post_init__` existant :
- ✅ Source unique de vérité pour le centre du banc et les limites physiques.
- ✅ Réutilisable (tests, futur usage simulation).
- ✅ Conforme aux standards du repo (domain pur, VO avec invariants, UI qui ne fait que construire/transmettre un DTO).
- ✅ Cohérent avec le pattern `center: Position2D` déjà choisi pour `LineScanConfig`/`ZAxisScanConfig`.

## Recommandation

**Domain.** Ajouter les factory methods carré/rectangle centré sur `ScanZone` (ou équivalent), branchés sur `physical_bench_limits.py`. Côté UI, `ScanControlPanel` ajoute un mode de saisie (bornes explicites vs centré+côté vs centré+largeur/hauteur) et transmet ces valeurs via DTO ; `ScanApplicationService._to_domain_config` choisit le constructeur `ScanZone` approprié selon le mode — aucune géométrie côté presenter.

**Prérequis avant implémentation** : réconcilier la constante de centre du banc entre `MotionPanelCompact` (1270) et `ScanZone` (1200), idéalement en les faisant dépendre toutes deux de `physical_bench_limits.py` une fois ce module créé.

## Non fait

Aucun code n'a été écrit pour cette feature à ce stade — analyse de placement uniquement, en attente de validation utilisateur avant implémentation.
