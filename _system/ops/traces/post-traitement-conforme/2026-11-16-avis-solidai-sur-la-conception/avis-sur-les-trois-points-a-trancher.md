---
doc_type: avis-solidai
---

# Avis sur les trois points à trancher du § 5

Lecture seule de la conception, des récits et du plan, face aux standards du profil `solidai` et au code réel (module, adaptateur et tests de `src/`).
Chaque décision est ferme ; l'ordre des tranches de la conception reste, sauf mention.

## Point 1 — Où vivent les étapes calculées

**Décision : A, un fichier propre `<scan>_post-processing.h5` à côté de celui de l'acquisition. Elle arrive en tranche 6, pas en tranche 1.**

Raisons :
- L'acquisition calcule l'empreinte du `.h5` à la fermeture de l'export (`_close_export`), puis lance le post-traitement (`_handle_scan_finished`, `scan_export_service.py` lignes 504 à 517). Le post-traitement modifie donc un fichier déjà pris en empreinte. Le récit R4 (« fichier modifié depuis l'acquisition ») marquerait toute acquisition traitée comme modifiée tant que le point 1 reste en B.
- La règle de dépendance est celle de la conception (l'aval ne modifie pas l'amont) : A la tient, B la viole.
- Le critère de la tranche 1 est « mêmes fichiers produits ». Un test de `src/` fige l'état actuel : `scan_export_with_post_processing_integration_test.py` exige un seul `.h5` par dossier, avec les cinq étapes dedans. A ne peut donc pas entrer avant que l'adaptateur et ce test changent, c'est-à-dire en tranche 6.

Impact sur les tranches :
- Tranche 1 : le chemin du fichier d'étapes sort d'une seule fonction (`processing_store_path(acquisition)`, dans l'adaptateur d'écriture et dans l'adaptateur de lecture, via une constante partagée). Passer à A en tranche 6 est alors un changement à un seul endroit.
- Tranche 6 : elle touche l'adaptateur de `src/`, son test (`aefi_post_processor_port_test.py`) et le test d'intégration ci-dessus (un `.h5` d'acquisition inchangé plus un `_post-processing.h5`). Elle supprime aussi le raccord temporaire `processing/processing_pipeline.py` (voir `decoupage-de-la-tranche-1.md`). Elle se fait sur `feature/*` depuis `develop`, pas dans le worktree borné.
- Après A, une acquisition dont les étapes sont seulement dans l'ancien `.h5` s'affiche « à recalculer » ; on ne les efface jamais dans le fichier de l'acquisition.
- Récit R4 : il ne se code qu'après la tranche 6.

## Point 2 — Le traitement automatique au lancement

**Décision : B, le lancement montre l'état de chaque acquisition et ne calcule rien ; le traitement part du bouton du panneau Acquisitions. L'option `--force` reste, comme choix explicite d'un traitement au lancement. Cela se fait en fin de tranche 1 (sous-étape 1.8), pas au début.**

Raisons :
- Un lancement qui écrit des fichiers avant d'afficher la fenêtre contredit le critère du récit R1 (« ouvrir la fenêtre ne modifie aucun fichier »).
- Le traitement en fin de scan est inchangé : l'adaptateur de `src/` appelle le calcul, puis lance la fenêtre avec `--repo-path`, qui sautait déjà le traitement.

Impact sur les tranches :
- La tranche 1 construit d'abord les couches et les panneaux avec le comportement actuel (traitement au lancement), vérifié « mêmes résultats » par le test d'étalon (1.1). La sous-étape 1.8 bascule ensuite le défaut. On sépare ainsi un risque d'architecture d'un changement de comportement.
- Le panneau Acquisitions a son bouton « Traiter » dès 1.7 (récit R2 est en tranche 1).
- Le bouton du panneau « External Modules » de `src/` lance toujours `composition_root.py` sans argument : il ouvre désormais la liste des états, sans calcul. Rien à changer côté `src/`.

## Point 3 — Emprunter le code par import ou le recopier

**Décision : import, par un seul paquet `aefi_acquisition_upstream/`, comme la conception le recommande, avec quatre précisions.**

1. **Rien n'est emprunté avant d'être utilisé.** Tranche 1 : `WindowsCarrier`, `CarrierPresentationModel`, `ModernTaskbar`, `TaskbarPresenter`, `TaskbarPresentationModel`. `RotationConvention` entre en tranche 2, `BenchReferential` en tranche 3, `ScanVisualizationPanel` en tranche 4.
2. **Le panneau Carte garde son tracé actuel (`FigureFactory`) en tranche 1.** `ScanVisualizationPanel` est une API au fil de l'eau (`initialize_scan`, `update_data_point` point par point, canaux nommés `x_in_phase` alors que les étapes portent `voltage_x_in_phase`). Le brancher sur une étape déjà calculée est un travail d'adaptation qui n'est pas de la conformité de base. La Carte passe au panneau emprunté en tranche 4, avec les Profils.
3. **Le raccord à `src/` est centralisé et protégé.** Un import de l'amont se fait par `from interface...` (racine `src/`), alors que le module a ses propres dossiers `domain`, `application`, `infrastructure`, `interface`. Lancé comme script (`composition_root.py`), le dossier du module est en tête de `sys.path` et `import interface` prendrait le dossier du module au lieu de celui de `src/`. `aefi_acquisition_upstream/__init__.py` règle le chemin à un seul endroit (retrait du dossier du module de `sys.path`, ajout de `src/` en dernier) ; un test de lancement en sous-processus le prouve. Dans le module, tout import interne est qualifié (`aefi_post_processor_module.…`) ou relatif, jamais `from domain…`.
4. **Le sens des dépendances est vérifié par un test du module**, car `solidai verify` ne voit pas ce paquet (il est hors des quatre couches) : un test d'architecture lit les imports de `domain/` et `application/` et refuse `PySide6`, `aefi_acquisition_upstream`, `interface`/`src`. C'est la parade à l'import circulaire acquisition ↔ post-traitement (voir écart 4 dans `ecarts-de-la-conception-aux-standards-solidai.md`).

Impact sur les tranches : une dépendance d'exécution de plus pour la fenêtre (`PySide6-QtAds` de l'acquisition, déjà dans l'environnement `uv` de la racine) ; aucune pour l'adaptateur de `src/`, qui n'importe que le domaine et l'application du module.
